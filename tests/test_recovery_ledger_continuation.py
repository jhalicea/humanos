import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from continue_recovery_ledger import apply_continuation
from notebook import Notebook
from recovery_continuation import ContinuationError, continue_recovery_ledger
from recovery_ledger import RecoveryLedgerCorrupt, parse_recovery_file


class RecoveryLedgerContinuationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self.tmp.name) / 'vault'
        self.book = Notebook(self.vault)
        self.book.recover()
        self.path = self.book.root / 'recovery.jsonl'

    def tearDown(self):
        self.book.close()
        self.tmp.cleanup()

    def write_raw(self, data):
        self.path.write_bytes(data)
        os.chmod(self.path, 0o600)

    def test_clean_terminated_ledger_refuses_continuation(self):
        self.write_raw(b'{"tx":null}\n')
        with self.assertRaisesRegex(ContinuationError, 'not sealed'):
            continue_recovery_ledger(self.book.root, self.book.integrity_key)

    def test_valid_unterminated_record_is_archived_exactly_and_continues(self):
        original = b'{"tx":null,"payload":{"note":"complete"}}'
        self.write_raw(original)
        result = continue_recovery_ledger(self.book.root, self.book.integrity_key)
        archive = self.book.root / result['archive_path']
        self.assertEqual((archive / 'recovery.jsonl').read_bytes(), original)
        self.assertTrue(self.path.read_bytes().endswith(b'\n'))
        parsed = parse_recovery_file(self.path)
        self.assertIsNone(parsed.anomaly)
        self.assertIsNone(parsed.quarantine)
        self.assertEqual(parsed.records[0]['scope'], 'LEDGER_CONTINUATION')
        self.assertEqual(parsed.records[0]['payload']['continuation_id'], result['continuation_id'])

    def test_truncated_tail_is_preserved_in_archive_and_existing_quarantine(self):
        original = b'{"tx":"old","payload":null}\n{"tx":"cut"'
        self.write_raw(original)
        result = continue_recovery_ledger(self.book.root, self.book.integrity_key)
        archive = self.book.root / result['archive_path']
        self.assertEqual((archive / 'recovery.jsonl').read_bytes(), original)
        quarantine_root = self.book.root / 'recovery-quarantine'
        self.assertTrue(any(path.name == 'tail.bin' for path in quarantine_root.rglob('tail.bin')))

    def test_repeated_continuation_is_idempotent(self):
        self.write_raw(b'{"tx":null}')
        first = continue_recovery_ledger(self.book.root, self.book.integrity_key)
        active = self.path.read_bytes()
        second = continue_recovery_ledger(self.book.root, self.book.integrity_key)
        self.assertEqual(second['continuation_id'], first['continuation_id'])
        self.assertTrue(second['already_continued'])
        self.assertEqual(self.path.read_bytes(), active)
        archives = [p for p in (self.book.root / 'recovery-archive').iterdir() if p.is_dir()]
        self.assertEqual(len(archives), 1)

    def test_malformed_middle_record_cannot_continue(self):
        self.write_raw(b'{"tx":null}\nnot-json\n{"tx":"tail"')
        with self.assertRaises(RecoveryLedgerCorrupt):
            continue_recovery_ledger(self.book.root, self.book.integrity_key)

    def test_tampered_archive_fails_closed_on_idempotent_retry(self):
        self.write_raw(b'{"tx":null}')
        result = continue_recovery_ledger(self.book.root, self.book.integrity_key)
        archive = self.book.root / result['archive_path'] / 'recovery.jsonl'
        archive.write_bytes(b'tampered')
        with self.assertRaisesRegex(ContinuationError, 'archive'):
            continue_recovery_ledger(self.book.root, self.book.integrity_key)

    def test_interruption_after_archive_can_resume(self):
        original = b'{"tx":null}'
        self.write_raw(original)
        real_replace = os.replace
        with mock.patch('recovery_continuation.os.replace', side_effect=OSError('simulated stop')):
            with self.assertRaisesRegex(OSError, 'simulated stop'):
                continue_recovery_ledger(self.book.root, self.book.integrity_key)
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(len(list((self.book.root / 'recovery-archive').glob('cont-*'))), 1)
        with mock.patch('recovery_continuation.os.replace', side_effect=real_replace):
            result = continue_recovery_ledger(self.book.root, self.book.integrity_key)
        self.assertFalse(result['already_continued'])
        self.assertTrue(self.path.read_bytes().endswith(b'\n'))

    def test_normal_recovery_writer_can_append_after_continuation(self):
        self.write_raw(b'{"tx":null}')
        continue_recovery_ledger(self.book.root, self.book.integrity_key)
        before = len(parse_recovery_file(self.path).records)
        self.book.problem(None, 'post-continuation evidence')
        after = parse_recovery_file(self.path).records
        self.assertEqual(len(after), before + 1)
        self.assertEqual(after[-1]['error'], 'post-continuation evidence')

    def test_explicit_application_records_one_sqlite_audit_event(self):
        self.write_raw(b'{"tx":null}')
        first = apply_continuation(self.book)
        second = apply_continuation(self.book)
        self.assertEqual(first['continuation_id'], second['continuation_id'])
        count = self.book.db.execute(
            "SELECT COUNT(*) FROM events WHERE kind='RECOVERY_LEDGER_CONTINUED'"
        ).fetchone()[0]
        self.assertEqual(count, 1)

    def test_unsafe_archive_root_permissions_fail_closed(self):
        self.write_raw(b'{"tx":null}')
        archive_root = self.book.root / 'recovery-archive'
        archive_root.mkdir(mode=0o700)
        if os.name == 'posix':
            os.chmod(archive_root, 0o755)
            with self.assertRaisesRegex(ContinuationError, 'archive root permissions are unsafe'):
                continue_recovery_ledger(self.book.root, self.book.integrity_key)


    def test_normal_notebook_open_verifies_continuation_archive(self):
        self.write_raw(b'{"tx":null}')
        result = continue_recovery_ledger(self.book.root, self.book.integrity_key)
        archive_file = self.book.root / result['archive_path'] / 'recovery.jsonl'
        archive_file.write_bytes(b'tampered')
        self.book.close()
        with self.assertRaisesRegex(ContinuationError, 'archive'):
            Notebook(self.vault)

    def test_normal_notebook_open_rejects_missing_continuation_archive(self):
        self.write_raw(b'{"tx":null}')
        result = continue_recovery_ledger(self.book.root, self.book.integrity_key)
        archive = self.book.root / result['archive_path']
        (archive / 'recovery.jsonl').unlink()
        (archive / 'manifest.json').unlink()
        archive.rmdir()
        self.book.close()
        with self.assertRaisesRegex(ContinuationError, 'archive'):
            Notebook(self.vault)

    def test_normal_notebook_open_rejects_tampered_continuation_header(self):
        self.write_raw(b'{"tx":null}')
        continue_recovery_ledger(self.book.root, self.book.integrity_key)
        parsed = parse_recovery_file(self.path)
        header = dict(parsed.records[0])
        header['created'] = 'tampered-time'
        self.path.write_text(__import__('json').dumps(header, sort_keys=True) + '\n', encoding='utf-8')
        os.chmod(self.path, 0o600)
        self.book.close()
        with self.assertRaisesRegex(ContinuationError, 'timestamp'):
            Notebook(self.vault)


if __name__ == '__main__':
    unittest.main()
