"""Exercise HumanOS file workflows across policy, tools, Notebook and CLI.

All files, plans and transcripts belong to isolated temporary test folders.
The simulated model makes authority-expansion attempts deliberately visible.
"""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import engine
import server
from engine import Agent, Tools
from notebook import Notebook, digest, encode
from permissions import task_scope
from server import HumanOSRuntime
from source_reader import SourceReader


class ScriptedModel:
    name = 'integration-test-model'

    def __init__(self, *responses):
        self.responses = iter(responses)
        self.calls = []

    def invoke(self, messages, timeout):
        self.calls.append(json.loads(json.dumps(messages)))
        response = next(self.responses)
        if isinstance(response, BaseException):
            raise response
        return response


class FileIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.workspace = self.root / 'selected-folder'
        self.book = Notebook(self.root / 'vault')
        self.book.recover()
        self.binding = self.book.bind('Jon', 'integration test')
        self.tools = Tools(self.workspace)
        self.core = self.root / 'core'
        self.core.mkdir()
        self.sources = self.root / 'runtime-source'
        self.sources.mkdir()
        (self.sources / 'server.py').write_text('print("HumanOS source verification")\n', encoding='utf-8')
        self.tools.source = SourceReader(self.sources)

    def tearDown(self):
        self.book.close()
        self.tmp.cleanup()

    def agent(self, *responses, **kwargs):
        kwargs.setdefault('finalize_on_error', True)
        return Agent(self.book, ScriptedModel(*responses), self.tools, self.core, **kwargs)

    def turn(self, agent, text, tx='turn'):
        return agent.run(tx, self.binding['hcid'], text)

    def events(self, tx, kind):
        return [json.loads(row['payload']) for row in self.book.db.execute(
            'SELECT payload FROM events WHERE tx=? AND kind=? ORDER BY seq', (tx, kind))]

    def assert_checkpoint(self, tx, human, final):
        rows = self.book.db.execute('SELECT role,text FROM transcript WHERE tx=? ORDER BY ordinal', (tx,)).fetchall()
        self.assertEqual((rows[0]['role'], rows[0]['text']), ('HUMAN', human))
        self.assertEqual((rows[-1]['role'], rows[-1]['text']), ('ASSISTANT', final))
        self.assertEqual(self.book.get_transaction(tx)['status'], 'CHECKPOINTED')
        self.assertTrue(self.book.verify())

    def test_screenshot_source_request_reads_source_outside_workspace(self):
        human = 'that doeesnt make sense how are you a file interface but can read a file read server.py'
        (self.workspace / 'server.py').write_text('unrelated workspace file', encoding='utf-8')
        agent = self.agent()
        final = self.turn(agent, human)
        self.assertIn('HumanOS source verification', final)
        self.assertNotIn('unrelated workspace file', final)
        self.assertEqual(agent.model.calls, [])
        self.assertEqual(self.events('turn', 'TOOL_REQUEST')[0]['name'], 'read_source')
        self.assert_checkpoint('turn', human, final)

    def test_source_reader_never_exposes_runtime_configuration(self):
        (self.sources / 'config.json').write_text('{"secret":"DO_NOT_EXPOSE"}', encoding='utf-8')
        human = '/source config.json'
        final = self.turn(self.agent(), human)
        self.assertNotIn('DO_NOT_EXPOSE', final)
        self.assertFalse(self.events('turn', 'TOOL_RESULT')[0]['ok'])
        self.assertEqual(self.book.task('turn')['outcome'], 'FAILED')
        self.assert_checkpoint('turn', human, final)

    def test_model_cannot_read_source_after_a_greeting(self):
        agent = self.agent({'tool': {'name': 'read_source', 'path': 'server.py'}}, {'final': 'Hello, Jon.'},
                           authorize=lambda request: True)
        self.assertEqual(self.turn(agent, 'hi'), 'Hello, Jon.')
        self.assertFalse(self.events('turn', 'AUTHORIZATION')[0]['allowed'])
        self.assertNotIn('HumanOS source verification', json.dumps(agent.model.calls))

    def test_utf8_file_pages_reconstruct_exact_content_and_full_hash(self):
        text = 'a' * 16383 + '🧭é漢字\r\n' * 2000
        (self.workspace / 'my note.txt').write_bytes(text.encode('utf-8'))
        offset, pages = 0, []
        while offset is not None:
            result = self.tools.execute({'name': 'read_file', 'path': 'my note.txt', 'offset': offset}, lambda request: True)
            self.assertTrue(result['ok'], result['stderr'])
            self.assertEqual(result['sha256'], digest(text))
            self.assertLessEqual(len(result['stdout'].encode('utf-8')), 128 * 1024)
            pages.append(result['stdout'])
            next_offset = result['next_offset']
            if next_offset is not None:
                self.assertGreater(next_offset, offset)
            offset = next_offset
        self.assertEqual(''.join(pages), text)
        split = self.tools.execute({'name': 'read_file', 'path': 'my note.txt', 'offset': 128 * 1024}, lambda request: True)
        self.assertFalse(split['ok'])

    def test_quoted_read_command_captures_exact_input_and_page(self):
        (self.workspace / 'my note.txt').write_text('exact quoted filename evidence', encoding='utf-8')
        human = '  /read "my note.txt" 0  '
        agent = self.agent()
        final = self.turn(agent, human)
        self.assertIn('exact quoted filename evidence', final)
        self.assertEqual(agent.model.calls, [])
        self.assert_checkpoint('turn', human, final)

    def test_binary_content_is_not_misrepresented_as_text(self):
        (self.workspace / 'picture.png').write_bytes(b'\x89PNG\r\n\xff')
        human = '/read picture.png'
        final = self.turn(self.agent(), human)
        self.assertIn('UTF-8', final)
        self.assertFalse(self.events('turn', 'TOOL_RESULT')[0]['ok'])
        self.assertEqual(self.book.task('turn')['outcome'], 'FAILED')
        self.assert_checkpoint('turn', human, final)

    def test_missing_read_closes_failure_and_next_turn_works(self):
        agent = self.agent({'final': 'We can continue.'})
        human = '/read missing.txt'
        final = self.turn(agent, human)
        self.assertIn('missing.txt', final)
        state = self.book.task('turn')
        self.assertEqual(state['phase'], 'COMPLETE')
        self.assertEqual(state['outcome'], 'FAILED')
        self.assertGreater(self.book.db.execute("SELECT COUNT(*) FROM recovery WHERE tx='turn' AND scope='TASK' AND closed=0").fetchone()[0], 0)
        self.assert_checkpoint('turn', human, final)
        self.assertEqual(self.turn(agent, 'hello again', 'next'), 'We can continue.')

    def test_iteration_exhaustion_closes_failed_turn_without_losing_original_input(self):
        agent = self.agent({'wrong': 'model response'}, max_steps=1)
        human = '  Help me work through this.\r\n'
        final = self.turn(agent, human)
        self.assertIn('task limit', final)
        state = self.book.task('turn')
        self.assertEqual(state['outcome'], 'FAILED')
        self.assertEqual(state['failure_snapshot']['steps'], 1)
        self.assertEqual(len(agent.model.calls), 1)
        self.assert_checkpoint('turn', human, final)

    def test_unavailable_model_reports_error_and_keeps_chat_usable(self):
        agent = self.agent(ConnectionError('local backend unavailable'), {'final': 'Recovered connection.'})
        final = self.turn(agent, 'hello')
        self.assertIn('local backend unavailable', final)
        self.assertEqual(self.book.task('turn')['outcome'], 'FAILED')
        self.assert_checkpoint('turn', 'hello', final)
        self.assertEqual(self.turn(agent, 'hello again', 'next'), 'Recovered connection.')

    def test_repeated_failure_readback_errors_do_not_erase_closure_or_repeat_tool(self):
        human = '/read missing.txt'
        agent = self.agent()
        self.book.start(self.binding['hcid'], 'turn', human)
        with patch.object(self.book, 'write_projection', side_effect=OSError('persistent readback failure')):
            with self.assertRaisesRegex(OSError, 'persistent readback failure'):
                agent.run('turn')
        state = self.book.task('turn')
        self.assertEqual(state['phase'], 'COMPLETE')
        self.assertTrue(state['failure_finalized'])
        self.assertEqual(state['outcome'], 'FAILED')
        self.assertEqual(self.book.message_count('turn'), 2)
        final = state['final']
        self.book.close()
        self.book = Notebook(self.root / 'vault')
        self.book.recover()
        resumed = self.agent()
        with patch.object(self.tools, 'execute', side_effect=AssertionError('completed tool must not rerun')):
            self.assertEqual(resumed.run('turn'), final)
        self.assertEqual(resumed.model.calls, [])
        self.assertEqual(len(self.events('turn', 'TOOL_RESULT')), 1)
        self.assertEqual(len(self.events('turn', 'TASK_FAILURE_FINALIZED')), 1)
        self.assertEqual(self.book.message_count('turn'), 2)
        self.assert_checkpoint('turn', human, final)

    def test_initialization_failure_without_elapsed_state_still_returns_saved_final(self):
        agent = self.agent()
        human = 'Please use this context.'
        final = agent.run('turn', self.binding['hcid'], human, context=['../invalid.md'])
        self.assertIn('Context record', final)
        self.assertEqual(self.book.task('turn')['outcome'], 'FAILED')
        self.assertEqual(self.book.task('turn')['failure_snapshot'], {})
        self.assertGreaterEqual(self.book.task('turn')['elapsed'], 0)
        self.assert_checkpoint('turn', human, final)

    def test_duplicate_command_reports_binary_content_matches_without_changes(self):
        payload = b'\x89PNG\xffexact content'
        (self.workspace / 'one.png').write_bytes(payload)
        (self.workspace / 'different-name.bin').write_bytes(payload)
        (self.workspace / 'unrelated.bin').write_bytes(b'x' * len(payload))
        before = {path.name: path.read_bytes() for path in self.workspace.iterdir()}
        final = self.turn(self.agent(), '/duplicates')
        report = json.loads(self.events('turn', 'TOOL_RESULT')[0]['stdout'])
        self.assertEqual(len(report['groups']), 1)
        self.assertEqual(set(report['groups'][0]['files']), {'one.png', 'different-name.bin'})
        self.assertIn('one.png', final)
        self.assertIn('different-name.bin', final)
        self.assertEqual({path.name: path.read_bytes() for path in self.workspace.iterdir()}, before)
        self.assert_checkpoint('turn', '/duplicates', final)

    def test_scan_scope_does_not_expand_to_sibling_folder_after_resume(self):
        (self.workspace / 'selected').mkdir()
        (self.workspace / 'private').mkdir()
        (self.workspace / 'private' / 'DO_NOT_ENUMERATE.txt').write_text('private', encoding='utf-8')
        self.book.start(self.binding['hcid'], 'turn', '/files selected')
        agent = self.agent()
        with patch.object(self.tools, 'execute', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                agent.run('turn')
        state = self.book.task('turn')
        state['pending'] = {'name': 'scan_files', 'path': 'private'}
        self.book.save_task('turn', state)
        final = agent.run('turn')
        self.assertFalse(self.events('turn', 'AUTHORIZATION')[0]['allowed'])
        self.assertNotIn('DO_NOT_ENUMERATE', final)
        self.assertNotIn('DO_NOT_ENUMERATE', json.dumps(self.events('turn', 'TOOL_RESULT')))

    def test_model_cannot_apply_unrequested_plan_even_with_permissive_callback(self):
        (self.workspace / 'note.txt').write_text('keep me', encoding='utf-8')
        agent = self.agent({'tool': {'name': 'apply_plan', 'plan_id': 'placeholder'}}, {'final': 'Approval is required.'})
        plan = self.tools.manager.plan_move('note.txt', 'Documents/note.txt')
        agent.model = ScriptedModel({'tool': {'name': 'apply_plan', 'plan_id': plan['plan_id']}}, {'final': 'Approval is required.'})
        approvals = []
        agent.authorize = lambda request: approvals.append(request) or True
        self.turn(agent, 'Please help me plan my day.')
        self.assertEqual(approvals, [])
        self.assertTrue((self.workspace / 'note.txt').exists())
        self.assertFalse((self.workspace / 'Documents' / 'note.txt').exists())
        self.assertFalse(self.events('turn', 'AUTHORIZATION')[0]['allowed'])

    def test_exact_plan_approval_is_durable_before_move_and_replay_does_not_repeat(self):
        (self.workspace / 'note.txt').write_text('retained bytes', encoding='utf-8')
        approvals = []
        agent = self.agent(authorize=lambda request: approvals.append(dict(request)) or True)
        plan = self.tools.manager.plan_move('note.txt', 'Documents/note.txt')
        request = {'name': 'apply_plan', 'plan_id': plan['plan_id']}
        original_apply = self.tools.manager.apply

        def check_then_apply(plan_id, authorized=False):
            state = self.book.task('turn')
            self.assertEqual(state['phase'], 'EXECUTING')
            self.assertIn(digest(encode(request)), state['approvals'])
            self.assertEqual(state['permissions']['plan_action'], request)
            self.assertTrue(self.events('turn', 'AUTHORIZATION')[-1]['allowed'])
            return original_apply(plan_id, authorized=authorized)

        with patch.object(self.tools.manager, 'apply', side_effect=check_then_apply) as apply:
            final = self.turn(agent, '/apply ' + plan['plan_id'])
            self.assertEqual(agent.run('turn'), final)
            self.assertEqual(apply.call_count, 1)
        self.assertEqual(approvals, [request])
        self.assertEqual((self.workspace / 'Documents' / 'note.txt').read_text(), 'retained bytes')
        self.assert_checkpoint('turn', '/apply ' + plan['plan_id'], final)

    def test_saved_plan_authority_cannot_change_to_another_plan(self):
        (self.workspace / 'first.txt').write_text('first', encoding='utf-8')
        (self.workspace / 'second.txt').write_text('second', encoding='utf-8')
        approved = []
        agent = self.agent(authorize=lambda request: approved.append(request) or True)
        first = self.tools.manager.plan_move('first.txt', 'Documents/first.txt')
        second = self.tools.manager.plan_move('second.txt', 'Documents/second.txt')
        with patch.object(self.tools, 'execute', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.turn(agent, '/apply ' + first['plan_id'])
        state = self.book.task('turn')
        state['pending'] = {'name': 'apply_plan', 'plan_id': second['plan_id']}
        self.book.save_task('turn', state)
        agent.run('turn')
        self.assertEqual(approved, [])
        self.assertFalse(self.events('turn', 'AUTHORIZATION')[0]['allowed'])
        self.assertTrue((self.workspace / 'first.txt').exists())
        self.assertTrue((self.workspace / 'second.txt').exists())
        self.assertFalse((self.workspace / 'Documents').exists())

    def test_undo_requires_its_own_approval_and_restores_exact_bytes(self):
        payload = b'keep exact bytes\r\n\x00\xff'
        (self.workspace / 'archive.bin').write_bytes(payload)
        approvals = []
        agent = self.agent(authorize=lambda request: approvals.append(dict(request)) or True)
        plan = self.tools.manager.plan_move('archive.bin', 'Archives/archive.bin')
        self.turn(agent, '/apply ' + plan['plan_id'], 'apply')
        undo_input = '/undo ' + plan['plan_id']
        final = self.turn(agent, undo_input, 'undo')
        self.assertEqual([request['name'] for request in approvals], ['apply_plan', 'undo_plan'])
        self.assertEqual((self.workspace / 'archive.bin').read_bytes(), payload)
        self.assertFalse((self.workspace / 'Archives' / 'archive.bin').exists())
        self.assert_checkpoint('undo', undo_input, final)

    def test_human_approval_and_final_output_are_captured_in_order(self):
        (self.workspace / 'note.txt').write_text('approved bytes', encoding='utf-8')
        agent = self.agent()
        plan = self.tools.manager.plan_move('note.txt', 'Documents/note.txt')
        runtime = object.__new__(HumanOSRuntime)
        runtime.book, runtime.tools = self.book, self.tools
        agent.authorize = lambda request: runtime.authorize('turn', request)
        human = '/apply ' + plan['plan_id']
        with patch('server.sys.stdin.isatty', return_value=True), patch('builtins.input', return_value='yes') as ask:
            final = self.turn(agent, human)
        rows = list(self.book.db.execute("SELECT role,text FROM transcript WHERE tx='turn' ORDER BY ordinal"))
        self.assertEqual([row['role'] for row in rows], ['HUMAN', 'ASSISTANT', 'HUMAN', 'ASSISTANT'])
        self.assertEqual(rows[0]['text'], human)
        self.assertEqual(rows[1]['text'], ask.call_args[0][0].rstrip('\n'))
        self.assertIn('note.txt', rows[1]['text'])
        self.assertIn('Documents/note.txt', rows[1]['text'])
        self.assertEqual(rows[2]['text'], 'yes')
        self.assertEqual(rows[3]['text'], final)
        output = io.StringIO()
        runtime.deliver('turn', final, output)
        self.assertEqual(output.getvalue(), final + '\n')
        self.assertEqual(self.book.task('turn')['delivery'], 'WRITTEN_TO_OUTPUT_STREAM')
        self.assert_checkpoint('turn', human, final)

    def test_noninteractive_cli_cannot_authorize_moves(self):
        (self.workspace / 'note.txt').write_text('stay here', encoding='utf-8')
        agent = self.agent()
        plan = self.tools.manager.plan_move('note.txt', 'Documents/note.txt')
        runtime = object.__new__(HumanOSRuntime)
        runtime.book, runtime.tools = self.book, self.tools
        agent.authorize = lambda request: runtime.authorize('turn', request)
        with patch('server.sys.stdin.isatty', return_value=False), patch('builtins.input') as ask:
            self.turn(agent, '/apply ' + plan['plan_id'])
        ask.assert_not_called()
        self.assertTrue((self.workspace / 'note.txt').exists())
        self.assertFalse(self.events('turn', 'AUTHORIZATION')[0]['allowed'])

    def test_version_one_scope_resume_retains_exact_authority(self):
        (self.workspace / 'allowed.txt').write_text('allowed evidence', encoding='utf-8')
        (self.workspace / 'secret.txt').write_text('DO_NOT_EXPOSE', encoding='utf-8')
        interrupted = self.agent(ConnectionError('offline'), finalize_on_error=False)
        with self.assertRaises(ConnectionError):
            self.turn(interrupted, 'read allowed.txt')
        state = self.book.task('turn')
        old_scope = task_scope(self.book.get_transaction('turn'), self.workspace, version=1)
        state['permissions'] = old_scope
        self.book.save_task('turn', state)
        self.book.close()
        self.book = Notebook(self.root / 'vault')
        self.book.recover()
        resumed = self.agent({'tool': {'name': 'read_file', 'path': 'secret.txt'}},
                             {'tool': {'name': 'read_file', 'path': 'allowed.txt'}},
                             {'final': 'allowed evidence'}, authorize=lambda request: True)
        self.assertEqual(resumed.run('turn'), 'allowed evidence')
        self.assertEqual(self.book.task('turn')['permissions'], old_scope)
        self.assertEqual(self.book.task('turn')['permissions']['version'], 1)
        self.assertNotIn('DO_NOT_EXPOSE', json.dumps(resumed.model.calls))
        self.assertFalse(self.events('turn', 'AUTHORIZATION')[0]['allowed'])
        self.assertTrue(self.events('turn', 'AUTHORIZATION')[1]['allowed'])
        self.assertTrue(self.book.verify())

    def test_cli_interactive_loop_continues_after_failed_read(self):
        runtime = object.__new__(HumanOSRuntime)
        runtime.book, runtime.tools, runtime.pending = self.book, self.tools, []
        runtime.agent = self.agent({'final': 'Hello after the failure.'})
        args = SimpleNamespace(status=False, resume=None, close_task=None, message=None,
                               session=self.binding['hcid'], tx=None, context=[])
        output = io.StringIO()
        with patch('builtins.input', side_effect=['/read missing.txt', 'hello', 'exit']), redirect_stdout(output), redirect_stderr(io.StringIO()):
            runtime.run(args)
        self.assertIn('missing.txt', output.getvalue())
        self.assertIn('Hello after the failure.', output.getvalue())
        rows = list(self.book.db.execute('SELECT tx FROM transactions'))
        self.assertEqual(len(rows), 2)
        for row in rows:
            self.assertEqual(self.book.task(row['tx'])['phase'], 'COMPLETE')
            self.assertEqual(self.book.task(row['tx'])['delivery'], 'WRITTEN_TO_OUTPUT_STREAM')
        self.assertTrue(self.book.verify())

    def test_cli_workspace_rejects_broad_roots_and_missing_folder(self):
        config = self.root / 'config.json'
        config.write_text(json.dumps({'vault': str(self.root / 'cli-vault'), 'core': str(self.core)}))
        candidates = ('/', str(Path.home()), str(Path(engine.__file__).resolve().parent), str(self.root / 'missing'))
        for folder in candidates:
            with self.subTest(folder=folder), patch('sys.argv', ['server.py', '--config', str(config), '--workspace', folder, '--status']), redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()) as errors:
                self.assertEqual(server.main(), 1)
                self.assertIn('HumanOS RECOVERY REQUIRED', errors.getvalue())

    def test_cli_explicit_workspace_is_used_without_changing_config(self):
        (self.workspace / 'selected-evidence.txt').write_text('evidence', encoding='utf-8')
        config = self.root / 'config.json'
        before = json.dumps({'vault': str(self.root / 'cli-vault'), 'core': str(self.core), 'workspace': 'other-folder'})
        config.write_text(before)
        output = io.StringIO()
        with patch('sys.argv', ['server.py', '--config', str(config), '--workspace', str(self.workspace), '--message', '/files']), redirect_stdout(output), redirect_stderr(io.StringIO()):
            self.assertEqual(server.main(), 0)
        self.assertIn('selected-evidence.txt', output.getvalue())
        self.assertEqual(config.read_text(), before)
        self.assertFalse((self.root / 'other-folder').exists())


if __name__ == '__main__':
    unittest.main()
