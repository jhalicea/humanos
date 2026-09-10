from pathlib import Path


def replace_once(path, old, new):
    p = Path(path)
    text = p.read_text()
    if text.count(old) != 1:
        raise SystemExit(f'expected exactly one marker in {path}: {old[:120]!r}; got {text.count(old)}')
    p.write_text(text.replace(old, new, 1))


# Persist content-light failed create attempts in work checkpoints.
replace_once('work_mode.py',
"def _checkpoint_from_state(goal, state):\n    evidence = _tool_evidence((state or {}).get('messages', []))\n    tools, inspected, scans, artifacts = [], [], [], []\n",
"def _checkpoint_from_state(goal, state):\n    messages = (state or {}).get('messages', [])\n    evidence = _tool_evidence(messages)\n    attempts = _tool_attempts(messages)\n    tools, inspected, scans, artifacts, failed_artifacts = [], [], [], [], []\n")
replace_once('work_mode.py',
"    contract = execution_contract(goal)\n",
"    for request, observation in attempts:\n        if (request.get('name') == 'create_file' and not observation.get('ok') and\n                isinstance(request.get('path'), str)):\n            failed_artifacts.append(request['path'])\n    contract = execution_contract(goal)\n")
replace_once('work_mode.py',
"            'artifact_paths': sorted(set(artifacts))[:50],\n            'required_paths': sorted(set(contract.get('required_paths', [])))}\n",
"            'artifact_paths': sorted(set(artifacts))[:50],\n            'failed_artifact_paths': sorted(set(failed_artifacts))[:50],\n            'required_paths': sorted(set(contract.get('required_paths', [])))}\n")

# Aggregate failed artifact attempts across turns; a later successful artifact wins.
replace_once('work_mode.py',
"        tools, inspected, discovered, artifacts, required = set(), set(), set(), set(), set()\n",
"        tools, inspected, discovered, artifacts, failed_artifacts, required = set(), set(), set(), set(), set(), set()\n")
replace_once('work_mode.py',
"            artifacts.update(value.get('artifact_paths', []))\n            required.update(value.get('required_paths', []))\n",
"            artifacts.update(value.get('artifact_paths', []))\n            failed_artifacts.update(value.get('failed_artifact_paths', []))\n            required.update(value.get('required_paths', []))\n")
replace_once('work_mode.py',
"                  'artifact_paths': sorted(artifacts)[:50], 'required_paths': sorted(required),\n",
"                  'artifact_paths': sorted(artifacts)[:50],\n                  'failed_artifact_paths': sorted(failed_artifacts - artifacts)[:50],\n                  'required_paths': sorted(required),\n")

# Work turn itself becomes BLOCKED when a requested create was denied/failed.
replace_once('work_mode.py',
"        status = 'BLOCKED' if failed else 'REVIEW'\n        outcome = 'FAILED' if failed else 'TURN_COMPLETE'\n        digest = self.book.content_digest(response)\n",
"        checkpoint = _checkpoint_from_state(row['goal'], self.book.task(tx) or {})\n        blocked = failed or bool(checkpoint.get('failed_artifact_paths'))\n        status = 'BLOCKED' if blocked else 'REVIEW'\n        outcome = 'FAILED' if failed else 'BLOCKED' if blocked else 'TURN_COMPLETE'\n        digest = self.book.content_digest(response)\n")
replace_once('work_mode.py',
"        checkpoint = _checkpoint_from_state(row['goal'], self.book.task(tx) or {})\n        summary = encode(checkpoint)\n",
"        summary = encode(checkpoint)\n")
replace_once('work_mode.py',
"        self.executor.sync(updated, execution_contract(updated['goal']), progress,\n                           failed=failed, response_present=not failed, tx=tx)\n",
"        self.executor.sync(updated, execution_contract(updated['goal']), progress,\n                           failed=blocked, response_present=True, tx=tx)\n")

# Executor understands a failed owner-requested deliverable as BLOCKED, not TODO/WORKING.
replace_once('work_executor.py',
"        artifacts = set(progress.get('artifact_paths', []))\n        scan_complete = bool(progress.get('scan_complete'))\n",
"        artifacts = set(progress.get('artifact_paths', []))\n        failed_artifacts = set(progress.get('failed_artifact_paths', [])) - artifacts\n        scan_complete = bool(progress.get('scan_complete'))\n")
replace_once('work_executor.py',
"            if deliver.get('target') in artifacts:\n                statuses[deliver['step_id']] = 'VERIFIED'\n            elif failed and synth_status == 'VERIFIED':\n                statuses[deliver['step_id']] = 'BLOCKED'\n",
"            if deliver.get('target') in artifacts:\n                statuses[deliver['step_id']] = 'VERIFIED'\n            elif deliver.get('target') in failed_artifacts:\n                statuses[deliver['step_id']] = 'BLOCKED'\n            elif failed and synth_status == 'VERIFIED':\n                statuses[deliver['step_id']] = 'BLOCKED'\n")
# A failed create attempt proves synthesis happened, because the supervisor only proposes create after model synthesis.
replace_once('work_executor.py',
"            synth = by_kind['SYNTHESIZE']['step_id']\n            if statuses[inspect] == 'VERIFIED' and response_present and not failed:\n                statuses[synth] = 'VERIFIED'\n",
"            synth = by_kind['SYNTHESIZE']['step_id']\n            deliver_target = by_kind.get('DELIVER', {}).get('target')\n            if statuses[inspect] == 'VERIFIED' and (response_present and not failed or deliver_target in failed_artifacts):\n                statuses[synth] = 'VERIFIED'\n")

# Make the create approval readable while still showing a bounded content preview.
replace_once('server.py',
"        else:\n            prompt = 'Approve creating this workspace file? ' + json.dumps(request, ensure_ascii=False) + ' [yes/no]'\n",
"        elif request['name'] == 'create_file':\n            content = request.get('content', '')\n            preview = content[:1200] + ('…' if len(content) > 1200 else '')\n            prompt = ('Approve creating workspace file ' + request['path'] + ' (' +\n                      str(len(content.encode('utf-8'))) + ' bytes)?\\nPreview:\\n' + preview + '\\n[yes/no]')\n        else:\n            safe = {key: value for key, value in request.items() if key != 'text'}\n            prompt = 'Approve ' + request['name'] + '? ' + json.dumps(safe, ensure_ascii=False) + ' [yes/no]'\n")

# Add true WorkBoard checkpoint/deliverable/DONE integration coverage.
test = '''\n    def test_checkpoint_artifact_drives_deliverable_verified_and_done(self):\n        goal = 'review the files in my workspace and create a report'\n        item = self._work(goal)\n        target = self.board.executor.next_step(item, execution_contract(goal))\n        self.assertEqual(target['kind'], 'DISCOVER')\n        scan = json.dumps({'folder': '.', 'entries': [\n            {'path': 'a.txt', 'kind': 'file', 'size': 1}], 'skipped': [], 'truncated': False})\n        messages = []\n        messages += self._observation({'name': 'scan_files', 'path': '.'}, scan)\n        messages += self._observation({'name': 'read_file', 'path': 'a.txt'}, 'A')\n        report = requested_deliverable(goal, item['work_id'])\n        messages += self._observation(\n            {'name': 'create_file', 'path': report, 'content': 'Verified report'},\n            'Created ' + report, artifacts=[{'path': report, 'sha256': 'digest'}])\n        self.book.save_task('tx-1', {'messages': messages})\n        updated = self.board.finish_turn(item['work_id'], 'Jon', 'tx-1', 'Work deliverable created and verified: ' + report)\n        self.assertEqual(updated['status'], 'REVIEW')\n        progress = self.board.progress(item['work_id'], 'Jon')\n        self.assertIn(report, progress['artifact_paths'])\n        self.assertIsNone(self.board.executor.next_step(updated, execution_contract(goal)))\n        self.assertEqual(self.board.set_status(item['work_id'], 'Jon', 'DONE')['status'], 'DONE')\n\n    def test_failed_deliverable_persists_blocked_job_and_step(self):\n        goal = 'review the files in my workspace and create a report'\n        item = self._work(goal)\n        scan = json.dumps({'folder': '.', 'entries': [\n            {'path': 'a.txt', 'kind': 'file', 'size': 1}], 'skipped': [], 'truncated': False})\n        messages = []\n        messages += self._observation({'name': 'scan_files', 'path': '.'}, scan)\n        messages += self._observation({'name': 'read_file', 'path': 'a.txt'}, 'A')\n        report = requested_deliverable(goal, item['work_id'])\n        messages += self._observation({'name': 'create_file', 'path': report, 'content': 'Verified report'},\n                                      '', ok=False, error='PermissionError: denied')\n        self.book.save_task('tx-1', {'messages': messages})\n        updated = self.board.finish_turn(item['work_id'], 'Jon', 'tx-1',\n                                         'Work blocked: HumanOS could not create the requested deliverable ' + report + '.')\n        self.assertEqual(updated['status'], 'BLOCKED')\n        steps = self.board.executor.steps(updated, execution_contract(goal))\n        by_kind = {row['kind']: row['status'] for row in steps}\n        self.assertEqual(by_kind['SYNTHESIZE'], 'VERIFIED')\n        self.assertEqual(by_kind['DELIVER'], 'BLOCKED')\n        self.assertEqual(by_kind['VERIFY'], 'BLOCKED')\n        with self.assertRaises(ValueError):\n            self.board.set_status(item['work_id'], 'Jon', 'DONE')\n'''
replace_once('tests/test_work_executor.py',
"\n\nif __name__ == '__main__':\n    unittest.main()\n",
test + "\n\nif __name__ == '__main__':\n    unittest.main()\n")

print('Blocked-state and end-to-end v3 fixes applied')
