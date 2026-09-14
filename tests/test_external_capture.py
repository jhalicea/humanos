import tempfile
import unittest
from pathlib import Path

from external_capture import ExternalTurnCapture, PENDING, EXTERNAL_DELIVERY_ORIGIN
from notebook import Notebook


class ExternalTurnCaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.book = Notebook(self.root / 'vault')
        self.book.recover()
        self.binding = self.book.bind('Jon', 'opening')
        self.capture = ExternalTurnCapture(self.book, 'chatgpt')

    def tearDown(self):
        self.book.close()
        self.tmp.cleanup()

    def test_human_message_is_saved_and_verified_before_assistant(self):
        text = '  exact human text 🧭\nwith a second line  '
        tx = self.capture.begin_turn(self.binding['hcid'], 'conversation-1', 'turn-1', text)
        row = self.book.db.execute(
            'SELECT role,text FROM transcript WHERE tx=? AND ordinal=0', (tx,)
        ).fetchone()
        self.assertEqual((row['role'], row['text']), ('HUMAN', text))
        self.assertEqual(self.book.task(tx)['phase'], PENDING)
        self.assertEqual(self.book.get_transaction(tx)['status'], 'STARTED')
        self.assertTrue(self.book.verify())

    def test_complete_turn_is_exact_checkpointed_and_not_pending_delivery(self):
        human = 'human exact'
        assistant = 'assistant exact\n'
        tx = self.capture.capture_turn(
            self.binding['hcid'], 'conversation-1', 'turn-1', human, assistant
        )
        transcript = [(row['role'], row['text']) for row in self.book.db.execute(
            'SELECT role,text FROM transcript WHERE tx=? ORDER BY ordinal', (tx,)
        )]
        self.assertEqual(transcript, [('HUMAN', human), ('ASSISTANT', assistant)])
        self.assertEqual(self.book.get_transaction(tx)['status'], 'CHECKPOINTED')
        state = self.book.task(tx)
        self.assertEqual(state['phase'], 'COMPLETE')
        self.assertEqual(state['delivery_origin'], EXTERNAL_DELIVERY_ORIGIN)
        self.assertEqual(self.book.delivery_pending(), [])
        self.assertTrue(self.book.verify())

    def test_begin_retry_is_idempotent(self):
        first = self.capture.begin_turn(self.binding['hcid'], 'conversation-1', 'turn-1', 'hello')
        second = self.capture.begin_turn(self.binding['hcid'], 'conversation-1', 'turn-1', 'hello')
        self.assertEqual(first, second)
        self.assertEqual(self.book.message_count(first), 1)
        self.assertEqual(self.book.db.execute(
            "SELECT COUNT(*) FROM events WHERE tx=? AND kind='EXTERNAL_CAPTURE_STARTED'", (first,)
        ).fetchone()[0], 1)

    def test_finish_retry_is_idempotent(self):
        tx = self.capture.begin_turn(self.binding['hcid'], 'conversation-1', 'turn-1', 'hello')
        self.capture.finish_turn(tx, 'world')
        self.capture.finish_turn(tx, 'world')
        self.assertEqual(self.book.message_count(tx), 2)
        self.assertEqual(self.book.db.execute(
            "SELECT COUNT(*) FROM events WHERE tx=? AND kind='EXTERNAL_CAPTURE_COMPLETED'", (tx,)
        ).fetchone()[0], 1)

    def test_conflicting_human_retry_fails_closed(self):
        self.capture.begin_turn(self.binding['hcid'], 'conversation-1', 'turn-1', 'one')
        with self.assertRaises(ValueError):
            self.capture.begin_turn(self.binding['hcid'], 'conversation-1', 'turn-1', 'two')

    def test_conflicting_assistant_retry_fails_closed(self):
        tx = self.capture.begin_turn(self.binding['hcid'], 'conversation-1', 'turn-1', 'hello')
        self.capture.finish_turn(tx, 'first answer')
        with self.assertRaises(ValueError):
            self.capture.finish_turn(tx, 'different answer')

    def test_retry_after_assistant_append_before_state_update(self):
        tx = self.capture.begin_turn(self.binding['hcid'], 'conversation-1', 'turn-1', 'hello')
        self.book.append(tx, 1, 'ASSISTANT', 'already preserved')
        self.capture.finish_turn(tx, 'already preserved')
        self.assertEqual(self.book.get_transaction(tx)['status'], 'CHECKPOINTED')
        self.assertEqual(self.book.message_count(tx), 2)
        self.assertTrue(self.book.verify())

    def test_host_identifiers_are_not_written_to_audit_payload(self):
        conversation_id = 'private-conversation-id'
        turn_id = 'private-turn-id'
        tx = self.capture.begin_turn(self.binding['hcid'], conversation_id, turn_id, 'hello')
        payloads = [row['payload'] for row in self.book.db.execute(
            'SELECT payload FROM events WHERE tx=?', (tx,)
        )]
        combined = '\n'.join(payloads)
        self.assertNotIn(conversation_id, combined)
        self.assertNotIn(turn_id, combined)


if __name__ == '__main__':
    unittest.main()
