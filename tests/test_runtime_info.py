from datetime import datetime, timezone
import unittest
import test_runtime
from runtime_info import execute, recent, intent
from server import HumanOSRuntime
import io


class RuntimeInfoTests(unittest.TestCase):
    setUp = test_runtime.RuntimeTests.setUp
    tearDown = test_runtime.RuntimeTests.tearDown
    agent = test_runtime.RuntimeTests.agent
    turn = test_runtime.RuntimeTests.turn
    def delivered(self, agent, text, tx):
        result = self.turn(agent, text, tx)
        runtime = object.__new__(HumanOSRuntime)
        runtime.book = self.book
        runtime.deliver(tx, result, io.StringIO())
        return result
    def test_clock_captured_without_model(self):
        agent = self.agent()
        result = self.turn(agent, 'what time it is?')
        self.assertIn('local date and time', result)
        self.assertEqual(agent.model.calls, [])
        self.assertEqual(self.book.get_transaction('tx-1')['status'], 'CHECKPOINTED')
        self.assertEqual(self.book.db.execute("SELECT text FROM transcript WHERE role='ASSISTANT'").fetchone()[0], result)

    def test_fixed_clock(self):
        self.book.start(self.binding['hcid'], 't', '/time')
        result = execute(self.book, self.binding, 't', 'current_time', datetime(2026, 9, 7, tzinfo=timezone.utc))
        self.assertIn('2026-09-07T00:00:00+00:00', result)

    def test_notebook_is_not_empty(self):
        self.delivered(self.agent({'final': 'Hello Jon'}), 'hi', 'one')
        result = self.turn(self.agent(), 'is this conversation in the notebook?', 'two')
        self.assertIn('2 transactions and 3 saved transcript messages', result)
        self.assertIn('Hello Jon', result)
        self.book.verify()

    def test_history_is_session_scoped_and_bounded(self):
        self.delivered(self.agent({'final': 'visible answer'}), 'remember apple', 'one')
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

    def test_self_inspection_uses_runtime_not_model_refusal(self):
        agent = self.agent()
        result = self.turn(agent, 'what model are you?', 'model')
        self.assertIn('Configured local model: test-model.', result)
        self.assertIn('Selected workspace folder:', result)
        self.assertIn('I’m Mirror', result)
        self.assertEqual(agent.model.calls, [])

    def test_policy_question_uses_capabilities_not_model_refusal(self):
        agent = self.agent()
        result = self.turn(agent, 'can you tell me what is the HumanOS policy?', 'policy')
        self.assertIn('File access stays inside the folder you select.', result)
        self.assertIn('Use /files', result)
        self.assertEqual(agent.model.calls, [])

    def test_runtime_check_typo_reads_fixture_directly(self):
        (self.workspace / 'runtime-check.txt').write_text(
            'Verification phrase: continuity belongs to Jon.\nVerification code: HOS-LOCAL-62947.\n')
        agent = self.agent()
        result = self.turn(agent, 'can you read the runtiem-check.txt and tell me what inside?', 'check')
        self.assertIn('continuity belongs to Jon', result)
        self.assertIn('HOS-LOCAL-62947', result)
        self.assertEqual(agent.model.calls, [])

    def test_debug_trace_preserves_visible_reasoning_provenance(self):
        self.turn(self.agent({'final': 'answered'}), 'hello', 'first')
        result = self.turn(self.agent(), '/debug-trace first', 'trace')
        self.assertIn('Provenance summary for first', result)
        self.assertIn('Hidden chain-of-thought captured: no.', result)
        self.assertIn('Summary trace avoids replaying prompts', result)
        self.assertNotIn('Visible model message packet:', result)
        self.assertIn('REASONING_PROVENANCE', result)
        self.assertIn('Answered by model', result)

    def test_full_debug_trace_requires_explicit_flag(self):
        self.turn(self.agent({'final': 'answered'}), 'hello', 'first')
        result = self.turn(self.agent(), '/debug-trace first --full', 'trace')
        self.assertIn('Full debug trace for first', result)
        self.assertIn('Visible model message packet:', result)
        self.assertIn('MODEL_RESPONSE', result)
        self.assertIn('REASONING_PROVENANCE', result)

    def test_file_request_not_intercepted(self):
        self.assertIsNone(intent('Read notebook.md and tell me what it says'))

    def test_ungrounded_file_final_requires_read(self):
        (self.workspace / 'note.txt').write_text('actual evidence')
        agent = self.agent({'final': 'invented'}, {'tool': {'name': 'read_file', 'path': 'note.txt'}}, {'final': 'actual evidence'})
        self.assertEqual(self.turn(agent, 'read note.txt'), 'actual evidence')
        self.assertEqual(len(agent.model.calls), 3)
