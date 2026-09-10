from pathlib import Path

NOTEBOOK = Path('notebook.py')
text = NOTEBOOK.read_text(encoding='utf-8')

old = "from integrity_lifecycle import bind_integrity_key, load_or_create_integrity_key\n"
new = "from integrity_lifecycle import bind_integrity_key, key_id, load_or_create_integrity_key\nfrom record_integrity import (RECORD_INTEGRITY_VERSION, policy_proof, record_proof,\n                              verify_policy_proof, verify_record_proof)\n"
assert old in text
text = text.replace(old, new, 1)

old = """          CREATE TABLE IF NOT EXISTS transcript(\n            seq INTEGER PRIMARY KEY AUTOINCREMENT, tx TEXT NOT NULL REFERENCES transactions(tx),\n            ordinal INTEGER NOT NULL, role TEXT NOT NULL, text TEXT NOT NULL,\n            sha256 TEXT NOT NULL, created TEXT NOT NULL, UNIQUE(tx,ordinal));\n          CREATE TABLE IF NOT EXISTS tasks(\n"""
new = """          CREATE TABLE IF NOT EXISTS transcript(\n            seq INTEGER PRIMARY KEY AUTOINCREMENT, tx TEXT NOT NULL REFERENCES transactions(tx),\n            ordinal INTEGER NOT NULL, role TEXT NOT NULL, text TEXT NOT NULL,\n            sha256 TEXT NOT NULL, created TEXT NOT NULL, UNIQUE(tx,ordinal));\n          CREATE TABLE IF NOT EXISTS transcript_integrity(\n            seq INTEGER PRIMARY KEY REFERENCES transcript(seq),\n            version INTEGER NOT NULL, proof TEXT NOT NULL);\n          CREATE TABLE IF NOT EXISTS tasks(\n"""
assert old in text
text = text.replace(old, new, 1)

old = """          CREATE TRIGGER IF NOT EXISTS transcript_no_delete BEFORE DELETE ON transcript\n            BEGIN SELECT RAISE(ABORT, 'append-only transcript'); END;\n          CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events\n"""
new = """          CREATE TRIGGER IF NOT EXISTS transcript_no_delete BEFORE DELETE ON transcript\n            BEGIN SELECT RAISE(ABORT, 'append-only transcript'); END;\n          CREATE TRIGGER IF NOT EXISTS transcript_integrity_no_update BEFORE UPDATE ON transcript_integrity\n            BEGIN SELECT RAISE(ABORT, 'append-only transcript integrity'); END;\n          CREATE TRIGGER IF NOT EXISTS transcript_integrity_no_delete BEFORE DELETE ON transcript_integrity\n            BEGIN SELECT RAISE(ABORT, 'append-only transcript integrity'); END;\n          CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events\n"""
assert old in text
text = text.replace(old, new, 1)

old = """        try:\n            # Reject a replaced key before recover() or any later code can append evidence.\n            bind_integrity_key(self.db, self.integrity_key)\n        except BaseException:\n"""
new = """        try:\n            # Reject a replaced key before recover() or any later code can append evidence.\n            self.integrity_key_id = bind_integrity_key(self.db, self.integrity_key)\n            self._ensure_transcript_integrity_policy()\n        except BaseException:\n"""
assert old in text
text = text.replace(old, new, 1)

anchor = """    def close(self):\n        self.db.close()\n        self.lock.close()\n\n"""
addition = """    def _ensure_transcript_integrity_policy(self):\n        keys = ('transcript_envelope_version', 'transcript_envelope_cutover_seq',\n                'transcript_envelope_policy_proof')\n        rows = dict(self.db.execute(\n            \"SELECT key,value FROM runtime_meta WHERE key IN (?,?,?)\", keys))\n        present = [name in rows for name in keys]\n        sidecars = self.db.execute('SELECT COUNT(*) FROM transcript_integrity').fetchone()[0]\n        if not any(present):\n            if sidecars:\n                raise RuntimeError('Transcript integrity policy is missing while envelope proofs exist')\n            cutover = self.db.execute('SELECT COALESCE(MAX(seq),0)+1 FROM transcript').fetchone()[0]\n            version = RECORD_INTEGRITY_VERSION\n            proof = policy_proof(self.integrity_key, version, cutover, self.integrity_key_id)\n            with self.db:\n                self.db.execute('INSERT INTO runtime_meta(key,value) VALUES(?,?)',\n                                (keys[0], str(version)))\n                self.db.execute('INSERT INTO runtime_meta(key,value) VALUES(?,?)',\n                                (keys[1], str(cutover)))\n                self.db.execute('INSERT INTO runtime_meta(key,value) VALUES(?,?)',\n                                (keys[2], proof))\n            self.transcript_integrity_version = version\n            self.transcript_integrity_cutover = cutover\n            return\n        if not all(present):\n            raise RuntimeError('Transcript integrity policy is incomplete')\n        try:\n            version = int(rows[keys[0]])\n            cutover = int(rows[keys[1]])\n        except (TypeError, ValueError):\n            raise RuntimeError('Transcript integrity policy metadata is invalid')\n        if version != RECORD_INTEGRITY_VERSION or cutover < 1:\n            raise RuntimeError('Unsupported transcript integrity policy')\n        if not verify_policy_proof(self.integrity_key, rows[keys[2]], version, cutover,\n                                   self.integrity_key_id):\n            raise RuntimeError('Transcript integrity policy verification failed')\n        if self.db.execute('SELECT 1 FROM transcript_integrity WHERE seq<? LIMIT 1',\n                           (cutover,)).fetchone():\n            raise RuntimeError('Legacy transcript rows were unexpectedly backfilled with envelope proofs')\n        self.transcript_integrity_version = version\n        self.transcript_integrity_cutover = cutover\n\n    def _insert_transcript(self, tx, ordinal, role, text):\n        \"\"\"Insert exact transcript evidence and its metadata envelope in one DB transaction.\"\"\"\n        created = now()\n        content_digest = self.content_digest(text)\n        cursor = self.db.execute(\n            'INSERT INTO transcript(tx,ordinal,role,text,sha256,created) VALUES(?,?,?,?,?,?)',\n            (tx, ordinal, role, text, content_digest, created))\n        seq = cursor.lastrowid\n        transaction = self.db.execute('SELECT hcid FROM transactions WHERE tx=?', (tx,)).fetchone()\n        if not transaction:\n            raise RuntimeError('Transcript envelope requires an existing transaction identity')\n        proof = record_proof(self.integrity_key, seq=seq, tx=tx, hcid=transaction['hcid'],\n                             ordinal=ordinal, role=role, content_digest=content_digest,\n                             created=created, key_id=self.integrity_key_id)\n        self.db.execute('INSERT INTO transcript_integrity(seq,version,proof) VALUES(?,?,?)',\n                        (seq, RECORD_INTEGRITY_VERSION, proof))\n        return seq\n\n    def transcript_integrity_status(self, seq):\n        row = self.db.execute(\n            '''SELECT s.seq,s.tx,t.hcid,s.ordinal,s.role,s.sha256,s.created,\n                      i.version,i.proof\n               FROM transcript s LEFT JOIN transactions t ON t.tx=s.tx\n               LEFT JOIN transcript_integrity i ON i.seq=s.seq WHERE s.seq=?''', (seq,)).fetchone()\n        if not row:\n            raise ValueError('Unknown transcript sequence')\n        if row['seq'] < self.transcript_integrity_cutover:\n            if row['proof'] is not None or row['version'] is not None:\n                return 'ENVELOPE_UNEXPECTED_LEGACY_PROOF'\n            return 'CONTENT_VERIFIED_METADATA_LEGACY'\n        if row['proof'] is None and row['version'] is None:\n            return 'ENVELOPE_MISSING'\n        if row['proof'] is None or row['version'] is None:\n            return 'ENVELOPE_PARTIAL'\n        if row['version'] != RECORD_INTEGRITY_VERSION or row['hcid'] is None:\n            return 'ENVELOPE_INVALID'\n        if not verify_record_proof(\n                self.integrity_key, row['proof'], seq=row['seq'], tx=row['tx'], hcid=row['hcid'],\n                ordinal=row['ordinal'], role=row['role'], content_digest=row['sha256'],\n                created=row['created'], key_id=self.integrity_key_id):\n            return 'ENVELOPE_INVALID'\n        return 'ENVELOPE_VERIFIED'\n\n    def close(self):\n        self.db.close()\n        self.lock.close()\n\n"""
assert anchor in text
text = text.replace(anchor, addition, 1)

old = """                self.db.execute('INSERT INTO transcript(tx,ordinal,role,text,sha256,created) VALUES(?,?,?,?,?,?)',\n                                (tx, 0, 'HUMAN', user_input, self.content_digest(user_input), now()))\n"""
new = """                self._insert_transcript(tx, 0, 'HUMAN', user_input)\n"""
assert old in text
text = text.replace(old, new, 1)

old = """            self.db.execute('INSERT INTO transcript(tx,ordinal,role,text,sha256,created) VALUES(?,?,?,?,?,?)',\n                            (tx, ordinal, role, text, self.content_digest(text), now()))\n"""
new = """            self._insert_transcript(tx, ordinal, role, text)\n"""
assert old in text
text = text.replace(old, new, 1)

old = """                    self.db.execute('INSERT INTO transcript(tx,ordinal,role,text,sha256,created) VALUES(?,?,?,?,?,?)',\n                                    (tx, ordinal, 'ASSISTANT', message, self.content_digest(message), now()))\n"""
new = """                    self._insert_transcript(tx, ordinal, 'ASSISTANT', message)\n"""
assert old in text
text = text.replace(old, new, 1)

old = """        for row in self.db.execute('SELECT text,sha256 FROM transcript'):\n            if not self.digest_matches(row['sha256'], row['text']):\n                raise RuntimeError('Transcript hash mismatch')\n"""
new = """        for row in self.db.execute('SELECT seq,text,sha256 FROM transcript ORDER BY seq'):\n            if not self.digest_matches(row['sha256'], row['text']):\n                raise RuntimeError('Transcript hash mismatch')\n            status = self.transcript_integrity_status(row['seq'])\n            if row['seq'] < self.transcript_integrity_cutover:\n                if status != 'CONTENT_VERIFIED_METADATA_LEGACY':\n                    raise RuntimeError('Legacy transcript envelope state is invalid: ' + status)\n            elif status != 'ENVELOPE_VERIFIED':\n                raise RuntimeError('Transcript envelope integrity failure: ' + status)\n        orphan = self.db.execute(\n            'SELECT i.seq FROM transcript_integrity i LEFT JOIN transcript s ON s.seq=i.seq '\n            'WHERE s.seq IS NULL LIMIT 1').fetchone()\n        if orphan:\n            raise RuntimeError('Orphan transcript envelope proof detected')\n"""
assert old in text
text = text.replace(old, new, 1)

NOTEBOOK.write_text(text, encoding='utf-8')

Path('record_integrity.py').write_text(r'''"""Versioned keyed metadata envelopes for immutable Life Notebook transcript rows."""
import hashlib
import hmac
import struct

RECORD_INTEGRITY_VERSION = 1
PROOF_PREFIX = 'record-hmac-sha256:v1:'
POLICY_PREFIX = 'record-policy-hmac-sha256:v1:'
_KEY_LABEL = b'HumanOS transcript envelope key v1'
_RECORD_DOMAIN = b'humanos/transcript-envelope/v1\x00'
_POLICY_DOMAIN = b'humanos/transcript-envelope-policy/v1\x00'


def _derived_key(vault_key):
    if not isinstance(vault_key, (bytes, bytearray)) or len(vault_key) < 16:
        raise ValueError('Invalid vault integrity key')
    return hmac.new(bytes(vault_key), _KEY_LABEL, hashlib.sha256).digest()


def _u64(value):
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 0xffffffffffffffff:
        raise ValueError('Envelope integer outside unsigned 64-bit range')
    return struct.pack('>Q', value)


def _lp(value):
    if isinstance(value, str):
        value = value.encode('utf-8')
    if not isinstance(value, (bytes, bytearray)):
        raise TypeError('Envelope field must be bytes or text')
    value = bytes(value)
    if len(value) > 0xffffffff:
        raise ValueError('Envelope field exceeds 32-bit length')
    return struct.pack('>I', len(value)) + value


def _field(name, value):
    return _lp(name) + _lp(value)


def canonical_record(*, seq, tx, hcid, ordinal, role, content_digest, created, key_id):
    """Serialize exactly stored logical values; no Unicode or timestamp normalization."""
    return b''.join((
        _RECORD_DOMAIN,
        _field('version', _u64(RECORD_INTEGRITY_VERSION)),
        _field('record_type', 'TRANSCRIPT'),
        _field('seq', _u64(seq)),
        _field('tx', tx),
        _field('hcid', hcid),
        _field('ordinal', _u64(ordinal)),
        _field('role', role),
        _field('content_digest', content_digest),
        _field('created', created),
        _field('key_id', key_id),
    ))


def record_proof(vault_key, **fields):
    mac = hmac.new(_derived_key(vault_key), canonical_record(**fields), hashlib.sha256).hexdigest()
    return PROOF_PREFIX + mac


def verify_record_proof(vault_key, stored, **fields):
    return isinstance(stored, str) and stored.startswith(PROOF_PREFIX) and hmac.compare_digest(
        stored, record_proof(vault_key, **fields))


def canonical_policy(version, cutover_seq, key_id):
    return b''.join((
        _POLICY_DOMAIN,
        _field('version', _u64(version)),
        _field('cutover_seq', _u64(cutover_seq)),
        _field('key_id', key_id),
    ))


def policy_proof(vault_key, version, cutover_seq, key_id):
    mac = hmac.new(_derived_key(vault_key), canonical_policy(version, cutover_seq, key_id),
                   hashlib.sha256).hexdigest()
    return POLICY_PREFIX + mac


def verify_policy_proof(vault_key, stored, version, cutover_seq, key_id):
    return isinstance(stored, str) and stored.startswith(POLICY_PREFIX) and hmac.compare_digest(
        stored, policy_proof(vault_key, version, cutover_seq, key_id))
''', encoding='utf-8')

Path('tests/test_record_integrity.py').write_text(r'''import sqlite3
from pathlib import Path
import tempfile
import unittest

from notebook import Notebook
from record_integrity import canonical_record


class RecordEnvelopeIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self.tmp.name) / 'vault'

    def tearDown(self):
        self.tmp.cleanup()

    def populated(self):
        book = Notebook(self.vault)
        ident = book.bind('Jon', 'record envelope test')
        book.start(ident['hcid'], 'tx', 'exact human text')
        book.append('tx', 1, 'ASSISTANT', 'exact assistant text')
        book.project()
        self.assertTrue(book.verify())
        self.assertEqual(book.transcript_integrity_status(1), 'ENVELOPE_VERIFIED')
        self.assertEqual(book.transcript_integrity_status(2), 'ENVELOPE_VERIFIED')
        book.close()
        return ident

    def raw(self):
        return sqlite3.connect(str(self.vault / 'runtime' / 'notebook.sqlite3'))

    def tamper_transcript(self, sql, params=()):
        with self.raw() as db:
            db.execute('DROP TRIGGER transcript_no_update')
            db.execute(sql, params)

    def assert_verify_fails(self, pattern='Transcript envelope integrity failure'):
        book = Notebook(self.vault)
        try:
            with self.assertRaisesRegex(RuntimeError, pattern):
                book.verify()
        finally:
            book.close()

    def test_new_rows_receive_atomic_envelope_proofs(self):
        self.populated()
        with self.raw() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM transcript').fetchone()[0], 2)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM transcript_integrity').fetchone()[0], 2)

    def test_role_tamper_is_detected(self):
        self.populated()
        self.tamper_transcript("UPDATE transcript SET role='HUMAN' WHERE seq=2")
        self.assert_verify_fails()

    def test_ordinal_tamper_is_detected(self):
        self.populated()
        self.tamper_transcript('UPDATE transcript SET ordinal=9 WHERE seq=2')
        self.assert_verify_fails()

    def test_transaction_tamper_is_detected(self):
        self.populated()
        self.tamper_transcript("UPDATE transcript SET tx='moved' WHERE seq=2")
        self.assert_verify_fails()

    def test_created_tamper_is_detected(self):
        self.populated()
        self.tamper_transcript("UPDATE transcript SET created='2000-01-01T00:00:00+00:00' WHERE seq=2")
        self.assert_verify_fails()

    def test_sequence_tamper_is_detected(self):
        self.populated()
        self.tamper_transcript('UPDATE transcript SET seq=99 WHERE seq=2')
        self.assert_verify_fails()

    def test_parent_identity_tamper_is_detected(self):
        self.populated()
        with self.raw() as db:
            db.execute("UPDATE transactions SET hcid='different-hcid' WHERE tx='tx'")
        self.assert_verify_fails()

    def test_content_substitution_still_fails_existing_content_digest(self):
        self.populated()
        self.tamper_transcript("UPDATE transcript SET text='changed' WHERE seq=2")
        self.assert_verify_fails('Transcript hash mismatch')

    def test_proof_deletion_cannot_downgrade_protected_row_to_legacy(self):
        self.populated()
        with self.raw() as db:
            db.execute('DROP TRIGGER transcript_integrity_no_delete')
            db.execute('DELETE FROM transcript_integrity WHERE seq=2')
        self.assert_verify_fails('ENVELOPE_MISSING')

    def test_policy_cutover_tamper_fails_before_verification(self):
        self.populated()
        with self.raw() as db:
            db.execute("UPDATE runtime_meta SET value='999' WHERE key='transcript_envelope_cutover_seq'")
        with self.assertRaisesRegex(RuntimeError, 'policy verification failed'):
            Notebook(self.vault)

    def test_canonical_encoding_is_deterministic_and_unicode_exact(self):
        fields = dict(seq=7, tx='tx', hcid='HCID-x', ordinal=1, role='ASSISTANT',
                      content_digest='hmac-sha256:abc', created='2026-09-10T00:00:00+00:00',
                      key_id='key-hmac-sha256:def')
        first = canonical_record(**fields)
        self.assertEqual(first, canonical_record(**fields))
        nfc = dict(fields, tx='caf\u00e9')
        nfd = dict(fields, tx='cafe\u0301')
        self.assertNotEqual(canonical_record(**nfc), canonical_record(**nfd))

    def test_existing_rows_at_cutover_remain_honestly_legacy(self):
        # Simulate an already-populated Runtime 0.1 DB by creating evidence, then
        # removing only the new feature metadata/sidecars before reopening. The
        # first feature-aware open sets cutover after those preserved rows.
        book = Notebook(self.vault)
        ident = book.bind('Jon', 'legacy simulation')
        book.start(ident['hcid'], 'tx', 'legacy-shaped row')
        book.close()
        with self.raw() as db:
            db.execute('DROP TRIGGER transcript_integrity_no_delete')
            db.execute('DELETE FROM transcript_integrity')
            db.execute("DELETE FROM runtime_meta WHERE key LIKE 'transcript_envelope_%'")
        reopened = Notebook(self.vault)
        try:
            self.assertEqual(reopened.transcript_integrity_cutover, 2)
            self.assertEqual(reopened.transcript_integrity_status(1),
                             'CONTENT_VERIFIED_METADATA_LEGACY')
            reopened.project()
            self.assertTrue(reopened.verify())
        finally:
            reopened.close()


if __name__ == '__main__':
    unittest.main()
''', encoding='utf-8')

print('record envelope patch staged')
