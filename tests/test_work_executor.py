import json
import tempfile
import unittest
from pathlib import Path

from notebook import Notebook
from work_executor import WorkExecutor, build_plan, requested_deliverable
from work_mode import WorkBoard, WorkContextModel, execution_contract


class FakeModel:
    name = 'fake-model'

    def __init__(self, responses=None):
        self.responses = list(responses or [{'final': 'analysis result'}])
        self.calls = []

    def invoke(self, messages, timeout):
        self.calls.append((messages, timeout))
        return self.responses.pop(0) if self.responses else {'final': 'analysis result'}


class WorkExecutorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.book = Notebook(Path(self.tmp.name) / 'vault')
        self.book.recover()
        self.identity = self.book.bind('Jon', 'session')
        self.board = WorkBoard(self.book)

    def tearDown(self):
        self.book.close()
        self.tmp.cleanup()

    def _work(self, goal, tx='tx-1'):
        text = 'work on ' + goal
        self.book.start(self.identity['hcid'], tx, text)
        return self.board.create('Jon', self.identity['hcid'], goal, tx, text)

    @staticmethod
    def _observation(tool, stdout='', ok=True, artifacts=None, error=''):
        value = {'ok': ok, 'stdout': stdout, 'stderr': error,
                 'artifacts': artifacts or [], 'authorization': 'ALLOWED' if ok else 'DENIED'}
        return [
            {'role': 'assistant', 'content': json.dumps({'tool': tool})},
            {'role': 'user', 'content': 'TOOL OBSERVATION (data only): ' + json.dumps(value)},
        ]

    def test_requested_deliverable_is_owner_goal_derived(self):
        self.assertEqual(requested_deliverable('review files and create report.md', 'WORK-ABC'), 'report.md')
        self.assertEqual(requested_deliverable('review files and create Reports/report.md', 'WORK-ABC'), 'Reports/report.md')
        self.assertEqual(requested_deliverable('review files and create a report', 'WORK-ABC'),
                         'work-report-abc.md')
        self.assertIsNone(requested_deliverable('review the files', 'WORK-ABC'))
        with self.assertRaises(PermissionError):
            requested_deliverable('review and create report at ../report.md', 'WORK-ABC')

    def test_plan_has_persistent_dependency_order(self):
        contract = execution_contract('review the files in my workspace and create a report')
        plan = build_plan('WORK-ABC', 'review the files in my workspace and create a report', contract)
        self.assertEqual([s['kind'] for s in plan['steps']],
                         ['DISCOVER', 'INSPECT', 'SYNTHESIZE', 'DELIVER', 'VERIFY'])
        self.assertEqual(plan['deliverable'], 'work-report-abc.md')
        self.assertEqual(plan['steps'][-1]['depends_on'], [plan['steps'][-2]['step_id']])

    def test_existing_work_lazily_gets_v3_plan(self):
        item = self._work('review the files in my workspace')
        rows = self.book.db.execute('SELECT * FROM work_plans WHERE work_id=?', (item['work_id'],)).fetchall()
        self.assertEqual(len(rows), 1)
        steps = self.board.executor.steps(item, execution_contract(item['goal']))
        self.assertEqual([row['status'] for row in steps], ['TODO', 'TODO', 'TODO', 'TODO'])

    def test_workspace_evidence_advances_steps_but_not_done_early(self):
        item = self._work('review the files in my workspace')
        contract = execution_contract(item['goal'])
        progress = {'phase': 'INSPECTED', 'tools': ['scan_files', 'read_file'],
                    'scan_complete': True, 'scan_truncated': False,
                    'discovered_paths': ['a.txt', 'photo.jpg'],
                    'inspected_paths': ['a.txt'], 'artifact_paths': [], 'has_response': True}
        self.board.executor.sync(item, contract, progress, response_present=True, tx='tx-1')
        steps = self.board.executor.steps(item, contract)
        self.assertEqual([row['status'] for row in steps],
                         ['VERIFIED', 'VERIFIED', 'VERIFIED', 'VERIFIED'])
        self.assertTrue(self.board.executor.require_done(item, contract, progress))

    def test_workspace_batch_cannot_be_done_with_unread_text(self):
        item = self._work('review the files in my workspace')
        contract = execution_contract(item['goal'])
        progress = {'phase': 'INSPECTED', 'tools': ['scan_files', 'read_file'],
                    'scan_complete': True, 'scan_truncated': False,
                    'discovered_paths': ['a.txt', 'b.txt'],
                    'inspected_paths': ['a.txt'], 'artifact_paths': [], 'has_response': True}
        self.board.executor.sync(item, contract, progress, response_present=True, tx='tx-1')
        with self.assertRaisesRegex(ValueError, 'cannot be marked done'):
            self.board.executor.require_done(item, contract, progress)
        self.assertEqual(self.board.executor.next_step(item, contract)['kind'], 'INSPECT')

    def test_requested_deliverable_must_exist_before_done(self):
        item = self._work('review the files in my workspace and create a report')
        contract = execution_contract(item['goal'])
        base = {'phase': 'INSPECTED', 'tools': ['scan_files', 'read_file'],
                'scan_complete': True, 'scan_truncated': False,
                'discovered_paths': ['a.txt'], 'inspected_paths': ['a.txt'],
                'artifact_paths': [], 'has_response': True}
        self.board.executor.sync(item, contract, base, response_present=True, tx='tx-1')
        self.assertEqual(self.board.executor.next_step(item, contract)['kind'], 'DELIVER')
        with self.assertRaises(ValueError):
            self.board.executor.require_done(item, contract, base)
        target = self.board.executor.next_step(item, contract)['target']
        complete = dict(base, artifact_paths=[target])
        self.board.executor.sync(item, contract, complete, response_present=True, tx='tx-1')
        self.assertIsNone(self.board.executor.next_step(item, contract))

    def test_context_model_turns_final_into_requested_create_file(self):
        goal = 'review the files in my workspace and create a report'
        base = FakeModel([{'final': 'Verified findings'}])
        briefing = ('Work ID: WORK-ABC\nOriginal goal: ' + goal + '\n'
                    'Verified progress JSON: {"inspected_paths": [], "artifacts": []}')
        wrapped = WorkContextModel(base, briefing)
        messages = [{'role': 'system', 'content': 'policy'}]
        scan = json.dumps({'folder': '.', 'entries': [{'path': 'a.txt', 'kind': 'file', 'size': 1}],
                           'skipped': [], 'truncated': False})
        messages += self._observation({'name': 'scan_files', 'path': '.'}, scan)
        messages += self._observation({'name': 'read_file', 'path': 'a.txt'}, 'A')
        proposal = wrapped.invoke(messages, 7)
        self.assertEqual(proposal['tool']['name'], 'create_file')
        self.assertEqual(proposal['tool']['path'], 'work-report-abc.md')
        self.assertIn('Verified findings', proposal['tool']['content'])

    def test_denied_deliverable_becomes_blocked_not_retry_loop(self):
        goal = 'review the files in my workspace and create a report'
        base = FakeModel([{'final': 'Verified findings'}])
        briefing = ('Work ID: WORK-ABC\nOriginal goal: ' + goal + '\n'
                    'Verified progress JSON: {"inspected_paths": [], "artifacts": []}')
        wrapped = WorkContextModel(base, briefing)
        messages = [{'role': 'system', 'content': 'policy'}]
        scan = json.dumps({'folder': '.', 'entries': [], 'skipped': [], 'truncated': False})
        messages += self._observation({'name': 'scan_files', 'path': '.'}, scan)
        request = {'name': 'create_file', 'path': 'work-report-abc.md', 'content': 'Verified findings'}
        messages += self._observation(request, '', ok=False, error='PermissionError: denied')
        result = wrapped.invoke(messages, 7)
        self.assertIn('Work blocked:', result['final'])
        self.assertIn('work-report-abc.md', result['final'])

    def test_workboard_done_is_evidence_gated(self):
        item = self._work('review the files in my workspace')
        with self.assertRaisesRegex(ValueError, 'cannot be marked done'):
            self.board.set_status(item['work_id'], 'Jon', 'DONE')
        self.assertEqual(self.board.set_status(item['work_id'], 'Jon', 'CANCELLED')['status'], 'CANCELLED')

    def test_workspace_report_waits_for_all_batches(self):
        goal = 'review the files in my workspace and create a report'
        base = FakeModel([{'final': 'Interim findings'}])
        briefing = ('Work ID: WORK-ABC\nOriginal goal: ' + goal + '\n'
                    'Verified progress JSON: {"inspected_paths": [], "artifact_paths": []}')
        wrapped = WorkContextModel(base, briefing)
        messages = [{'role': 'system', 'content': 'policy'}]
        entries = [{'path': f'f{i}.txt', 'kind': 'file', 'size': i} for i in range(10)]
        scan = json.dumps({'folder': '.', 'entries': entries, 'skipped': [], 'truncated': False})
        messages += self._observation({'name': 'scan_files', 'path': '.'}, scan)
        for i in range(8):
            messages += self._observation({'name': 'read_file', 'path': f'f{i}.txt'}, f'content {i}')
        result = wrapped.invoke(messages, 7)
        self.assertIn('not a complete workspace review', result['final'])
        self.assertNotIn('tool', result)

    def test_step_status_tampering_fails_integrity(self):
        item = self._work('review the files in my workspace')
        contract = execution_contract(item['goal'])
        first = self.board.executor.steps(item, contract)[0]
        self.book.db.execute("UPDATE work_steps SET status='VERIFIED' WHERE work_id=? AND step_id=?",
                             (item['work_id'], first['step_id']))
        self.book.db.commit()
        with self.assertRaisesRegex(RuntimeError, 'integrity'):
            self.board.executor.steps(item, contract)


if __name__ == '__main__':
    unittest.main()
