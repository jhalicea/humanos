import tempfile
import unittest
from pathlib import Path

from conversation_capture import UniversalConversationCapture, PENDING
from notebook import Notebook


class UniversalConversationCaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.book = Notebook(self.root / 'vault')
        self.book.recover()
        self.binding = self.book.bind('Jon', 'opening')

    def tearDown(self):
        self.book.close()
        self.tmp.cleanup()

    def test_exact_turn_round_trip(self):
        capture = UniversalConversationCapture(self.book, 'chatgpt')
        human = '  exact human text 🧭\nline two  '
        assistant = ' exact assistant text\n'
        tx = capture.capture_turn(
            self.binding['hcid'], 'conversation-1', 'turn-1', human, assistant
        )
        rows = list(self.book.db.execute(
            'SELECT role,text FROM transcript WHERE tx=? ORDER BY ordinal', (tx,)
        ))
        self.assertEqual([(row['role'], row['text']) for row in rows], [
            ('HUMAN', human), ('ASSISTANT', assistant)
        ])
        self.assertEqual(self.book.get_transaction(tx)['status'], 'CHECKPOINTED')
        self.assertTrue(self.book.verify())

    def test_human_half_turn_remains_pending(self):
        capture = UniversalConversationCapture(self.book, 'chatgpt')
        tx = capture.begin_turn(self.binding['hcid'], 'conversation-1', 'turn-1', 'hello')
        self.assertEqual(self.book.task(tx)['phase'], PENDING)
        self.assertEqual(self.book.message_count(tx), 1)
        self.assertTrue(self.book.verify())

    def test_source_isolation(self):
        chatgpt = UniversalConversationCapture(self.book, 'chatgpt')
        claude = UniversalConversationCapture(self.book, 'claude')
        chatgpt_tx = chatgpt.begin_turn(
            self.binding['hcid'], 'same-conversation', 'same-turn', 'from ChatGPT'
        )
        claude_tx = claude.begin_turn(
            self.binding['hcid'], 'same-conversation', 'same-turn', 'from Claude'
        )
        self.assertNotEqual(chatgpt_tx, claude_tx)
        self.assertEqual(self.book.message_count(chatgpt_tx), 1)
        self.assertEqual(self.book.message_count(claude_tx), 1)

    def test_provider_identifiers_not_present_in_audit_payload(self):
        capture = UniversalConversationCapture(self.book, 'chatgpt')
        conversation_id = 'private-provider-conversation-id'
        turn_id = 'private-provider-turn-id'
        tx = capture.begin_turn(self.binding['hcid'], conversation_id, turn_id, 'hello')
        payloads = [row['payload'] for row in self.book.db.execute(
            'SELECT payload FROM events WHERE tx=?', (tx,)
        )]
        joined = '\n'.join(payloads)
        self.assertNotIn(conversation_id, joined)
        self.assertNotIn(turn_id, joined)


if __name__ == '__main__':
    unittest.main()
