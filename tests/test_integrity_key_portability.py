import json
import os
from pathlib import Path
import sqlite3
import stat
import tempfile
import unittest

from integrity_lifecycle import IntegrityKeyError, KEY_BYTES, KEY_ID_PREFIX
from notebook import Notebook
from vault_portability import (DB_FILE, MANIFEST, RECOVERY_FILE, VaultBackupError,
                               _encode, _seal_manifest, create_portable_backup,
                               restore_portable_backup, verify_portable_backup)


class IntegrityKeyLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def populated(self, name='vault'):
        vault = self.root / name
        book = Notebook(vault)
        ident = book.bind('Jon', 'opening')
        book.start(ident['hcid'], 'tx', 'protected human text')
        book.close()
        return vault

    def test_fresh_vault_creates_one_owner_only_key_and_binds_identity(self):
        vault = self.root / 'fresh'
        book = Notebook(vault)
        try:
            key_path = book.root / 'integrity.key'
            first = key_path.read_bytes()
            self.assertEqual(len(first), KEY_BYTES)
            if os.name == 'posix':
                self.assertEqual(stat.S_IMODE(key_path.stat().st_mode) & 0o077, 0)
            row = book.db.execute("SELECT value FROM runtime_meta WHERE key='integrity_key_id'").fetchone()
            self.assertTrue(row[0].startswith(KEY_ID_PREFIX))
        finally:
            book.close()
        reopened = Notebook(vault)
        try:
            self.assertEqual(reopened.integrity_key, first)
        finally:
            reopened.close()

    def test_missing_key_on_existing_vault_fails_without_generating_replacement(self):
        vault = self.populated()
        key_path = vault / 'runtime' / 'integrity.key'
        key_path.unlink()
        with self.assertRaisesRegex(IntegrityKeyError, 'missing from an existing vault'):
            Notebook(vault)
        self.assertFalse(key_path.exists())

    def test_replaced_key_fails_before_any_recovery_event_can_be_appended(self):
        vault = self.populated()
        db_path = vault / 'runtime' / 'notebook.sqlite3'
        with sqlite3.connect(db_path) as db:
            before = db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
        key_path = vault / 'runtime' / 'integrity.key'
        key_path.write_bytes(b'X' * KEY_BYTES)
        os.chmod(key_path, 0o600)
        with self.assertRaisesRegex(IntegrityKeyError, 'does not match this vault'):
            Notebook(vault)
        with sqlite3.connect(db_path) as db:
            after = db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
        self.assertEqual(after, before)

    def test_legacy_metadata_migration_validates_hmac_rows_before_binding(self):
        vault = self.populated()
        db_path = vault / 'runtime' / 'notebook.sqlite3'
        with sqlite3.connect(db_path) as db:
            db.execute('DROP TABLE runtime_meta')
            db.commit()
        book = Notebook(vault)
        try:
            self.assertTrue(book.db.execute(
                "SELECT value FROM runtime_meta WHERE key='integrity_key_id'").fetchone()[0].startswith(KEY_ID_PREFIX))
        finally:
            book.close()
        with sqlite3.connect(db_path) as db:
            db.execute('DROP TABLE runtime_meta')
            db.commit()
        key_path = vault / 'runtime' / 'integrity.key'
        key_path.write_bytes(b'Y' * KEY_BYTES)
        os.chmod(key_path, 0o600)
        with self.assertRaisesRegex(IntegrityKeyError, 'does not match existing protected transcript'):
            Notebook(vault)

    def test_symlink_hardlink_and_group_readable_keys_fail_closed(self):
        # Permission exposure.
        exposed = self.populated('exposed')
        exposed_key = exposed / 'runtime' / 'integrity.key'
        os.chmod(exposed_key, 0o644)
        with self.assertRaisesRegex(IntegrityKeyError, 'permissions are unsafe'):
            Notebook(exposed)

        # Symlink substitution.
        linked = self.populated('symlink')
        linked_key = linked / 'runtime' / 'integrity.key'
        outside = self.root / 'outside.key'
        outside.write_bytes(linked_key.read_bytes())
        os.chmod(outside, 0o600)
        linked_key.unlink()
        linked_key.symlink_to(outside)
        with self.assertRaisesRegex(IntegrityKeyError, 'ordinary non-linked'):
            Notebook(linked)

        # Hardlink substitution.
        hard = self.populated('hardlink')
        hard_key = hard / 'runtime' / 'integrity.key'
        preserved = self.root / 'preserved.key'
        hard_key.replace(preserved)
        os.link(preserved, hard_key)
        with self.assertRaisesRegex(IntegrityKeyError, 'ordinary non-linked'):
            Notebook(hard)


class PortableVaultBackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def source_vault(self, name='source'):
        vault = self.root / name
        book = Notebook(vault)
        ident = book.bind('Jon', 'portable opening')
        book.start(ident['hcid'], 'tx', 'portable exact human text')
        # Independent fallback is canonical recovery evidence and must travel too.
        fallback = book.root / RECOVERY_FILE
        fallback.write_text(json.dumps({'tx': 'orphan', 'error': 'retained fallback', 'payload': None}) + '\n',
                            encoding='utf-8')
        os.chmod(fallback, 0o600)
        book.project()
        self.assertTrue(book.verify())
        book.close()
        return vault

    def backup(self, name='bundle'):
        source = self.source_vault('source-' + name)
        bundle = self.root / name
        result = create_portable_backup(source, bundle)
        self.assertTrue(result['verified'])
        self.assertTrue(result['staged_restore_verified'])
        return source, bundle

    def db_dump(self, path):
        db = sqlite3.connect(str(path))
        try:
            tables = [row[0] for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
            return {table: db.execute('SELECT * FROM "' + table.replace('"', '""') + '" ORDER BY rowid').fetchall()
                    for table in tables}
        finally:
            db.close()

    def test_backup_restore_preserves_key_database_and_recovery_exactly(self):
        source, bundle = self.backup('roundtrip')
        verified = verify_portable_backup(bundle)
        self.assertTrue(verified['verified'])
        manifest = json.loads((bundle / MANIFEST).read_text())
        self.assertEqual(manifest['confidentiality'], 'PLAINTEXT_OWNER_ONLY')
        self.assertTrue(manifest['key_id'].startswith(KEY_ID_PREFIX))
        self.assertTrue(all(record['proof'].startswith('hmac-sha256:')
                            for record in manifest['files'].values()))
        self.assertFalse(any('sha256' == key for record in manifest['files'].values() for key in record))

        restored = self.root / 'restored'
        result = restore_portable_backup(bundle, restored)
        self.assertTrue(result['restored'])
        self.assertEqual((source / 'runtime/integrity.key').read_bytes(),
                         (restored / 'runtime/integrity.key').read_bytes())
        self.assertEqual((source / 'runtime/recovery.jsonl').read_bytes(),
                         (restored / 'runtime/recovery.jsonl').read_bytes())
        self.assertEqual(self.db_dump(source / 'runtime/notebook.sqlite3'),
                         self.db_dump(restored / 'runtime/notebook.sqlite3'))
        book = Notebook(restored)
        try:
            self.assertTrue(book.verify())
        finally:
            book.close()

    def test_backup_never_overwrites_and_restore_refuses_nonempty_destination(self):
        source = self.source_vault()
        bundle = self.root / 'bundle'
        bundle.mkdir()
        with self.assertRaises(FileExistsError):
            create_portable_backup(source, bundle)
        bundle.rmdir()
        create_portable_backup(source, bundle)
        destination = self.root / 'occupied'
        destination.mkdir()
        (destination / 'keep.txt').write_text('keep')
        with self.assertRaises(FileExistsError):
            restore_portable_backup(bundle, destination)
        self.assertEqual((destination / 'keep.txt').read_text(), 'keep')

    def test_tampered_database_manifest_and_key_are_rejected(self):
        _, db_bundle = self.backup('db-tamper')
        with open(db_bundle / DB_FILE, 'ab') as f:
            f.write(b'TAMPER')
        with self.assertRaisesRegex(VaultBackupError, 'authentication failed'):
            verify_portable_backup(db_bundle)

        _, manifest_bundle = self.backup('manifest-tamper')
        manifest_path = manifest_bundle / MANIFEST
        manifest = json.loads(manifest_path.read_text())
        manifest['files'][DB_FILE]['bytes'] += 1
        manifest_path.write_text(_encode(manifest) + '\n')
        os.chmod(manifest_path, 0o600)
        with self.assertRaisesRegex(VaultBackupError, 'manifest authentication failed'):
            verify_portable_backup(manifest_bundle)

        _, key_bundle = self.backup('key-tamper')
        key_path = key_bundle / 'integrity.key'
        key_path.write_bytes(b'Z' * KEY_BYTES)
        os.chmod(key_path, 0o600)
        with self.assertRaisesRegex(VaultBackupError, 'does not match its manifest'):
            verify_portable_backup(key_bundle)

    def test_staged_notebook_verification_rejects_semantic_db_tamper_even_if_manifest_is_resealed(self):
        _, bundle = self.backup('semantic-tamper')
        db_path = bundle / DB_FILE
        with sqlite3.connect(db_path) as db:
            db.execute("UPDATE transcript SET text='attacker changed plaintext' WHERE tx='tx' AND ordinal=0")
            db.commit()
        key = (bundle / 'integrity.key').read_bytes()
        files = {DB_FILE: db_path.read_bytes(), 'integrity.key': key,
                 RECOVERY_FILE: (bundle / RECOVERY_FILE).read_bytes()}
        manifest = _seal_manifest(key, files)
        manifest_path = bundle / MANIFEST
        manifest_path.write_text(_encode(manifest) + '\n')
        os.chmod(manifest_path, 0o600)
        self.assertTrue(verify_portable_backup(bundle)['verified'])
        with self.assertRaisesRegex(RuntimeError, 'Transcript hash mismatch'):
            restore_portable_backup(bundle, self.root / 'must-not-restore')
        self.assertFalse((self.root / 'must-not-restore').exists())

    def test_backup_destination_inside_source_vault_is_rejected(self):
        source = self.source_vault()
        with self.assertRaisesRegex(VaultBackupError, 'outside the source vault'):
            create_portable_backup(source, source / 'backup')


if __name__ == '__main__':
    unittest.main()
