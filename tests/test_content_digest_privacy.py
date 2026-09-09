import hashlib
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

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
        book = self.new_book()
        try:
            ident = book.bind('Jon', 'opening')
            text = 'legacy row'
            with book.db:
                book.db.execute('INSERT INTO transactions VALUES(?,?,?,?,?)',
                                ('legacy', ident['hcid'], text, 'STARTED', 'legacy-time'))
                book.db.execute('INSERT INTO transcript(tx,ordinal,role,text,sha256,created) VALUES(?,?,?,?,?,?)',
                                ('legacy', 0, 'HUMAN', text, digest(text), 'legacy-time'))
            book.project()
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
        reopened = Notebook(vault)
        try:
            with self.assertRaisesRegex(RuntimeError, 'Transcript hash mismatch'):
                reopened.verify()
        finally:
            reopened.close()

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
