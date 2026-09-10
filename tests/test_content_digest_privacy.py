import hashlib
import json
import os
import sqlite3
import stat
import tempfile
import unittest
from pathlib import Path

from integrity_lifecycle import IntegrityKeyError
from notebook import DIGEST_PREFIX, Notebook, digest


class ContentDigestPrivacyTests(unittest.TestCase):
    def new_book(self, name='vault'):
        root = Path(self.tmp.name) / name
        book = Notebook(root)
        book.recover()
        return book

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def test_new_transcript_digest_is_keyed_not_plain_sha256(self):
        book = self.new_book()
        try:
            ident = book.bind('Jon', 'same opening')
            book.start(ident['hcid'], 'tx', 'predictable plaintext')
            stored = book.db.execute("SELECT sha256 FROM transcript WHERE tx='tx'").fetchone()[0]
            self.assertTrue(stored.startswith(DIGEST_PREFIX))
            self.assertNotEqual(stored, hashlib.sha256(b'predictable plaintext').hexdigest())
            self.assertTrue(book.verify())
        finally:
            book.close()

    def test_same_plaintext_in_different_vaults_has_different_digest(self):
        one = self.new_book('one')
        two = self.new_book('two')
        try:
            a = one.bind('Jon', 'opening')
            b = two.bind('Jon', 'opening')
            one.start(a['hcid'], 'tx-a', 'same secret-shaped text')
            two.start(b['hcid'], 'tx-b', 'same secret-shaped text')
            da = one.db.execute("SELECT sha256 FROM transcript WHERE tx='tx-a'").fetchone()[0]
            db = two.db.execute("SELECT sha256 FROM transcript WHERE tx='tx-b'").fetchone()[0]
            self.assertNotEqual(da, db)
        finally:
            one.close()
            two.close()

    def test_integrity_key_is_local_owner_only_and_not_projected(self):
        book = self.new_book()
        try:
            key_path = book.root / 'integrity.key'
            self.assertEqual(len(key_path.read_bytes()), 32)
            if os.name == 'posix':
                mode = stat.S_IMODE(key_path.stat().st_mode)
                self.assertEqual(mode & 0o077, 0)
            ident = book.bind('Jon', 'opening')
            book.start(ident['hcid'], 'tx', 'text')
            book.project()
            key_hex = key_path.read_bytes().hex()
            for path in book.root.rglob('*'):
                if path.is_file() and path != key_path and path.suffix in ('.json', '.md'):
                    self.assertNotIn(key_hex, path.read_text(encoding='utf-8'))
        finally:
            book.close()

    def test_legacy_sha256_transcript_remains_verifiable(self):
        vault = Path(self.tmp.name) / 'legacy-vault'
        runtime = vault / 'runtime'
        runtime.mkdir(parents=True, mode=0o700)
        db = sqlite3.connect(runtime / 'notebook.sqlite3')
        try:
            db.executescript("""
                CREATE TABLE identities(
                  hcid TEXT PRIMARY KEY, owner TEXT NOT NULL, page TEXT UNIQUE NOT NULL,
                  binding TEXT NOT NULL, opening_hash TEXT NOT NULL, created TEXT NOT NULL);
                CREATE TABLE transactions(
                  tx TEXT PRIMARY KEY, hcid TEXT NOT NULL REFERENCES identities(hcid),
                  input TEXT NOT NULL, status TEXT NOT NULL, created TEXT NOT NULL);
                CREATE TABLE transcript(
                  seq INTEGER PRIMARY KEY AUTOINCREMENT, tx TEXT NOT NULL REFERENCES transactions(tx),
                  ordinal INTEGER NOT NULL, role TEXT NOT NULL, text TEXT NOT NULL,
                  sha256 TEXT NOT NULL, created TEXT NOT NULL, UNIQUE(tx,ordinal));
            """)
            text = 'legacy row'
            db.execute('INSERT INTO identities VALUES(?,?,?,?,?,?)',
                       ('legacy-hcid', 'Jon', 'legacy-page', 'VERIFIED', digest('opening'), 'legacy-time'))
            db.execute('INSERT INTO transactions VALUES(?,?,?,?,?)',
                       ('legacy', 'legacy-hcid', text, 'STARTED', 'legacy-time'))
            db.execute('INSERT INTO transcript(tx,ordinal,role,text,sha256,created) VALUES(?,?,?,?,?,?)',
                       ('legacy', 0, 'HUMAN', text, digest(text), 'legacy-time'))
            db.commit()
        finally:
            db.close()
        book = Notebook(vault)
        try:
            book.project()
            row = book.db.execute("SELECT * FROM transcript WHERE tx='legacy'").fetchone()
            self.assertIsNone(row['record_integrity'])
            self.assertIsNone(row['record_integrity_version'])
            self.assertTrue(book.verify())
        finally:
            book.close()

    def test_wrong_key_fails_closed_for_new_rows(self):
        vault = Path(self.tmp.name) / 'vault'
        book = Notebook(vault)
        ident = book.bind('Jon', 'opening')
        book.start(ident['hcid'], 'tx', 'protected text')
        book.close()
        key_path = vault / 'runtime' / 'integrity.key'
        key_path.write_bytes(b'X' * 32)
        os.chmod(key_path, 0o600)
        with self.assertRaisesRegex(IntegrityKeyError, 'does not match this vault'):
            Notebook(vault)

    def test_delivery_events_use_content_digest_not_plain_sha256(self):
        book = self.new_book()
        try:
            ident = book.bind('Jon', 'opening')
            book.start(ident['hcid'], 'tx', 'hello')
            final = 'predictable final'
            book.append('tx', 1, 'ASSISTANT', final)
            book.save_task('tx', {'phase': 'COMPLETE', 'final': final, 'final_ordinal': 1,
                                  'delivery': 'PREPARED_NOT_CONFIRMED'})
            book.checkpoint('tx')
            self.assertTrue(book.prepare_delivery('tx', final))
            started = json.loads(book.db.execute(
                "SELECT payload FROM events WHERE tx='tx' AND kind='DELIVERY_STARTED'").fetchone()[0])
            self.assertIn('content_digest', started)
            self.assertNotIn('sha256', started)
            self.assertTrue(started['content_digest'].startswith(DIGEST_PREFIX))
            self.assertNotEqual(started['content_digest'], hashlib.sha256(final.encode()).hexdigest())
            self.assertTrue(book.finish_delivery('tx'))
            delivered = json.loads(book.db.execute(
                "SELECT payload FROM events WHERE tx='tx' AND kind='DELIVERY'").fetchone()[0])
            self.assertIn('content_digest', delivered)
            self.assertNotIn('sha256', delivered)
        finally:
            book.close()

    def test_existing_legacy_delivery_digest_can_still_finish(self):
        book = self.new_book()
        try:
            ident = book.bind('Jon', 'opening')
            book.start(ident['hcid'], 'tx', 'hello')
            final = 'legacy delivery final'
            book.append('tx', 1, 'ASSISTANT', final)
            state = {'phase': 'COMPLETE', 'final': final, 'final_ordinal': 1,
                     'delivery': 'DELIVERING', 'delivery_attempt': 'old-attempt',
                     'delivery_sha256': digest(final)}
            book.save_task('tx', state)
            book.checkpoint('tx')
            self.assertTrue(book.finish_delivery('tx'))
        finally:
            book.close()


if __name__ == '__main__':
    unittest.main()
