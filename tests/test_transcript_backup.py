import json
import tempfile
import unittest
from pathlib import Path

from conversation_capture import UniversalConversationCapture
from notebook import Notebook
from transcript_backup import (
    ARTIFACT_JSONL,
    ARTIFACT_MARKDOWN,
    TranscriptBackupError,
    TranscriptBatchOutbox,
)


class TranscriptBatchOutboxTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.book = Notebook(self.root / 'vault')
        self.book.recover()
        self.binding = self.book.bind('Jon', 'opening')
        self.capture = UniversalConversationCapture(self.book, 'chatgpt')
        self.outbox = TranscriptBatchOutbox(self.book)

    def tearDown(self):
        self.book.close()
        self.tmp.cleanup()

    def _remote_receipt(self, manifest):
        return {
            name: {'id': 'drive-' + name, 'sha256': record['sha256']}
            for name, record in manifest['files'].items()
        }

    def test_prepare_batch_preserves_exact_unicode_whitespace(self):
        human = '  exact human 🧭\nsecond line\t  '
        assistant = 'assistant exact\n\nwith trailing spaces   '
        self.capture.capture_turn(
            self.binding['hcid'], 'conversation-1', 'turn-1', human, assistant
        )

        manifest = self.outbox.prepare_batch()
        self.assertEqual(manifest['first_seq'], 1)
        self.assertEqual(manifest['last_seq'], 2)
        self.assertEqual(manifest['record_count'], 2)
        self.assertEqual(self.outbox.last_confirmed_seq(), 0)

        paths = self.outbox.artifact_paths(manifest['batch_id'])
        rows = [json.loads(line) for line in paths[ARTIFACT_JSONL].read_text(encoding='utf-8').splitlines()]
        self.assertEqual(rows[0]['role'], 'HUMAN')
        self.assertEqual(rows[0]['text'], human)
        self.assertEqual(rows[1]['role'], 'ASSISTANT')
        self.assertEqual(rows[1]['text'], assistant)
        markdown = paths[ARTIFACT_MARKDOWN].read_text(encoding='utf-8')
        self.assertIn(human, markdown)
        self.assertIn(assistant, markdown)

    def test_pending_retry_returns_same_batch(self):
        self.capture.capture_turn(
            self.binding['hcid'], 'conversation-1', 'turn-1', 'hello', 'world'
        )
        first = self.outbox.prepare_batch(max_records=1)
        second = self.outbox.prepare_batch(max_records=100)
        self.assertEqual(first['batch_id'], second['batch_id'])
        self.assertEqual(first['first_seq'], second['first_seq'])
        self.assertEqual(first['last_seq'], second['last_seq'])

    def test_cursor_advances_only_after_verified_remote_hashes(self):
        self.capture.capture_turn(
            self.binding['hcid'], 'conversation-1', 'turn-1', 'hello', 'world'
        )
        manifest = self.outbox.prepare_batch()
        remote = self._remote_receipt(manifest)
        remote[ARTIFACT_JSONL]['sha256'] = '0' * 64
        with self.assertRaises(TranscriptBackupError):
            self.outbox.confirm_upload(manifest['batch_id'], remote)
        self.assertEqual(self.outbox.last_confirmed_seq(), 0)
        self.assertTrue((self.outbox.pending / manifest['batch_id']).exists())

        receipt = self.outbox.confirm_upload(manifest['batch_id'], self._remote_receipt(manifest))
        self.assertEqual(receipt['last_seq'], 2)
        self.assertEqual(self.outbox.last_confirmed_seq(), 2)
        self.assertFalse((self.outbox.pending / manifest['batch_id']).exists())
        self.assertTrue((self.outbox.confirmed / manifest['batch_id']).exists())

    def test_next_batch_contains_only_rows_after_confirmed_cursor(self):
        self.capture.capture_turn(
            self.binding['hcid'], 'conversation-1', 'turn-1', 'one', 'two'
        )
        first = self.outbox.prepare_batch()
        self.outbox.confirm_upload(first['batch_id'], self._remote_receipt(first))

        self.capture.capture_turn(
            self.binding['hcid'], 'conversation-1', 'turn-2', 'three', 'four'
        )
        second = self.outbox.prepare_batch()
        self.assertEqual(second['first_seq'], 3)
        self.assertEqual(second['last_seq'], 4)
        paths = self.outbox.artifact_paths(second['batch_id'])
        rows = [json.loads(line) for line in paths[ARTIFACT_JSONL].read_text(encoding='utf-8').splitlines()]
        self.assertEqual([row['text'] for row in rows], ['three', 'four'])

    def test_pending_human_message_can_be_backed_up_before_assistant_arrives(self):
        exact = 'human message preserved before model response'
        self.capture.begin_turn(
            self.binding['hcid'], 'conversation-1', 'turn-1', exact
        )
        manifest = self.outbox.prepare_batch()
        self.assertEqual(manifest['record_count'], 1)
        paths = self.outbox.artifact_paths(manifest['batch_id'])
        row = json.loads(paths[ARTIFACT_JSONL].read_text(encoding='utf-8').strip())
        self.assertEqual(row['role'], 'HUMAN')
        self.assertEqual(row['text'], exact)

    def test_committed_cursor_reconciles_pending_directory_after_crash_window(self):
        self.capture.capture_turn(
            self.binding['hcid'], 'conversation-1', 'turn-1', 'hello', 'world'
        )
        manifest = self.outbox.prepare_batch()

        # Simulate the only post-commit crash window: remote verification has
        # already happened and the authenticated cursor was committed, but the
        # local pending directory was not moved yet.
        self.outbox._write_cursor(manifest['last_seq'])
        self.assertTrue((self.outbox.pending / manifest['batch_id']).exists())
        self.assertIsNone(self.outbox.prepare_batch())
        self.assertFalse((self.outbox.pending / manifest['batch_id']).exists())
        self.assertTrue((self.outbox.confirmed / manifest['batch_id']).exists())

    def test_corrupt_cursor_fails_closed(self):
        self.capture.capture_turn(
            self.binding['hcid'], 'conversation-1', 'turn-1', 'hello', 'world'
        )
        self.outbox.cursor_path.write_text('{"last_confirmed_seq":999}\n', encoding='utf-8')
        with self.assertRaises(TranscriptBackupError):
            self.outbox.prepare_batch()


if __name__ == '__main__':
    unittest.main()
