from pathlib import Path
import errno
import sqlite3
import tempfile
import unittest

from capture_fabric import CaptureEvent, SQLiteRelay
from capture_importer import CaptureImporter
from notebook import Notebook


class CaptureImporterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.book = Notebook(self.root / 'vault')
        self.book.recover()
        self.relay = SQLiteRelay(self.root / 'remote' / 'relay.sqlite3')
        self.importer = CaptureImporter(self.book, self.root / 'import-state')

    def tearDown(self):
        self.importer.close()
        self.relay.close()
        self.book.close()
        self.tmp.cleanup()

    def event(self, role, text, event_type=None, turn='turn-1', variant='primary'):
        event_type = event_type or ('human_message' if role == 'human' else 'assistant_message')
        return CaptureEvent(
            source='chatgpt',
            conversation_id='conversation-1',
            turn_id=turn,
            event_type=event_type,
            role=role,
            text=text,
            idempotency_key=f'chatgpt/conversation-1/{turn}/{role}/{variant}/{event_type}',
            variant_id=variant,
        )

    def transcript(self):
        return [(row['tx'], row['role'], row['text']) for row in self.book.db.execute(
            'SELECT tx,role,text FROM transcript ORDER BY seq'
        )]

    def test_remote_turn_imports_exactly_into_life_notebook(self):
        human = '  human exact 🧭\nline two  '
        assistant = ' assistant exact\n'
        self.relay.append(self.event('human', human))
        self.relay.append(self.event('assistant', assistant))

        self.assertEqual(self.importer.stage(self.relay.after), 2)
        result = self.importer.drain()

        rows = self.transcript()
        self.assertEqual([(role, text) for _, role, text in rows], [
            ('HUMAN', human), ('ASSISTANT', assistant)
        ])
        self.assertEqual(rows[0][0], rows[1][0])
        self.assertEqual(result['acknowledged_seq'], 2)
        self.assertEqual(result['pending'], 0)
        self.assertTrue(self.book.verify())

    def test_out_of_order_assistant_is_staged_until_human_arrives(self):
        # Arrival order can differ from logical turn order. The local staging
        # inbox keeps the assistant safely while a later human event establishes
        # the transaction identity.
        self.relay.append(self.event('assistant', 'answer'))
        self.relay.append(self.event('human', 'question'))

        self.importer.stage(self.relay.after)
        result = self.importer.drain()

        self.assertEqual([(role, text) for _, role, text in self.transcript()], [
            ('HUMAN', 'question'), ('ASSISTANT', 'answer')
        ])
        self.assertEqual(result['acknowledged_seq'], 2)
        self.assertEqual(result['pending'], 0)

    def test_regeneration_becomes_new_immutable_branch(self):
        self.relay.append(self.event('human', 'same question'))
        self.relay.append(self.event('assistant', 'first answer'))
        self.relay.append(self.event(
            'assistant', 'second answer',
            event_type='assistant_regeneration', variant='regen-1'))

        self.importer.stage(self.relay.after)
        result = self.importer.drain()
        rows = self.transcript()

        self.assertEqual([(role, text) for _, role, text in rows], [
            ('HUMAN', 'same question'),
            ('ASSISTANT', 'first answer'),
            ('HUMAN', 'same question'),
            ('ASSISTANT', 'second answer'),
        ])
        self.assertNotEqual(rows[0][0], rows[2][0])
        self.assertEqual(result['acknowledged_seq'], 3)

    def test_restart_does_not_duplicate_remote_events(self):
        self.relay.append(self.event('human', 'hello'))
        self.relay.append(self.event('assistant', 'hi'))
        self.importer.stage(self.relay.after)
        self.importer.drain()
        before = self.transcript()

        self.importer.close()
        self.importer = CaptureImporter(self.book, self.root / 'import-state')
        self.assertEqual(self.importer.stage(self.relay.after), 0)
        result = self.importer.drain()

        self.assertEqual(self.transcript(), before)
        self.assertEqual(result['imported'], 0)
        self.assertEqual(result['acknowledged_seq'], 2)

    def test_locked_notebook_storage_stays_staged_and_retries(self):
        self.relay.append(self.event('human', 'durable after storage recovery'))
        self.importer.stage(self.relay.after)
        self.book.db.execute('PRAGMA busy_timeout=1')
        blocker = sqlite3.connect(str(self.book.root / 'notebook.sqlite3'), timeout=0)
        blocker.execute('BEGIN EXCLUSIVE')
        result = self.importer.drain()
        blocker.rollback()
        blocker.close()
        self.book.db.execute('PRAGMA busy_timeout=5000')
        self.assertEqual(result['pending'], 1)
        self.assertEqual(result['errors'], 1)
        self.assertEqual(result['retryable_errors'], 1)
        self.assertEqual(result['permanent_errors'], 0)
        self.assertEqual(self.importer.status(), {
            'staged_remote_seq': 1, 'acknowledged_seq': 0,
            'staged': 1, 'imported': 0, 'errors': 1,
            'retryable_errors': 1, 'permanent_errors': 0, 'failure_history': 1,
        })

        result = self.importer.drain()
        self.assertEqual(result['imported'], 1)
        self.assertEqual(result['pending'], 0)
        self.assertEqual(result['errors'], 0)
        self.assertEqual(result['failure_history'], 1)
        self.assertEqual([(row['role'], row['text']) for row in self.book.db.execute(
            'SELECT role,text FROM transcript ORDER BY seq'
        )], [('HUMAN', 'durable after storage recovery')])

    def test_injected_disk_full_stays_staged_and_retries(self):
        """An ENOSPC reported by Notebook leaves the verified inbox evidence retryable.

        This is fault injection at the Notebook boundary, not a claim that the
        host filesystem has been filled in this test environment.
        """
        self.relay.append(self.event('human', 'durable after injected disk full'))
        self.importer.stage(self.relay.after)
        original = self.book.start

        def disk_full(*args, **kwargs):
            raise OSError(errno.ENOSPC, 'injected disk full')

        self.book.start = disk_full
        result = self.importer.drain()
        self.book.start = original
        self.assertEqual((result['pending'], result['retryable_errors'], result['permanent_errors']),
                         (1, 1, 0))
        self.assertEqual(self.importer.drain()['acknowledged_seq'], 1)
        self.assertEqual([(role, text) for _, role, text in self.transcript()],
                         [('HUMAN', 'durable after injected disk full')])

    def test_injected_permission_loss_is_visible_until_owner_requeues(self):
        """Permission loss is terminal, so the importer never retries it silently."""
        self.relay.append(self.event('human', 'durable after permission repair'))
        self.importer.stage(self.relay.after)
        original = self.book.start

        def permission_denied(*args, **kwargs):
            raise PermissionError(errno.EACCES, 'injected permission denied')

        self.book.start = permission_denied
        result = self.importer.drain()
        self.book.start = original
        self.assertEqual((result['pending'], result['retryable_errors'], result['permanent_errors']),
                         (0, 0, 1))
        self.assertEqual(self.importer.status()['acknowledged_seq'], 0)
        self.importer.requeue_error(1)
        self.assertEqual(self.importer.drain()['acknowledged_seq'], 1)
        self.assertEqual([(role, text) for _, role, text in self.transcript()],
                         [('HUMAN', 'durable after permission repair')])

    def test_permanent_error_does_not_block_later_capture_and_can_be_requeued(self):
        self.relay.append(self.event('human', 'bad evidence', turn='turn-bad'))
        self.relay.append(self.event('human', 'good evidence', turn='turn-good'))
        self.importer.stage(self.relay.after)
        original = self.importer._import_event

        def import_with_permanent_failure(event):
            if event.turn_id == 'turn-bad':
                raise ValueError('preserved evidence conflict')
            return original(event)

        self.importer._import_event = import_with_permanent_failure
        result = self.importer.drain()
        self.assertEqual(result['imported'], 1)
        self.assertEqual(result['acknowledged_seq'], 0)
        self.assertEqual(result['permanent_errors'], 1)
        self.assertEqual(self.importer.db.execute(
            'SELECT status FROM inbox WHERE remote_seq=1').fetchone()[0], 'ERROR')
        self.assertEqual([(role, text) for _, role, text in self.transcript()], [
            ('HUMAN', 'good evidence')])

        self.importer._import_event = original
        self.importer.requeue_error(1)
        self.assertEqual(self.importer.status()['errors'], 0)
        history = list(self.importer.db.execute(
            'SELECT classification,message FROM failure_history WHERE remote_seq=1 ORDER BY id'))
        self.assertEqual([tuple(row) for row in history], [
            ('TERMINAL', 'preserved evidence conflict'),
            ('OWNER_REQUEUE', 'preserved evidence conflict'),
        ])
        with self.assertRaises(sqlite3.IntegrityError):
            self.importer.db.execute('UPDATE failure_history SET message="changed" WHERE remote_seq=1')
        with self.assertRaises(sqlite3.IntegrityError):
            self.importer.db.execute('DELETE FROM failure_history WHERE remote_seq=1')
        result = self.importer.drain()
        self.assertEqual(result['acknowledged_seq'], 2)
        self.assertEqual(result['errors'], 0)
        self.assertEqual([(role, text) for _, role, text in self.transcript()], [
            ('HUMAN', 'good evidence'), ('HUMAN', 'bad evidence')])

    def test_legacy_error_is_visible_and_requires_explicit_requeue(self):
        self.relay.append(self.event('human', 'legacy failed record'))
        self.importer.stage(self.relay.after)
        with self.importer.db:
            self.importer.db.execute(
                "UPDATE inbox SET status='ERROR', error='legacy storage failure' WHERE remote_seq=1"
            )
        self.assertEqual(self.importer.status()['permanent_errors'], 1)
        self.assertEqual(self.importer.drain()['imported'], 0)
        self.importer.requeue_error(1)
        self.assertEqual(self.importer.db.execute(
            'SELECT message FROM failure_history WHERE classification="OWNER_REQUEUE"').fetchone()[0],
            'legacy storage failure')
        self.assertEqual(self.importer.drain()['acknowledged_seq'], 1)

    def test_retry_policy_excludes_permission_and_schema_errors(self):
        self.assertFalse(self.importer._retryable(PermissionError(errno.EACCES, 'access denied')))
        self.assertFalse(self.importer._retryable(sqlite3.OperationalError('no such table: transcript')))
        self.assertTrue(self.importer._retryable(sqlite3.OperationalError('database is locked')))
        self.assertTrue(self.importer._retryable(OSError(errno.ENOSPC, 'disk full')))

    def test_tampered_remote_digest_fails_before_local_staging(self):
        receipt = self.relay.append(self.event('human', 'hello'))
        event = self.event('human', 'hello')
        bad = type(receipt)(receipt.seq, receipt.event_id, '0' * 64, receipt.received_at)

        with self.assertRaisesRegex(RuntimeError, 'digest mismatch'):
            self.importer.stage(lambda seq, limit: [(bad, event)])
        self.assertEqual(self.importer.status()['staged'], 0)
        self.assertEqual(self.transcript(), [])


if __name__ == '__main__':
    unittest.main()
