import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from source_reader import MAX_PAGE_BYTES, MAX_SOURCE_BYTES, SourceReader


class SourceReaderTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name).resolve()
        self.reader = SourceReader(self.root)
        self.source = self.root / 'server.py'
        self.source.write_text('print("HumanOS")\n', encoding='utf-8')

    def tearDown(self):
        self.directory.cleanup()

    def test_default_file_read_and_complete_hash(self):
        result = self.reader.read()
        self.assertEqual(result['text'], 'print("HumanOS")\n')
        self.assertEqual(result['sha256'], hashlib.sha256(self.source.read_bytes()).hexdigest())
        self.assertEqual(result['source'], str(self.source))
        self.assertEqual(result['path'], 'server.py')
        self.assertFalse(result['truncated'])
        self.assertIsNone(result['next_offset'])
        self.assertEqual(result['total_bytes'], len(self.source.read_bytes()))

    def test_unicode_pagination_reconstructs_exact_source_with_whole_file_hash(self):
        text = 'abc😀defé汉字\n' * 5
        self.source.write_text(text, encoding='utf-8')
        digest = hashlib.sha256(text.encode()).hexdigest()
        offset, pages = 0, []
        while offset is not None:
            page = self.reader.read(offset=offset, limit=5)
            self.assertLessEqual(len(page['text'].encode()), 5)
            self.assertEqual(page['sha256'], digest)
            pages.append(page['text'])
            if page['next_offset'] is not None:
                self.assertGreater(page['next_offset'], offset)
            offset = page['next_offset']
        self.assertEqual(''.join(pages), text)

    def test_invalid_offsets_and_limits_fail_explicitly(self):
        self.source.write_text('a😀b', encoding='utf-8')
        for arguments in ({'offset': -1}, {'offset': 2}, {'offset': 999}, {'offset': True},
                          {'offset': '0'}, {'limit': 0}, {'limit': 3}, {'limit': True},
                          {'limit': MAX_PAGE_BYTES + 1}):
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                self.reader.read(**arguments)
        self.assertEqual(self.reader.read(offset=6)['text'], '')

    def test_scope_rejects_private_and_arbitrary_paths(self):
        for path in ('config.json', '.env', 'HumanOS_Vault/notebook.sqlite3', 'workspace/a.py',
                     'backups/server.py', '.git/config', '../server.py', './server.py',
                     str(self.source), 'unknown.py', 'SERVER.py', None, ['server.py']):
            with self.subTest(path=path), self.assertRaises(PermissionError):
                self.reader.read(path)

    def test_missing_allowed_source_is_honest_error(self):
        with self.assertRaises(FileNotFoundError):
            self.reader.read('engine.py')

    def test_symlink_file_and_root_ancestor_rejected(self):
        (self.root / 'engine.py').symlink_to(self.source)
        with self.assertRaises(OSError):
            self.reader.read('engine.py')
        actual = self.root / 'actual'
        actual.mkdir()
        (actual / 'child').mkdir()
        (actual / 'child' / 'server.py').write_text('source')
        (self.root / 'alias').symlink_to(actual, target_is_directory=True)
        with self.assertRaises(OSError):
            SourceReader(self.root / 'alias' / 'child').read()

    def test_hardlink_directory_and_fifo_rejected_without_reading(self):
        os.link(self.source, self.root / 'engine.py')
        with self.assertRaises(PermissionError):
            self.reader.read()
        (self.root / 'notebook.py').mkdir()
        with self.assertRaises(PermissionError):
            self.reader.read('notebook.py')
        os.mkfifo(self.root / 'audit.py')
        with self.assertRaises(PermissionError):
            self.reader.read('audit.py')

    def test_total_file_budget_and_default_page_budget(self):
        self.source.write_bytes(b'x' * MAX_SOURCE_BYTES)
        result = self.reader.read()
        self.assertEqual(len(result['text']), MAX_PAGE_BYTES)
        self.assertTrue(result['truncated'])
        self.assertEqual(result['next_offset'], MAX_PAGE_BYTES)
        self.source.write_bytes(b'x' * (MAX_SOURCE_BYTES + 1))
        with self.assertRaisesRegex(ValueError, '256 KiB'):
            self.reader.read()

    def test_invalid_utf8_is_not_silently_transformed(self):
        self.source.write_bytes(b'valid\xffinvalid')
        with self.assertRaises(UnicodeDecodeError):
            self.reader.read()

    def test_concurrent_source_edit_rejected(self):
        original_read = os.read
        changed = []

        def change_after_read(fd, size):
            data = original_read(fd, size)
            if not changed:
                self.source.write_text('a changed source with a different length')
                changed.append(True)
            return data

        with patch('source_reader.os.read', side_effect=change_after_read):
            with self.assertRaisesRegex(RuntimeError, 'changed'):
                self.reader.read()


if __name__ == '__main__':
    unittest.main()
