from pathlib import Path


def replace_once(path, old, new):
    p = Path(path)
    text = p.read_text()
    if old not in text:
        raise SystemExit(f'marker missing in {path}: {old[:120]!r}')
    if text.count(old) != 1:
        raise SystemExit(f'marker not unique in {path}: {old[:120]!r}')
    p.write_text(text.replace(old, new, 1))


# Safe nested relative deliverables are allowed; parent/absolute paths fail closed.
replace_once('work_executor.py',
"    unsafe = re.search(r'\\b(?:create|write|save|produce|generate|make)\\b[^\\n]{0,100}?(?:\\.\\./|/(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\\.(?:md|txt))', text, re.I)\n",
"    unsafe = re.search(r'\\b(?:create|write|save|produce|generate|make)\\b[^\\n]{0,100}?(?:\\.\\./|(?:^|\\s)/[A-Za-z0-9_.-])', text, re.I)\n")

# Integrity-protect mutable step state with the Notebook key.
replace_once('work_executor.py',
"                evidence_digest TEXT,\n                updated TEXT NOT NULL,\n",
"                state_digest TEXT NOT NULL,\n                updated TEXT NOT NULL,\n")
replace_once('work_executor.py',
"    def ensure(self, item, contract):\n",
"    def _state_digest(self, step, status):\n        value = {'step_id': step['step_id'], 'ordinal': step['ordinal'], 'kind': step['kind'],\n                 'title': step['title'], 'status': status, 'depends_on': step['depends_on'],\n                 'required': bool(step['required']), 'target': step.get('target')}\n        return self.book.content_digest(encode(value))\n\n    def ensure(self, item, contract):\n")
replace_once('work_executor.py',
"                     step.get('target'), None, stamp))\n",
"                     step.get('target'), self._state_digest(step, 'TODO'), stamp))\n")
replace_once('work_executor.py',
"                    bool(row['required']) != bool(step['required']) or row['target'] != step.get('target') or\n                    row['status'] not in STEP_STATUSES):\n",
"                    bool(row['required']) != bool(step['required']) or row['target'] != step.get('target') or\n                    row['status'] not in STEP_STATUSES or\n                    not self.book.digest_matches(row['state_digest'], encode({\n                        'step_id': step['step_id'], 'ordinal': step['ordinal'], 'kind': step['kind'],\n                        'title': step['title'], 'status': row['status'], 'depends_on': step['depends_on'],\n                        'required': bool(step['required']), 'target': step.get('target')}))):\n")

# WorkBoard stores content-light artifact paths; executor consumes those exact paths.
replace_once('work_executor.py',
"        artifacts = {item.get('path') for item in progress.get('artifacts', []) if isinstance(item, dict)}\n",
"        artifacts = set(progress.get('artifact_paths', []))\n")
replace_once('work_executor.py',
"                            'artifact_count': len(progress.get('artifacts', []))}\n",
"                            'artifact_count': len(progress.get('artifact_paths', []))}\n")
replace_once('work_executor.py',
"                new = desired[step['step_id']]\n                if old == new:\n",
"                new = desired[step['step_id']]\n                if old == 'VERIFIED':\n                    new = 'VERIFIED'\n                if old == new:\n")
replace_once('work_executor.py',
"                    'UPDATE work_steps SET status=?,evidence_digest=?,updated=? WHERE work_id=? AND step_id=?',\n                    (new, self.book.content_digest(evidence_text), stamp, item['work_id'], step['step_id']))\n",
"                    'UPDATE work_steps SET status=?,state_digest=?,updated=? WHERE work_id=? AND step_id=?',\n                    (new, self._state_digest(step, new), stamp, item['work_id'], step['step_id']))\n")

# Never create a final deliverable while a bounded review still has unread files.
replace_once('work_mode.py',
"        if 'final' in proposal and self.deliverable:\n            return {'tool': {'name': 'create_file', 'path': self.deliverable, 'content': proposal['final']}}\n",
"        incomplete = bool(checkpoint and int(checkpoint.get('remaining', 0)) > 0)\n        if 'final' in proposal and self.deliverable and not incomplete:\n            return {'tool': {'name': 'create_file', 'path': self.deliverable, 'content': proposal['final']}}\n")

# Validate an owner-derived output path before persisting a new work item.
replace_once('work_mode.py',
"        goal = goal.strip()\n        with self.book.db:\n",
"        goal = goal.strip()\n        requested_deliverable(goal, work_id)\n        with self.book.db:\n")

# Update and extend v3 tests.
replace_once('tests/test_work_executor.py',
"        self.assertEqual(requested_deliverable('review files and create report.md', 'WORK-ABC'), 'report.md')\n",
"        self.assertEqual(requested_deliverable('review files and create report.md', 'WORK-ABC'), 'report.md')\n        self.assertEqual(requested_deliverable('review files and create Reports/report.md', 'WORK-ABC'), 'Reports/report.md')\n")
replace_once('tests/test_work_executor.py',
"                    'inspected_paths': ['a.txt'], 'artifacts': [], 'has_response': True}\n",
"                    'inspected_paths': ['a.txt'], 'artifact_paths': [], 'has_response': True}\n")
replace_once('tests/test_work_executor.py',
"                    'inspected_paths': ['a.txt'], 'artifacts': [], 'has_response': True}\n",
"                    'inspected_paths': ['a.txt'], 'artifact_paths': [], 'has_response': True}\n")
replace_once('tests/test_work_executor.py',
"                'artifacts': [], 'has_response': True}\n",
"                'artifact_paths': [], 'has_response': True}\n")
replace_once('tests/test_work_executor.py',
"        complete = dict(base, artifacts=[{'path': target, 'sha256': 'digest'}])\n",
"        complete = dict(base, artifact_paths=[target])\n")

insert = '''\n    def test_workspace_report_waits_for_all_batches(self):\n        goal = 'review the files in my workspace and create a report'\n        base = FakeModel([{'final': 'Interim findings'}])\n        briefing = ('Work ID: WORK-ABC\\nOriginal goal: ' + goal + '\\n'\n                    'Verified progress JSON: {"inspected_paths": [], "artifact_paths": []}')\n        wrapped = WorkContextModel(base, briefing)\n        messages = [{'role': 'system', 'content': 'policy'}]\n        entries = [{'path': f'f{i}.txt', 'kind': 'file', 'size': i} for i in range(10)]\n        scan = json.dumps({'folder': '.', 'entries': entries, 'skipped': [], 'truncated': False})\n        messages += self._observation({'name': 'scan_files', 'path': '.'}, scan)\n        for i in range(8):\n            messages += self._observation({'name': 'read_file', 'path': f'f{i}.txt'}, f'content {i}')\n        result = wrapped.invoke(messages, 7)\n        self.assertIn('not a complete workspace review', result['final'])\n        self.assertNotIn('tool', result)\n\n    def test_step_status_tampering_fails_integrity(self):\n        item = self._work('review the files in my workspace')\n        contract = execution_contract(item['goal'])\n        first = self.board.executor.steps(item, contract)[0]\n        self.book.db.execute("UPDATE work_steps SET status='VERIFIED' WHERE work_id=? AND step_id=?",\n                             (item['work_id'], first['step_id']))\n        self.book.db.commit()\n        with self.assertRaisesRegex(RuntimeError, 'integrity'):\n            self.board.executor.steps(item, contract)\n'''
replace_once('tests/test_work_executor.py',
"\n\nif __name__ == '__main__':\n    unittest.main()\n",
insert + "\n\nif __name__ == '__main__':\n    unittest.main()\n")

print('Work Executor v3 hardening applied')
