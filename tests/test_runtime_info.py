from datetime import datetime, timezone
import unittest
import test_runtime
from runtime_info import execute, recent, intent, request_for
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

    def test_file_request_not_intercepted(self):
        self.assertIsNone(intent('Read notebook.md and tell me what it says'))

    def test_ungrounded_file_final_requires_read(self):
        (self.workspace / 'note.txt').write_text('actual evidence')
        agent = self.agent({'final': 'invented'}, {'tool': {'name': 'read_file', 'path': 'note.txt'}}, {'final': 'actual evidence'})
        self.assertEqual(self.turn(agent, 'read note.txt'), 'actual evidence')
        self.assertEqual(len(agent.model.calls), 3)

    def test_common_workspace_browse_phrases_are_direct_requests(self):
        expected = {'name': 'list_files', 'path': '.'}
        for text in ('list files', 'list folders', 'list them', 'show workspace',
                     'show me the files', "what's in the workspace"):
            with self.subTest(text=text):
                self.assertEqual(request_for(text, []), expected)
        self.assertIsNone(request_for('do not list files', []))
        self.assertIsNone(request_for('list files in private', []))

    def test_natural_workspace_browse_is_grounded_without_model(self):
        (self.workspace / 'runtime-check.txt').write_text('proof')
        (self.workspace / 'Archive').mkdir()
        agent = self.agent({'final': 'invented stale listing'})
        result = self.turn(agent, 'show workspace', 'browse')
        self.assertIn('Workspace contains 2 visible item(s):', result)
        self.assertIn('runtime-check.txt', result)
        self.assertIn('Archive', result)
        self.assertNotIn('invented stale listing', result)
        self.assertEqual(agent.model.calls, [])

    def test_natural_listing_creates_verified_reference_frame(self):
        (self.workspace / 'runtime-check.txt').write_text('proof')
        agent = self.agent()
        self.turn(agent, 'list files', 'browse')
        frame = self.book.task('browse').get('reference_frame')
        self.assertEqual(frame['kind'], 'file')
        self.assertEqual(frame['paths'], ['runtime-check.txt'])
        followup = self.turn(self.agent(), 'read that file', 'read')
        self.assertIn('File: runtime-check.txt', followup)
        self.assertIn('proof', followup)
