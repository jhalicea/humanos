import json
import io
import unittest
from unittest.mock import patch
import test_runtime
from engine import Agent, Tools
from capabilities import validate_request, describe
from permissions import task_scope
from runtime_info import recent
from server import HumanOSRuntime


class PermissionTests(unittest.TestCase):
    setUp = test_runtime.RuntimeTests.setUp
    tearDown = test_runtime.RuntimeTests.tearDown
    agent = test_runtime.RuntimeTests.agent
    turn = test_runtime.RuntimeTests.turn

    def test_resume_cannot_expand_scope_even_with_allow_callback(self):
        (self.workspace / 'allowed.txt').write_text('allowed')
        (self.workspace / 'secret.txt').write_text('private')
        with self.assertRaises(ConnectionError):
            self.turn(self.agent(ConnectionError('interrupted')), 'read allowed.txt')
        before = self.book.task('tx-1')['permissions']
        resumed = self.agent({'tool': {'name': 'read_file', 'path': 'secret.txt'}},
            {'tool': {'name': 'read_file', 'path': 'allowed.txt'}}, {'final': 'allowed'}, authorize=lambda r: True)
        self.assertEqual(resumed.run('tx-1'), 'allowed')
        observations = [json.loads(r[0]) for r in self.book.db.execute("SELECT payload FROM events WHERE kind='TOOL_RESULT'")]
        self.assertEqual(observations[0]['authorization'], 'DENIED')
        self.assertNotIn('private', json.dumps(observations))
        self.assertEqual(before, self.book.task('tx-1')['permissions'])

    def test_request_substring_is_not_permission(self):
        state = task_scope({'tx': 't', 'hcid': 'h', 'input': 'read secret.txt.bak'}, self.workspace)
        self.assertNotIn('secret.txt', state['read_paths'])

    def test_negated_filename_mention_is_not_permission(self):
        for text in ('read public.txt but do not read secret.txt', "don't read secret.txt", 'list files except secrets'):
            state = task_scope({'tx': 't', 'hcid': 'h', 'input': text}, self.workspace)
            self.assertEqual(state['read_paths'], [])
            self.assertEqual(state['list_paths'], [])

    def test_nested_requested_file_satisfies_grounding(self):
        (self.workspace / 'folder').mkdir()
        (self.workspace / 'folder' / 'note.txt').write_text('nested evidence')
        agent = self.agent({'tool': {'name': 'read_file', 'path': 'folder/note.txt'}}, {'final': 'nested evidence'})
        self.assertEqual(self.turn(agent, 'read folder/note.txt'), 'nested evidence')

    def test_authority_state_and_event_are_atomic(self):
        import sqlite3
        self.book.start(self.binding['hcid'], 't', 'read note.txt')
        before = {'phase': 'TOOL', 'denials': []}
        self.book.save_task('t', before)
        self.book.db.execute("CREATE TRIGGER reject_authorization BEFORE INSERT ON events WHEN NEW.kind='AUTHORIZATION' BEGIN SELECT RAISE(ABORT, 'injected'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.book.save_task_event('t', {'phase': 'TOOL', 'denials': ['saved decision']}, 'AUTHORIZATION', {'allowed': False})
        self.assertEqual(self.book.task('t'), before)
        self.assertEqual(self.book.db.execute("SELECT COUNT(*) FROM events WHERE kind='AUTHORIZATION'").fetchone()[0], 0)

    def test_saved_scope_tamper_fails_closed(self):
        with self.assertRaises(ConnectionError):
            self.turn(self.agent(ConnectionError()), 'read allowed.txt')
        state = self.book.task('tx-1')
        state['permissions']['read_paths'].append('secret.txt')
        self.book.save_task('tx-1', state)
        with self.assertRaisesRegex(PermissionError, 'scope differs'):
            self.agent().run('tx-1')

    def test_legacy_unfinished_task_needs_reconciliation(self):
        with self.assertRaises(ConnectionError):
            self.turn(self.agent(ConnectionError()), 'read allowed.txt')
        state = self.book.task('tx-1')
        del state['permissions']
        self.book.save_task('tx-1', state)
        with self.assertRaisesRegex(PermissionError, 'no saved permission'):
            self.agent().run('tx-1')

    def test_read_denial_survives_callback_loss(self):
        with self.assertRaises(ConnectionError):
            self.turn(self.agent({'tool': {'name': 'read_file', 'path': 'allowed.txt'}},
                ConnectionError(), authorize=lambda r: False), 'read allowed.txt')
        (self.workspace / 'allowed.txt').write_text('private after denial')
        resumed = self.agent({'tool': {'name': 'read_file', 'path': 'allowed.txt'}}, {'final': 'Denied'})
        resumed.run('tx-1')
        self.assertNotIn('private after denial', json.dumps(resumed.model.calls))

    def test_registry_rejects_unknown_unavailable_and_cross_session_args(self):
        for request in ({'name': 'shell'}, {'name': 'internet_search'},
                        {'name': 'read_notebook', 'hcid': 'another'}, {'name': 'read_file', 'path': 3},
                        {'name': 'create_file', 'path': 'x'}):
            with self.subTest(request=request), self.assertRaises(PermissionError):
                validate_request(request)
        self.assertEqual(validate_request({'name': 'list_files'})['path'], '.')

    def test_model_and_direct_runtime_queries_share_executor(self):
        model = self.agent({'tool': {'name': 'current_time'}}, {'final': 'Time read'})
        self.turn(model, 'Please consult the clock', 'one')
        self.turn(self.agent(), '/time', 'two')
        for tx in ('one', 'two'):
            events = [r[0] for r in self.book.db.execute('SELECT kind FROM events WHERE tx=?', (tx,))]
            self.assertIn('TOOL_REQUEST', events)
            self.assertIn('AUTHORIZATION', events)
            self.assertIn('TOOL_RESULT', events)

    def test_registry_rejection_cannot_execute_handler(self):
        result = self.tools.execute({'name': 'read_notebook', 'hcid': 'other'}, lambda r: True,
            runtime=lambda name: self.fail('handler must not execute'))
        self.assertFalse(result['ok'])

    def test_history_omits_undelivered_assistant_keeps_human(self):
        final = self.turn(self.agent({'final': 'unseen reply'}), 'visible human input')
        history = recent(self.book, self.binding['hcid'], 'next')
        self.assertEqual([r['text'] for r in history], ['visible human input'])
        runtime = object.__new__(HumanOSRuntime)
        runtime.book = self.book
        runtime.deliver('tx-1', final, io.StringIO())
        self.assertIn('unseen reply', [r['text'] for r in recent(self.book, self.binding['hcid'], 'next')])

    def test_short_write_and_flush_failure_are_uncertain(self):
        final = self.turn(self.agent({'final': 'exact'}))
        runtime = object.__new__(HumanOSRuntime)
        runtime.book = self.book
        class Short:
            def write(self, text): return 1
        class FlushFails:
            def write(self, text): return len(text)
            def flush(self): raise OSError('lost output')
        for stream in (Short(), FlushFails()):
            with self.assertRaises(OSError):
                runtime.deliver('tx-1', final, stream)
            self.assertEqual(self.book.task('tx-1')['delivery'], 'OUTPUT_UNCERTAIN')
