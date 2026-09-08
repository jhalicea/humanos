import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from file_manager import FileManager
from notebook import Notebook, encode
from runtime_info import request_for, format_observation


class FileManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.workspace = self.root / 'files'
        self.workspace.mkdir()
        self.book = Notebook(self.root / 'vault')
        self.book.recover()
        self.manager = FileManager(self.workspace, self.book)

    def tearDown(self):
        self.book.close()
        self.tmp.cleanup()

    def file(self, path, text='content'):
        target = self.workspace / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        return target

    def test_preview_apply_restart_undo_retains_exact_bytes_and_inode(self):
        original = self.file('note.txt', '  exact\nUnicode 🧭\n')
        data, inode = original.read_bytes(), original.stat().st_ino
        plan = self.manager.plan_organize()
        self.assertEqual(plan['status'], 'PREVIEW')
        self.assertTrue(original.exists())
        with self.assertRaises(PermissionError): self.manager.apply(plan['plan_id'])
        applied = self.manager.apply(plan['plan_id'], authorized=True)
        destination = self.workspace / 'Documents/note.txt'
        self.assertEqual(destination.read_bytes(), data)
        self.assertEqual(destination.stat().st_ino, inode)
        self.assertFalse(original.exists())
        self.book.close()
        self.book = Notebook(self.root / 'vault')
        self.book.recover()
        self.manager = FileManager(self.workspace, self.book)
        self.assertEqual(self.manager.apply(plan['plan_id'], True), applied)
        self.assertEqual(self.manager.undo(plan['plan_id'], True)['status'], 'UNDONE')
        self.assertEqual(original.read_bytes(), data)
        self.assertEqual(self.manager.undo(plan['plan_id'], True)['status'], 'UNDONE')
        self.assertTrue(self.book.verify())

    def test_nested_folder_move_and_undo(self):
        original = self.file('Project/Sub/note.txt', 'nested')
        plan = self.manager.plan_move('Project', 'Archive/Renamed')
        self.manager.apply(plan['plan_id'], True)
        self.assertEqual((self.workspace / 'Archive/Renamed/Sub/note.txt').read_text(), 'nested')
        self.manager.undo(plan['plan_id'], True)
        self.assertEqual(original.read_text(), 'nested')

    def test_existing_destination_never_overwritten(self):
        self.file('note.txt', 'original')
        protected = self.file('Documents/note.txt', 'do not overwrite')
        plan = self.manager.plan_move('note.txt', 'Documents/note.txt')
        with self.assertRaises(FileExistsError): self.manager.apply(plan['plan_id'], True)
        self.assertEqual(protected.read_text(), 'do not overwrite')
        self.assertEqual(self.manager.get_plan(plan['plan_id'])['status'], 'NEEDS_RECONCILIATION')
        self.assertEqual(self.manager.pending()[0]['plan_id'], plan['plan_id'])
        self.assertTrue((self.workspace / 'note.txt').exists())

    def test_destination_created_during_move_cannot_be_overwritten(self):
        self.file('note.txt')
        plan = self.manager.plan_move('note.txt', 'moved.txt')
        import file_manager
        native = file_manager.rename_exclusive
        def collide(*args):
            self.file('moved.txt', 'concurrent')
            return native(*args)
        with patch('file_manager.rename_exclusive', side_effect=collide), self.assertRaises(FileExistsError):
            self.manager.apply(plan['plan_id'], True)
        self.assertEqual((self.workspace / 'moved.txt').read_text(), 'concurrent')
        self.assertTrue((self.workspace / 'note.txt').exists())

    def test_changed_source_and_changed_undo_target_fail_closed(self):
        source = self.file('note.txt')
        plan = self.manager.plan_move('note.txt', 'moved.txt')
        source.write_text('changed')
        with self.assertRaisesRegex(RuntimeError, 'changed'): self.manager.apply(plan['plan_id'], True)
        plan = self.manager.plan_move('note.txt', 'moved.txt')
        self.manager.apply(plan['plan_id'], True)
        (self.workspace / 'moved.txt').write_text('edited after move')
        with self.assertRaisesRegex(RuntimeError, 'changed'): self.manager.undo(plan['plan_id'], True)
        self.assertEqual((self.workspace / 'moved.txt').read_text(), 'edited after move')

    def test_source_replaced_before_native_move_is_rejected(self):
        source = self.file('note.txt')
        plan = self.manager.plan_move('note.txt', 'moved.txt')
        move = self.manager._move
        def replace(*args):
            source.rename(self.workspace / 'preserved.txt')
            self.file('note.txt', 'replacement')
            return move(*args)
        with patch.object(self.manager, '_move', side_effect=replace), self.assertRaisesRegex(RuntimeError, 'identity changed'):
            self.manager.apply(plan['plan_id'], True)
        self.assertFalse((self.workspace / 'moved.txt').exists())
        self.assertEqual(source.read_text(), 'replacement')

    def test_crash_after_rename_reconciles_without_repeating_move(self):
        self.file('note.txt')
        plan = self.manager.plan_move('note.txt', 'moved.txt')
        move = self.manager._move
        def crash(*args):
            move(*args)
            raise KeyboardInterrupt('simulated process death after rename')
        with patch.object(self.manager, '_move', side_effect=crash), self.assertRaises(KeyboardInterrupt):
            self.manager.apply(plan['plan_id'], True)
        self.book.close()
        self.book = Notebook(self.root / 'vault')
        self.manager = FileManager(self.workspace, self.book)
        with patch.object(self.manager, '_move', side_effect=AssertionError('must not repeat')):
            self.assertEqual(self.manager.apply(plan['plan_id'], True)['status'], 'APPLIED')

    def test_undo_can_reconcile_interrupted_apply(self):
        self.file('note.txt')
        plan = self.manager.plan_move('note.txt', 'moved.txt')
        move = self.manager._move
        def crash(*args):
            move(*args)
            raise KeyboardInterrupt()
        with patch.object(self.manager, '_move', side_effect=crash), self.assertRaises(KeyboardInterrupt):
            self.manager.apply(plan['plan_id'], True)
        self.assertEqual(self.manager.undo(plan['plan_id'], True)['status'], 'UNDONE')
        self.assertTrue((self.workspace / 'note.txt').exists())

    def test_partial_plan_can_be_undone_after_collision(self):
        self.file('a.txt'); self.file('b.txt')
        self.file('Documents/b.txt', 'existing')
        plan = self.manager.plan_organize()
        with self.assertRaises(FileExistsError): self.manager.apply(plan['plan_id'], True)
        self.manager.undo(plan['plan_id'], True)
        self.assertTrue((self.workspace / 'a.txt').exists())
        self.assertTrue((self.workspace / 'b.txt').exists())
        self.assertEqual((self.workspace / 'Documents/b.txt').read_text(), 'existing')

    def test_duplicates_use_full_contents_not_names_and_never_delete(self):
        self.file('one/a.txt', 'duplicate')
        self.file('two/different.bin', 'duplicate')
        self.file('two/a.txt', 'different')
        report = self.manager.duplicates()
        self.assertEqual(len(report['groups']), 1)
        self.assertEqual(set(report['groups'][0]['files']), {'one/a.txt', 'two/different.bin'})
        self.assertFalse(report['incomplete'])
        self.assertEqual(len(list(self.workspace.rglob('*.*'))), 3)

    def test_links_hidden_special_and_protected_entries_excluded(self):
        target = self.file('a.txt')
        self.file('.private'); self.file('HumanOS_Vault/secret.txt')
        (self.workspace / 'alias').symlink_to(self.root)
        os.link(target, self.workspace / 'hardlink')
        os.mkfifo(self.workspace / 'pipe')
        self.assertEqual(self.manager.scan()['entries'], [])
        self.assertEqual(len(self.manager.scan()['skipped']), 6)
        for path in ('../a.txt', '/etc/passwd', '.private', 'HumanOS_Vault/secret.txt', 'alias/vault'):
            with self.subTest(path=path), self.assertRaises((OSError, PermissionError)):
                self.manager.plan_move(path, 'moved')

    def test_folder_with_excluded_descendant_cannot_be_moved(self):
        self.file('Project/.private', 'secret')
        with self.assertRaises(PermissionError): self.manager.plan_move('Project', 'Moved')

    def test_changed_workspace_identity_rejected(self):
        self.file('note.txt')
        plan = self.manager.plan_organize()
        self.workspace.rename(self.root / 'previous')
        self.workspace.mkdir()
        with self.assertRaisesRegex(PermissionError, 'identity changed'): self.manager.apply(plan['plan_id'], True)

    def test_symlink_destination_parent_rejected(self):
        self.file('note.txt')
        (self.root / 'outside').mkdir()
        (self.workspace / 'Documents').symlink_to(self.root / 'outside')
        plan = self.manager.plan_move('note.txt', 'Documents/note.txt')
        with self.assertRaises(OSError): self.manager.apply(plan['plan_id'], True)
        self.assertEqual(list((self.root / 'outside').iterdir()), [])

    def test_tampered_plan_or_state_is_not_executed(self):
        self.file('note.txt')
        plan = self.manager.plan_organize()
        row = self.book.db.execute('SELECT state FROM file_plans').fetchone()
        state = json.loads(row[0]); state['completed'] = [0]
        with self.book.db: self.book.db.execute('UPDATE file_plans SET state=?', (encode(state),))
        with self.assertRaisesRegex(RuntimeError, 'progress'): self.manager.apply(plan['plan_id'], True)
        with self.assertRaises(ValueError): self.manager.get_plan('%')

    def test_shared_hash_budget_and_scan_limit(self):
        self.file('a.txt', '1234'); self.file('b.txt', '1234')
        with patch('file_manager.MAX_BYTES', 4):
            with self.assertRaisesRegex(ValueError, 'limit'): self.manager.plan_organize()
            report = self.manager.duplicates()
            self.assertTrue(report['incomplete'])
        with patch('file_manager.MAX_ENTRIES', 1):
            report = self.manager.scan()
            self.assertTrue(report['truncated'])
            self.assertLessEqual(len(report['entries']), 1)

    def test_natural_language_never_silently_widens_folder_scope(self):
        for text in ('find duplicates in Documents', 'organize my files in Receipts',
                     'find duplicates but avoid Secret', 'find duplicates excluding Secret'):
            self.assertIsNone(request_for(text, []), text)
        self.assertEqual(request_for('/duplicates "My Files"', []), {'name': 'find_duplicates', 'path': 'My Files'})
        self.assertIsNone(request_for('read folder/server.py', []))
        self.assertIsNone(request_for('read server.py.bak', []))

    def test_plan_output_is_readable_and_discloses_empty_folder_limit(self):
        self.file('note.txt')
        plan = self.manager.plan_organize()
        text = format_observation({'name': 'plan_organization'}, {'ok': True, 'stdout': encode(plan)})
        self.assertIn('note.txt → Documents/note.txt', text)
        self.assertIn('empty folders', text)
        self.assertNotIn('inode', text)
        self.assertIn('/apply ' + plan['plan_id'], text)


if __name__ == '__main__':
    unittest.main()
