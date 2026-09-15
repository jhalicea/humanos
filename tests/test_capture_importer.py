from pathlib import Path
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

    def test_unavailable_local_storage_stays_staged_and_retries(self):
        self.relay.append(self.event('human', 'durable after storage recovery'))
        self.importer.stage(self.relay.after)
        original = self.importer._import_event
        self.importer._import_event = lambda event: (_ for _ in ()).throw(OSError('storage unavailable'))
        with self.assertRaisesRegex(OSError, 'storage unavailable'):
            self.importer.drain()
        self.assertEqual(self.importer.status(), {
            'staged_remote_seq': 1, 'acknowledged_seq': 0,
            'staged': 1, 'imported': 0, 'errors': 1,
        })

        self.importer._import_event = original
        result = self.importer.drain()
        self.assertEqual(result['imported'], 1)
        self.assertEqual(result['pending'], 0)
        self.assertEqual(result['errors'], 0)
        self.assertEqual([(row['role'], row['text']) for row in self.book.db.execute(
            'SELECT role,text FROM transcript ORDER BY seq'
        )], [('HUMAN', 'durable after storage recovery')])

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
