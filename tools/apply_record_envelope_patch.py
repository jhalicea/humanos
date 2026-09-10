from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / 'notebook.py'
TEST = ROOT / 'tests' / 'test_record_envelope_integrity.py'


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError('patch anchor missing: ' + label)
    if text.count(old) != 1:
        raise RuntimeError('patch anchor not unique: ' + label)
    return text.replace(old, new, 1)


text = NOTEBOOK.read_text(encoding='utf-8')

text = replace_once(text,
"DIGEST_PREFIX = 'hmac-sha256:'\n",
"DIGEST_PREFIX = 'hmac-sha256:'\nRECORD_INTEGRITY_PREFIX = 'hmac-sha256-record-v1:'\nRECORD_INTEGRITY_VERSION = 1\nRECORD_INTEGRITY_DOMAIN = b'HumanOS transcript record envelope v1\\x00'\n",
'constants')

text = replace_once(text,
"""            role TEXT NOT NULL, text TEXT NOT NULL,\n            sha256 TEXT NOT NULL, created TEXT NOT NULL, UNIQUE(tx,ordinal));""",
"""            role TEXT NOT NULL, text TEXT NOT NULL,\n            sha256 TEXT NOT NULL, created TEXT NOT NULL,\n            record_integrity TEXT, record_integrity_version INTEGER,\n            UNIQUE(tx,ordinal));""",
'create transcript schema')

text = replace_once(text,
"""        if 'scope' not in {row['name'] for row in self.db.execute('PRAGMA table_info(recovery)')}:\n            with self.db:\n                self.db.execute(\"ALTER TABLE recovery ADD COLUMN scope TEXT NOT NULL DEFAULT 'NOTEBOOK'\")\n\n        try:""",
"""        if 'scope' not in {row['name'] for row in self.db.execute('PRAGMA table_info(recovery)')}:\n            with self.db:\n                self.db.execute(\"ALTER TABLE recovery ADD COLUMN scope TEXT NOT NULL DEFAULT 'NOTEBOOK'\")\n        transcript_columns = {row['name'] for row in self.db.execute('PRAGMA table_info(transcript)')}\n        with self.db:\n            if 'record_integrity' not in transcript_columns:\n                self.db.execute('ALTER TABLE transcript ADD COLUMN record_integrity TEXT')\n            if 'record_integrity_version' not in transcript_columns:\n                self.db.execute('ALTER TABLE transcript ADD COLUMN record_integrity_version INTEGER')\n\n        try:""",
'legacy schema migration')

text = replace_once(text,
"""    def digest_matches(self, stored, text):\n        if not isinstance(stored, str):\n            return False\n        if stored.startswith(DIGEST_PREFIX):\n            return hmac.compare_digest(stored, self.content_digest(text))\n        # Backward compatibility only: old vault rows used naked SHA-256.\n        return hmac.compare_digest(stored, digest(text))\n\n    def close(self):""",
"""    def digest_matches(self, stored, text):\n        if not isinstance(stored, str):\n            return False\n        if stored.startswith(DIGEST_PREFIX):\n            return hmac.compare_digest(stored, self.content_digest(text))\n        # Backward compatibility only: old vault rows used naked SHA-256.\n        return hmac.compare_digest(stored, digest(text))\n\n    def record_integrity(self, tx, ordinal, role, content_digest, created):\n        envelope = {\n            'record_type': 'TRANSCRIPT',\n            'record_integrity_version': RECORD_INTEGRITY_VERSION,\n            'tx': tx,\n            'ordinal': ordinal,\n            'role': role,\n            'content_digest': content_digest,\n            'created': created,\n        }\n        mac = hmac.new(self.integrity_key, RECORD_INTEGRITY_DOMAIN + encode(envelope).encode('utf-8'),\n                       hashlib.sha256).hexdigest()\n        return RECORD_INTEGRITY_PREFIX + mac\n\n    def _insert_transcript(self, tx, ordinal, role, text):\n        stamp = now()\n        content_digest = self.content_digest(text)\n        record_integrity = self.record_integrity(tx, ordinal, role, content_digest, stamp)\n        self.db.execute('''INSERT INTO transcript(\n            tx,ordinal,role,text,sha256,created,record_integrity,record_integrity_version)\n            VALUES(?,?,?,?,?,?,?,?)''',\n            (tx, ordinal, role, text, content_digest, stamp, record_integrity, RECORD_INTEGRITY_VERSION))\n\n    def _verify_record_integrity(self, row):\n        stored = row['record_integrity']\n        version = row['record_integrity_version']\n        if stored is None and version is None:\n            return 'CONTENT_VERIFIED_METADATA_LEGACY'\n        if stored is None or version is None:\n            raise RuntimeError('Transcript record integrity is partial')\n        if version != RECORD_INTEGRITY_VERSION:\n            raise RuntimeError('Unsupported transcript record integrity version')\n        if not isinstance(stored, str) or not stored.startswith(RECORD_INTEGRITY_PREFIX):\n            raise RuntimeError('Transcript record integrity encoding is invalid')\n        expected = self.record_integrity(row['tx'], row['ordinal'], row['role'], row['sha256'], row['created'])\n        if not hmac.compare_digest(stored, expected):\n            raise RuntimeError('Transcript record integrity mismatch')\n        return 'ENVELOPE_VERIFIED'\n\n    def close(self):""",
'envelope methods')

text = replace_once(text,
"""                self.db.execute('INSERT INTO transcript(tx,ordinal,role,text,sha256,created) VALUES(?,?,?,?,?,?)',\n                                (tx, 0, 'HUMAN', user_input, self.content_digest(user_input), now()))""",
"""                self._insert_transcript(tx, 0, 'HUMAN', user_input)""",
'start transcript insert')

text = replace_once(text,
"""        with self.db:\n            self.db.execute('INSERT INTO transcript(tx,ordinal,role,text,sha256,created) VALUES(?,?,?,?,?,?)',\n                            (tx, ordinal, role, text, self.content_digest(text), now()))\n\n    def save_task""",
"""        with self.db:\n            self._insert_transcript(tx, ordinal, role, text)\n\n    def save_task""",
'append transcript insert')

text = replace_once(text,
"""                if not prior:\n                    self.db.execute('INSERT INTO transcript(tx,ordinal,role,text,sha256,created) VALUES(?,?,?,?,?,?)',\n                                    (tx, ordinal, 'ASSISTANT', message, self.content_digest(message), now()))""",
"""                if not prior:\n                    self._insert_transcript(tx, ordinal, 'ASSISTANT', message)""",
'failure transcript insert')

text = replace_once(text,
"""        for row in self.db.execute('SELECT text,sha256 FROM transcript'):\n            if not self.digest_matches(row['sha256'], row['text']):\n                raise RuntimeError('Transcript hash mismatch')""",
"""        for row in self.db.execute('SELECT * FROM transcript ORDER BY seq'):\n            if not self.digest_matches(row['sha256'], row['text']):\n                raise RuntimeError('Transcript hash mismatch')\n            self._verify_record_integrity(row)""",
'verify transcript envelope')

NOTEBOOK.write_text(text, encoding='utf-8')

TEST.write_text(r'''import sqlite3
import tempfile
import unittest
from pathlib import Path

from notebook import Notebook, RECORD_INTEGRITY_PREFIX, RECORD_INTEGRITY_VERSION, digest


class RecordEnvelopeIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self.tmp.name) / 'vault'

    def tearDown(self):
        self.tmp.cleanup()

    def populated(self):
        book = Notebook(self.vault)
        ident = book.bind('Jon', 'opening')
        book.start(ident['hcid'], 'tx-a', 'human text')
        book.append('tx-a', 1, 'ASSISTANT', 'assistant text')
        book.project()
        self.assertTrue(book.verify())
        return book

    def tamper(self, sql, args=()):
        book = self.populated()
        book.close()
        db_path = self.vault / 'runtime' / 'notebook.sqlite3'
        with sqlite3.connect(db_path) as db:
            db.execute('DROP TRIGGER transcript_no_update')
            db.execute(sql, args)
            db.commit()
        return Notebook(self.vault)

    def test_new_rows_are_envelope_verified(self):
        book = self.populated()
        try:
            rows = list(book.db.execute('SELECT * FROM transcript ORDER BY seq'))
            self.assertEqual(len(rows), 2)
            for row in rows:
                self.assertEqual(row['record_integrity_version'], RECORD_INTEGRITY_VERSION)
                self.assertTrue(row['record_integrity'].startswith(RECORD_INTEGRITY_PREFIX))
                self.assertEqual(book._verify_record_integrity(row), 'ENVELOPE_VERIFIED')
        finally:
            book.close()

    def test_legacy_row_remains_content_verifiable_without_backfill(self):
        book = Notebook(self.vault)
        try:
            ident = book.bind('Jon', 'opening')
            text = 'legacy exact text'
            with book.db:
                book.db.execute('INSERT INTO transactions VALUES(?,?,?,?,?)',
                                ('legacy', ident['hcid'], text, 'STARTED', 'legacy-time'))
                book.db.execute('''INSERT INTO transcript(tx,ordinal,role,text,sha256,created)
                                   VALUES(?,?,?,?,?,?)''',
                                ('legacy', 0, 'HUMAN', text, digest(text), 'legacy-time'))
            book.project()
            row = book.db.execute("SELECT * FROM transcript WHERE tx='legacy'").fetchone()
            self.assertIsNone(row['record_integrity'])
            self.assertIsNone(row['record_integrity_version'])
            self.assertEqual(book._verify_record_integrity(row), 'CONTENT_VERIFIED_METADATA_LEGACY')
            self.assertTrue(book.verify())
        finally:
            book.close()

    def test_role_tampering_is_detected(self):
        book = self.tamper("UPDATE transcript SET role='HUMAN' WHERE tx='tx-a' AND ordinal=1")
        try:
            with self.assertRaisesRegex(RuntimeError, 'record integrity mismatch'):
                book.verify()
        finally:
            book.close()

    def test_ordinal_tampering_is_detected(self):
        book = self.tamper("UPDATE transcript SET ordinal=9 WHERE tx='tx-a' AND ordinal=1")
        try:
            with self.assertRaisesRegex(RuntimeError, 'record integrity mismatch'):
                book.verify()
        finally:
            book.close()

    def test_transaction_reassignment_is_detected(self):
        book = self.populated()
        ident = book.get_identity(book.get_transaction('tx-a')['hcid'])
        with book.db:
            book.db.execute('INSERT INTO transactions VALUES(?,?,?,?,?)',
                            ('tx-b', ident['hcid'], 'other', 'STARTED', 'other-time'))
        book.close()
        db_path = self.vault / 'runtime' / 'notebook.sqlite3'
        with sqlite3.connect(db_path) as db:
            db.execute('DROP TRIGGER transcript_no_update')
            db.execute("UPDATE transcript SET tx='tx-b' WHERE tx='tx-a' AND ordinal=1")
            db.commit()
        reopened = Notebook(self.vault)
        try:
            with self.assertRaisesRegex(RuntimeError, 'record integrity mismatch'):
                reopened.verify()
        finally:
            reopened.close()

    def test_timestamp_tampering_is_detected(self):
        book = self.tamper("UPDATE transcript SET created='2099-01-01T00:00:00+00:00' WHERE tx='tx-a' AND ordinal=1")
        try:
            with self.assertRaisesRegex(RuntimeError, 'record integrity mismatch'):
                book.verify()
        finally:
            book.close()

    def test_content_digest_substitution_is_detected(self):
        book = self.tamper("UPDATE transcript SET sha256='hmac-sha256:0000' WHERE tx='tx-a' AND ordinal=1")
        try:
            with self.assertRaisesRegex(RuntimeError, 'Transcript hash mismatch'):
                book.verify()
        finally:
            book.close()

    def test_partial_envelope_fails_closed(self):
        book = self.populated()
        book.close()
        db_path = self.vault / 'runtime' / 'notebook.sqlite3'
        with sqlite3.connect(db_path) as db:
            db.execute('DROP TRIGGER transcript_no_update')
            db.execute("UPDATE transcript SET record_integrity=NULL WHERE tx='tx-a' AND ordinal=1")
            db.commit()
        reopened = Notebook(self.vault)
        try:
            with self.assertRaisesRegex(RuntimeError, 'record integrity is partial'):
                reopened.verify()
        finally:
            reopened.close()

    def test_unknown_envelope_version_fails_closed(self):
        book = self.tamper("UPDATE transcript SET record_integrity_version=999 WHERE tx='tx-a' AND ordinal=1")
        try:
            with self.assertRaisesRegex(RuntimeError, 'Unsupported transcript record integrity version'):
                book.verify()
        finally:
            book.close()

    def test_unicode_roundtrip_keeps_exact_content_and_envelope(self):
        text = 'Cafe\u0301 / Café / 👩🏽‍💻 / \u200fمرحبا'
        book = Notebook(self.vault)
        try:
            ident = book.bind('Jon', 'opening')
            book.start(ident['hcid'], 'unicode', text)
            book.project()
            row = book.db.execute("SELECT * FROM transcript WHERE tx='unicode'").fetchone()
            self.assertEqual(row['text'], text)
            self.assertEqual(book._verify_record_integrity(row), 'ENVELOPE_VERIFIED')
            self.assertTrue(book.verify())
        finally:
            book.close()


if __name__ == '__main__':
    unittest.main()
''', encoding='utf-8')

print('record envelope patch applied')
