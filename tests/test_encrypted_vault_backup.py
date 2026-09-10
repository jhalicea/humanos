import json
import os
from pathlib import Path
import sqlite3
import stat
import struct
import tempfile
import unittest

try:
    import cryptography  # noqa: F401
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

from notebook import Notebook
from vault_encryption import (MAGIC, EncryptedBackupError, create_encrypted_backup,
                              main, restore_encrypted_backup, verify_encrypted_backup)


@unittest.skipUnless(HAS_CRYPTOGRAPHY, 'optional encrypted-backup dependency is not installed')
class EncryptedVaultBackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.passphrase = 'correct horse battery staple for HumanOS'

    def tearDown(self):
        self.tmp.cleanup()

    def source_vault(self, name='source'):
        vault = self.root / name
        book = Notebook(vault)
        ident = book.bind('Jon', 'portable encrypted opening')
        book.start(ident['hcid'], 'tx', 'HUMANOS-SECRET-HUMAN-PAYLOAD-49381')
        final = 'HUMANOS-SECRET-ASSISTANT-PAYLOAD-92744'
        book.append('tx', 1, 'ASSISTANT', final)
        book.save_task('tx', {'phase': 'COMPLETE', 'final': final, 'final_ordinal': 1,
                              'delivery': 'PREPARED_NOT_CONFIRMED'})
        book.checkpoint('tx')
        fallback = book.root / 'recovery.jsonl'
        fallback.write_text(json.dumps({'tx': 'orphan', 'error': 'HUMANOS-SECRET-RECOVERY-55128',
                                        'payload': None}) + '\n', encoding='utf-8')
        os.chmod(fallback, 0o600)
        book.project()
        self.assertTrue(book.verify())
        key = bytes(book.integrity_key)
        book.close()
        return vault, key

    def db_dump(self, path):
        db = sqlite3.connect(str(path))
        try:
            tables = [row[0] for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
            return {table: db.execute('SELECT * FROM "' + table.replace('"', '""') + '" ORDER BY rowid').fetchall()
                    for table in tables}
        finally:
            db.close()

    def make_backup(self, name='vault.hosenc'):
        source, key = self.source_vault('source-' + name.replace('.', '-'))
        encrypted = self.root / name
        result = create_encrypted_backup(source, encrypted, self.passphrase)
        self.assertTrue(result['verified'])
        self.assertTrue(result['staged_restore_verified'])
        return source, key, encrypted

    def test_encrypted_backup_roundtrip_preserves_exact_notebook_state(self):
        source, key, encrypted = self.make_backup()
        data = encrypted.read_bytes()
        self.assertTrue(data.startswith(MAGIC))
        self.assertNotIn(b'SQLite format 3', data)
        self.assertNotIn(b'HUMANOS-SECRET-HUMAN-PAYLOAD-49381', data)
        self.assertNotIn(b'HUMANOS-SECRET-ASSISTANT-PAYLOAD-92744', data)
        self.assertNotIn(b'HUMANOS-SECRET-RECOVERY-55128', data)
        self.assertNotIn(key, data)
        if os.name == 'posix':
            self.assertEqual(stat.S_IMODE(encrypted.stat().st_mode) & 0o077, 0)

        verified = verify_encrypted_backup(encrypted, self.passphrase)
        self.assertTrue(verified['verified'])
        restored = self.root / 'restored'
        result = restore_encrypted_backup(encrypted, restored, self.passphrase)
        self.assertTrue(result['restored'])
        self.assertTrue(result['encrypted'])
        self.assertEqual(key, (restored / 'runtime/integrity.key').read_bytes())
        self.assertEqual((source / 'runtime/recovery.jsonl').read_bytes(),
                         (restored / 'runtime/recovery.jsonl').read_bytes())
        self.assertEqual(self.db_dump(source / 'runtime/notebook.sqlite3'),
                         self.db_dump(restored / 'runtime/notebook.sqlite3'))
        book = Notebook(restored)
        try:
            self.assertTrue(book.verify())
        finally:
            book.close()

    def test_wrong_passphrase_fails_before_restore_and_places_nothing(self):
        _, _, encrypted = self.make_backup('wrong-pass.hosenc')
        with self.assertRaisesRegex(EncryptedBackupError, 'authentication failed'):
            verify_encrypted_backup(encrypted, 'definitely wrong passphrase')
        destination = self.root / 'must-not-exist'
        with self.assertRaisesRegex(EncryptedBackupError, 'authentication failed'):
            restore_encrypted_backup(encrypted, destination, 'definitely wrong passphrase')
        self.assertFalse(destination.exists())

    def test_ciphertext_and_tag_tamper_fail_authentication(self):
        _, _, encrypted = self.make_backup('tamper.hosenc')
        original = encrypted.read_bytes()
        header_len = struct.unpack('>I', original[len(MAGIC):len(MAGIC) + 4])[0]
        payload_start = len(MAGIC) + 4 + header_len

        ciphertext = bytearray(original)
        ciphertext[payload_start + 10] ^= 0x01
        encrypted.write_bytes(ciphertext)
        os.chmod(encrypted, 0o600)
        with self.assertRaisesRegex(EncryptedBackupError, 'authentication failed'):
            verify_encrypted_backup(encrypted, self.passphrase)

        encrypted.write_bytes(original)
        tag = bytearray(original)
        tag[-1] ^= 0x01
        encrypted.write_bytes(tag)
        os.chmod(encrypted, 0o600)
        with self.assertRaisesRegex(EncryptedBackupError, 'authentication failed'):
            verify_encrypted_backup(encrypted, self.passphrase)

    def test_header_tamper_is_rejected(self):
        _, _, encrypted = self.make_backup('header.hosenc')
        raw = bytearray(encrypted.read_bytes())
        header_len = struct.unpack('>I', raw[len(MAGIC):len(MAGIC) + 4])[0]
        start = len(MAGIC) + 4
        header = json.loads(bytes(raw[start:start + header_len]).decode('utf-8'))
        nonce = header['cipher']['nonce']
        replacement = ('A' if nonce[0] != 'A' else 'B') + nonce[1:]
        header['cipher']['nonce'] = replacement
        replacement_raw = json.dumps(header, ensure_ascii=False, sort_keys=True,
                                     separators=(',', ':')).encode('utf-8')
        self.assertEqual(len(replacement_raw), header_len)
        raw[start:start + header_len] = replacement_raw
        encrypted.write_bytes(raw)
        os.chmod(encrypted, 0o600)
        with self.assertRaises(EncryptedBackupError):
            verify_encrypted_backup(encrypted, self.passphrase)

    def test_same_vault_and_passphrase_use_fresh_salt_and_nonce(self):
        source, _ = self.source_vault('unique-source')
        first = self.root / 'first.hosenc'
        second = self.root / 'second.hosenc'
        create_encrypted_backup(source, first, self.passphrase)
        create_encrypted_backup(source, second, self.passphrase)
        self.assertNotEqual(first.read_bytes(), second.read_bytes())
        self.assertTrue(verify_encrypted_backup(first, self.passphrase)['verified'])
        self.assertTrue(verify_encrypted_backup(second, self.passphrase)['verified'])

    def test_backup_never_overwrites_and_restore_refuses_nonempty_destination(self):
        source, _ = self.source_vault('overwrite-source')
        encrypted = self.root / 'existing.hosenc'
        encrypted.write_bytes(b'preserve-me')
        os.chmod(encrypted, 0o600)
        with self.assertRaises(FileExistsError):
            create_encrypted_backup(source, encrypted, self.passphrase)
        self.assertEqual(encrypted.read_bytes(), b'preserve-me')

        encrypted.unlink()
        create_encrypted_backup(source, encrypted, self.passphrase)
        destination = self.root / 'occupied'
        destination.mkdir()
        (destination / 'keep.txt').write_text('keep', encoding='utf-8')
        with self.assertRaises(FileExistsError):
            restore_encrypted_backup(encrypted, destination, self.passphrase)
        self.assertEqual((destination / 'keep.txt').read_text(), 'keep')

    def test_empty_passphrase_is_rejected(self):
        source, _ = self.source_vault('empty-pass-source')
        with self.assertRaisesRegex(EncryptedBackupError, 'nonempty'):
            create_encrypted_backup(source, self.root / 'empty.hosenc', '')
        self.assertFalse((self.root / 'empty.hosenc').exists())

    def test_cli_has_no_passphrase_argument(self):
        # argparse must reject secrets in argv before getpass can run.
        with self.assertRaises(SystemExit):
            main(['verify', 'missing.hosenc', '--passphrase', 'do-not-allow-this'])


if __name__ == '__main__':
    unittest.main()
