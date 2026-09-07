import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from notebook import Notebook, BindingConflict
from engine import Agent, Tools, OllamaModel, load_context
from server import HumanOSRuntime


class FakeModel:
    name = 'test-model'
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.calls = []
    def invoke(self, messages, timeout):
        self.calls.append(json.loads(json.dumps(messages)))
        response = next(self.responses)
        if isinstance(response, BaseException):
            raise response
        return response


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.book = Notebook(self.root / 'vault')
        self.book.recover()
        self.binding = self.book.bind('Jon', 'opening')
        self.workspace = self.root / 'workspace'
        self.tools = Tools(self.workspace)
        self.core = self.root / 'core'
        self.core.mkdir()
        (self.core / 'constitution.md').write_text('Human owns HumanOS. Models cannot grant authority.')
    def tearDown(self):
        self.book.close()
        self.tmp.cleanup()
    def agent(self, *responses, **kwargs):
        return Agent(self.book, FakeModel(*responses), self.tools, self.core, **kwargs)
    def turn(self, agent, text='Help with this test task.', tx='tx-1'):
        return agent.run(tx, self.binding['hcid'], text)
    def test_new_identity_unique_even_same_opening(self):
        new = self.book.bind('Jon', 'opening')
        self.assertNotEqual(new['hcid'], self.binding['hcid'])
        self.assertNotEqual(new['page'], self.binding['page'])
    def test_exact_identity_continuation(self):
        self.assertEqual(self.book.bind('Jon', 'later', self.binding['hcid']), self.binding)
    def test_ambiguous_binding_fails_closed(self):
        with self.assertRaises(BindingConflict):
            self.book.bind('Jon', 'later', self.binding['hcid'], 'wrong-page')
        self.assertEqual(self.book.db.execute('SELECT COUNT(*) FROM transcript').fetchone()[0], 0)
        self.assertEqual(self.book.db.execute("SELECT COUNT(*) FROM identities WHERE binding='RECONCILIATION_REQUIRED'").fetchone()[0], 1)
        fallback = json.loads((self.book.root / 'recovery.jsonl').read_text().splitlines()[-1])
        self.assertEqual(fallback['payload']['text'], 'later')
    def test_unknown_session_does_not_reuse_page(self):
        with self.assertRaises(BindingConflict):
            self.book.bind('Jon', 'opening', 'made-up')
    def test_exact_transcript_append(self):
        original = '  Jon: correction\r\nNo—keep HumanOS. 🧭\n  '
        self.book.start(self.binding['hcid'], 't', original)
        self.book.append('t', 1, 'ASSISTANT', '\nI disagree.  ')
        self.book.project()
        self.book.verify()
        self.assertEqual(self.book.db.execute('SELECT text FROM transcript ORDER BY seq').fetchone()[0], original)
    def test_transcript_append_only_enforced(self):
        self.book.start(self.binding['hcid'], 't', 'x')
        with self.assertRaises(sqlite3.IntegrityError):
            self.book.db.execute("UPDATE transcript SET text='bad'")
        self.book.db.rollback()
    def test_duplicate_transaction_prevention(self):
        a = self.agent({'final': 'done'})
        self.turn(a)
        self.turn(a)
        self.assertEqual(len(a.model.calls), 1)
        self.assertEqual(self.book.db.execute('SELECT COUNT(*) FROM transcript').fetchone()[0], 2)
    def test_duplicate_transaction_different_payload_rejected(self):
        self.book.start(self.binding['hcid'], 't', 'one')
        with self.assertRaises(ValueError):
            self.book.start(self.binding['hcid'], 't', 'two')
        self.assertEqual(self.book.db.execute('SELECT input FROM transactions WHERE tx=?', ('t',)).fetchone()[0], 'one')
    def test_rejected_replay_does_not_change_verified_transaction(self):
        self.turn(self.agent({'final': 'done'}))
        with self.assertRaises(ValueError):
            self.book.start(self.binding['hcid'], 'tx-1', 'different')
        self.assertEqual(self.book.get_transaction('tx-1')['status'], 'CHECKPOINTED')
        self.book.verify()
    def test_completed_transaction_rejects_new_message(self):
        self.turn(self.agent({'final': 'done'}))
        with self.assertRaises(ValueError):
            self.book.append('tx-1', 2, 'ASSISTANT', 'extra')
    def test_fallback_recovers_input_when_database_insert_fails(self):
        self.book.db.execute("CREATE TRIGGER fail_insert BEFORE INSERT ON transactions BEGIN SELECT RAISE(ABORT, 'injected'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.book.start(self.binding['hcid'], 't', 'retain exact input')
        self.book.db.execute('DROP TRIGGER fail_insert')
        self.book.recover()
        self.assertEqual(self.book.get_transaction('t')['input'], 'retain exact input')
    def test_notebook_checkpoint_readback(self):
        self.turn(self.agent({'final': 'done'}))
        self.assertTrue(self.book.verify())
        self.assertEqual(self.book.db.execute('SELECT status FROM transactions').fetchone()[0], 'CHECKPOINTED')
    def test_simulated_write_failure_recovery(self):
        with patch.object(self.book, 'write_projection', side_effect=OSError('simulated disk failure')):
            with self.assertRaises(OSError):
                self.book.start(self.binding['hcid'], 't', 'exact never lost')
        record = json.loads((self.book.root / 'recovery.jsonl').read_text().splitlines()[-1])
        self.assertEqual(record['payload']['text'], 'exact never lost')
        self.assertEqual(self.book.db.execute('SELECT status FROM transactions').fetchone()[0], 'RECOVERY_REQUIRED')
        self.book.recover()
        self.assertTrue(self.book.verify())
    def test_final_write_failure_recovers_without_model_repeat(self):
        self.book.start(self.binding['hcid'], 't', 'hello')
        agent = self.agent({'final': 'exact final'})
        with patch.object(self.book, 'write_projection', side_effect=OSError('disk failure')):
            with self.assertRaises(OSError):
                agent.run('t')
        self.book.recover()
        self.assertEqual(agent.run('t'), 'exact final')
        self.assertEqual(len(agent.model.calls), 1)
        self.assertEqual(self.book.db.execute('SELECT COUNT(*) FROM transcript').fetchone()[0], 2)
    def test_adapter_invocation(self):
        class Response(io.BytesIO):
            pass
        class Opener:
            def open(inner, req, timeout):
                self.assertEqual(json.loads(req.data)['model'], 'configured-model')
                self.assertEqual(timeout, 7)
                return Response(json.dumps({'message': {'content': '{"final":"yes"}', 'thinking': 'not captured'}}).encode())
        model = OllamaModel('configured-model', 'http://127.0.0.1:11434', Opener())
        self.assertEqual(model.invoke([{'role': 'user', 'content': 'Hi'}], 7), {'final': 'yes'})
    def test_nonlocal_model_rejected(self):
        with self.assertRaises(ValueError):
            OllamaModel('x', 'https://example.com')
    def test_unauthorized_tool_rejected(self):
        result = self.tools.execute({'name': 'shell', 'path': 'whoami'}, lambda r: True)
        self.assertFalse(result['ok'])
        self.assertEqual(result['authorization'], 'DENIED')
    def test_authorized_sandboxed_tool_success(self):
        (self.workspace / 'note.txt').write_text('verified content')
        result = self.tools.execute({'name': 'read_file', 'path': 'note.txt'}, lambda r: True)
        self.assertEqual(result['stdout'], 'verified content')
        self.assertTrue(result['ok'])
    def test_traversal_and_symlink_rejected(self):
        secret = self.root / 'outside.txt'
        secret.write_text('outside')
        (self.workspace / 'link.txt').symlink_to(secret)
        for path in ('../outside.txt', str(secret), 'link.txt', '.hidden'):
            self.assertFalse(self.tools.execute({'name': 'read_file', 'path': path}, lambda r: True)['ok'])
    def test_parent_symlink_and_hardlink_rejected(self):
        import os
        (self.workspace / 'outside').symlink_to(self.core, target_is_directory=True)
        os.link(self.core / 'constitution.md', self.workspace / 'hardlink')
        for path in ('outside/constitution.md', 'hardlink'):
            self.assertFalse(self.tools.execute({'name': 'read_file', 'path': path}, lambda r: True)['ok'])
    def test_create_requires_authorization_and_never_overwrites(self):
        request = {'name': 'create_file', 'path': 'new.txt', 'content': 'original'}
        self.assertFalse(self.tools.execute(request, lambda r: False)['ok'])
        self.assertFalse((self.workspace / 'new.txt').exists())
        self.assertTrue(self.tools.execute(request, lambda r: True)['ok'])
        request['content'] = 'changed'
        self.assertFalse(self.tools.execute(request, lambda r: True)['ok'])
        self.assertEqual((self.workspace / 'new.txt').read_text(), 'original')
    def test_agent_loop_success(self):
        (self.workspace / 'note.txt').write_text('Notebook first')
        agent = self.agent({'tool': {'name': 'read_file', 'path': 'note.txt'}}, {'final': 'Notebook first'})
        self.assertEqual(self.turn(agent, 'read note.txt'), 'Notebook first')
        self.assertIn('Notebook first', agent.model.calls[1][-1]['content'])
        kinds = [r[0] for r in self.book.db.execute('SELECT kind FROM events')]
        for k in ('CONTEXT_LOADED', 'MODEL_REQUEST', 'AUTHORIZATION', 'TOOL_RESULT', 'CHECKPOINT_VERIFIED'):
            self.assertIn(k, kinds)
    def test_tool_failure_surfaced_and_recoverable(self):
        agent = self.agent({'tool': {'name': 'read_file', 'path': 'missing.txt'}}, {'final': 'File does not exist.'})
        self.assertEqual(self.turn(agent, 'read missing.txt'), 'File does not exist.')
        self.assertIn('FileNotFoundError', agent.model.calls[1][-1]['content'])
        self.assertEqual(self.book.db.execute('SELECT COUNT(*) FROM recovery').fetchone()[0], 1)
    def test_task_resume_after_model_outage(self):
        (self.workspace / 'note.txt').write_text('persisted')
        agent = self.agent({'tool': {'name': 'read_file', 'path': 'note.txt'}}, ConnectionError('offline'))
        with self.assertRaises(ConnectionError):
            self.turn(agent, 'read note.txt')
        self.book.close()
        self.book = Notebook(self.root / 'vault')
        self.book.recover()
        agent = self.agent({'final': 'resumed'})
        self.assertEqual(agent.run('tx-1'), 'resumed')
        self.assertIn('persisted', agent.model.calls[0][-1]['content'])
        self.assertEqual(self.book.db.execute("SELECT COUNT(*) FROM events WHERE kind='TOOL_RESULT'").fetchone()[0], 1)
    def test_unavailable_backend_truthful(self):
        with self.assertRaises(ConnectionError):
            self.turn(self.agent(ConnectionError('backend unavailable')))
        self.assertEqual(self.book.db.execute('SELECT status FROM transactions').fetchone()[0], 'RECOVERY_REQUIRED')
        self.assertEqual(self.book.db.execute("SELECT COUNT(*) FROM transcript WHERE role='ASSISTANT'").fetchone()[0], 0)
    def test_task_step_limit(self):
        agent = self.agent({'tool': {'name': 'list_files', 'path': '.'}}, max_steps=1)
        with self.assertRaisesRegex(RuntimeError, 'iteration budget'):
            self.turn(agent)
    def test_invalid_model_proposal_repaired_within_budget(self):
        agent = self.agent({'bad': 'shape'}, {'final': 'repaired'})
        self.assertEqual(self.turn(agent), 'repaired')
        self.assertEqual(len(agent.model.calls), 2)
        self.assertIn('FORMAT ERROR', agent.model.calls[1][-1]['content'])
    def test_task_time_limit(self):
        with self.assertRaises(TimeoutError):
            self.turn(self.agent({'final': 'never'}, max_seconds=0))
    def test_context_selective(self):
        (self.core / 'selected.md').write_text('relevant')
        (self.core / 'private.md').write_text('unrelated')
        packet = load_context(self.core, ['selected.md'])
        self.assertEqual(len(packet['records']), 1)
        self.assertNotIn('unrelated', json.dumps(packet))
    def test_empty_context_does_not_load_constitution(self):
        packet = load_context(self.core, [])
        self.assertEqual(packet['records'], [])
        self.assertEqual(packet['missing'], [])
    def test_greeting_tool_request_is_denied(self):
        agent = self.agent({'tool': {'name': 'read_file', 'path': 'constitution.md'}},
                           {'final': 'Hello, Jon.'})
        agent.authorize = lambda request: request.get('path', '').casefold() in 'hi'
        self.assertEqual(agent.run('greeting', self.binding['hcid'], 'hi'), 'Hello, Jon.')
        authorization = [json.loads(r[0]) for r in self.book.db.execute(
            "SELECT payload FROM events WHERE tx='greeting' AND kind='AUTHORIZATION'")]
        self.assertEqual(authorization[-1]['allowed'], False)
    def test_system_prompt_requires_complete_observation_answer(self):
        self.assertIn("answer every explicit part", __import__('engine').SYSTEM)
        self.assertIn("Preserve exact values", __import__('engine').SYSTEM)
    def test_end_to_end_final_capture_and_output(self):
        agent = self.agent({'tool': {'name': 'list_files', 'path': '.'}}, {'final': '  Exact final\nwith correction. 🧭  '})
        final = self.turn(agent)
        runtime = object.__new__(HumanOSRuntime)
        runtime.book = self.book
        output = io.StringIO()
        runtime.deliver('tx-1', final, output)
        self.assertEqual(output.getvalue(), final + '\n')
        self.assertEqual(self.book.db.execute("SELECT text FROM transcript WHERE role='ASSISTANT'").fetchone()[0], final)
        self.assertEqual(self.book.task('tx-1')['delivery'], 'WRITTEN_TO_OUTPUT_STREAM')
        self.book.verify()
    def test_output_failure_not_claimed_delivered(self):
        final = self.turn(self.agent({'final': 'ready'}))
        runtime = object.__new__(HumanOSRuntime)
        runtime.book = self.book
        class Broken:
            def write(self, text):
                raise BrokenPipeError('closed')
        with self.assertRaises(BrokenPipeError):
            runtime.deliver('tx-1', final, Broken())
        self.assertEqual(self.book.task('tx-1')['delivery'], 'OUTPUT_UNCERTAIN')
    def test_second_writer_rejected(self):
        with self.assertRaises(RuntimeError):
            Notebook(self.root / 'vault')
    def test_unknown_write_outcome_not_replayed(self):
        self.book.start(self.binding['hcid'], 't', 'create file')
        state = {'phase': 'EXECUTING', 'steps': 1, 'elapsed': 0,
                 'model': 'test-model', 'workspace': str(self.tools.workspace),
                 'pending': {'name': 'create_file', 'path': 'x', 'content': 'x'}}
        self.book.save_task('t', state)
        with self.assertRaisesRegex(RuntimeError, 'unknown outcome'):
            self.agent({'final': 'wrong'}).run('t')
        self.assertFalse((self.workspace / 'x').exists())
    def test_audit_chain_detects_corruption(self):
        self.book.db.execute('DROP TRIGGER events_no_update')
        self.book.db.execute("UPDATE events SET payload='{}' WHERE seq=1")
        self.book.db.commit()
        with self.assertRaisesRegex(RuntimeError, 'Audit chain'):
            self.book.verify()
    def test_final_readback_required(self):
        self.turn(self.agent({'final': 'original'}))
        state = self.book.task('tx-1')
        state['final'] = 'different'
        self.book.save_task('tx-1', state)
        with self.assertRaisesRegex(RuntimeError, 'Final response readback'):
            self.book.checkpoint('tx-1')
    def test_projection_tamper_preserved_and_repaired(self):
        p = self.book.root / 'bindings.json'
        p.write_text('tampered')
        with self.assertRaises(Exception):
            self.book.verify()
        self.book.recover()
        self.assertTrue(self.book.verify())
        self.assertTrue(any(p.read_text() == 'tampered' for p in (self.book.root / 'recovery-copies').glob('*/bindings.json')))


if __name__ == '__main__':
    unittest.main()
