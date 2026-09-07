from datetime import datetime, timezone
import unittest
import test_runtime
from runtime_info import answer, recent, intent


class RuntimeInfoTests(unittest.TestCase):
    setUp = test_runtime.RuntimeTests.setUp
    tearDown = test_runtime.RuntimeTests.tearDown
    agent = test_runtime.RuntimeTests.agent
    turn = test_runtime.RuntimeTests.turn
    def test_clock_captured_without_model(self):
        agent = self.agent()
        result = self.turn(agent, 'what time it is?')
        self.assertIn('local date and time', result)
        self.assertEqual(agent.model.calls, [])
        self.assertEqual(self.book.get_transaction('tx-1')['status'], 'CHECKPOINTED')
        self.assertEqual(self.book.db.execute("SELECT text FROM transcript WHERE role='ASSISTANT'").fetchone()[0], result)

    def test_fixed_clock(self):
        self.book.start(self.binding['hcid'], 't', '/time')
        result = answer(self.book, self.binding, 't', '/time', [], datetime(2026, 9, 7, tzinfo=timezone.utc))
        self.assertIn('2026-09-07T00:00:00+00:00', result)

    def test_notebook_is_not_empty(self):
        self.turn(self.agent({'final': 'Hello Jon'}), 'hi', 'one')
        result = self.turn(self.agent(), 'is this conversation in the notebook?', 'two')
        self.assertIn('2 transactions and 3 saved transcript messages', result)
        self.assertIn('Hello Jon', result)
        self.book.verify()

    def test_history_is_session_scoped_and_bounded(self):
        self.turn(self.agent({'final': 'visible answer'}), 'remember apple', 'one')
        other = self.book.bind('Jon', 'different')
        self.assertEqual(recent(self.book, other['hcid'], 'x'), [])
        self.assertEqual(recent(self.book, self.binding['hcid'], 'x', budget=1), [])
        agent = self.agent({'final': 'apple'})
        self.turn(agent, 'what word?', 'two')
        self.assertIn({'role': 'user', 'content': 'remember apple'}, agent.model.calls[0])

    def test_followup_clock(self):
        self.turn(self.agent(), 'what time is it?', 'one')
        self.assertIn('local date and time', self.turn(self.agent(), 'do it', 'two'))

    def test_capabilities_truthful(self):
        result = self.turn(self.agent(), 'can you search the internet?')
        self.assertIn('not connected', result)

    def test_file_request_not_intercepted(self):
        self.assertIsNone(intent('Read notebook.md and tell me what it says'))

    def test_ungrounded_file_final_requires_read(self):
        (self.workspace / 'note.txt').write_text('actual evidence')
        agent = self.agent({'final': 'invented'}, {'tool': {'name': 'read_file', 'path': 'note.txt'}}, {'final': 'actual evidence'})
        self.assertEqual(self.turn(agent, 'read note.txt'), 'actual evidence')
        self.assertEqual(len(agent.model.calls), 3)
