from pathlib import Path


def replace_once(path, old, new):
    p = Path(path)
    text = p.read_text()
    if old not in text:
        raise SystemExit(f'marker missing in {path}: {old[:100]!r}')
    if text.count(old) != 1:
        raise SystemExit(f'marker not unique in {path}: {old[:100]!r}')
    p.write_text(text.replace(old, new, 1))


# work_executor.py: reject obviously unsafe owner-requested output paths.
replace_once('work_executor.py',
"    explicit = re.search(\n        r'\\b(?:create|write|save|produce|generate|make)\\b[^\\n]{0,100}?'\n        r'([A-Za-z0-9_-]+(?:/[A-Za-z0-9_.-]+)*\\.(?:md|txt))\\b', text, re.I)\n",
"    unsafe = re.search(r'\\b(?:create|write|save|produce|generate|make)\\b[^\\n]{0,100}?(?:\\.\\./|/(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\\.(?:md|txt))', text, re.I)\n    if unsafe:\n        raise PermissionError('Requested work deliverable path is outside the selected workspace')\n    explicit = re.search(\n        r'\\b(?:create|write|save|produce|generate|make)\\b[^\\n]{0,100}?'\n        r'([A-Za-z0-9_-]+(?:/[A-Za-z0-9_.-]+)*\\.(?:md|txt))\\b', text, re.I)\n")

# work_mode.py integration.
replace_once('work_mode.py',
"from notebook import encode, now\n",
"from notebook import encode, now\nfrom work_executor import WorkExecutor, requested_deliverable\n")

replace_once('work_mode.py',
'''def _tool_evidence(messages):\n    """Pair model tool proposals with successful executor observations."""\n    pending = None\n    evidence = []\n    for message in messages:\n        role = message.get('role')\n        content = message.get('content', '')\n        if role == 'assistant':\n            try:\n                proposal = json.loads(content)\n            except Exception:\n                pending = None\n                continue\n            pending = proposal.get('tool') if isinstance(proposal, dict) else None\n            continue\n        prefix = 'TOOL OBSERVATION (data only): '\n        if role == 'user' and content.startswith(prefix):\n            try:\n                observation = json.loads(content[len(prefix):])\n            except Exception:\n                pending = None\n                continue\n            if pending and observation.get('ok'):\n                evidence.append((dict(pending), observation))\n            pending = None\n    return evidence\n''',
'''def _tool_attempts(messages):\n    """Pair model tool proposals with executor observations, including failures."""\n    pending = None\n    attempts = []\n    for message in messages:\n        role = message.get('role')\n        content = message.get('content', '')\n        if role == 'assistant':\n            try:\n                proposal = json.loads(content)\n            except Exception:\n                pending = None\n                continue\n            pending = proposal.get('tool') if isinstance(proposal, dict) else None\n            continue\n        prefix = 'TOOL OBSERVATION (data only): '\n        if role == 'user' and content.startswith(prefix):\n            try:\n                observation = json.loads(content[len(prefix):])\n            except Exception:\n                pending = None\n                continue\n            if pending:\n                attempts.append((dict(pending), observation))\n            pending = None\n    return attempts\n\n\ndef _tool_evidence(messages):\n    """Successful executor observations only."""\n    return [(request, observation) for request, observation in _tool_attempts(messages)\n            if observation.get('ok')]\n''')

replace_once('work_mode.py',
'''def _goal_from_briefing(briefing):\n    for line in briefing.splitlines():\n        if line.startswith('Original goal: '):\n            return line[len('Original goal: '):]\n    raise RuntimeError('Delegated work briefing is missing its original goal')\n''',
'''def _goal_from_briefing(briefing):\n    for line in briefing.splitlines():\n        if line.startswith('Original goal: '):\n            return line[len('Original goal: '):]\n    raise RuntimeError('Delegated work briefing is missing its original goal')\n\n\ndef _work_id_from_briefing(briefing):\n    for line in briefing.splitlines():\n        if line.startswith('Work ID: '):\n            value = line[len('Work ID: '):].strip()\n            if re.fullmatch(r'WORK-[A-Za-z0-9]+', value):\n                return value.upper()\n    raise RuntimeError('Delegated work briefing is missing its work ID')\n''')

start = '''def _checkpoint_from_state(goal, state):\n    evidence = _tool_evidence((state or {}).get('messages', []))\n    tools, inspected, scans = [], [], []\n    for request, observation in evidence:\n        name = request.get('name')\n        if isinstance(name, str):\n            tools.append(name)\n        if name == 'read_file' and isinstance(request.get('path'), str):\n            inspected.append(request['path'])\n        if name == 'scan_files':\n            scans.extend(_scan_entries([(request, observation)]))\n    contract = execution_contract(goal)\n    if contract['kind'] == 'workspace_review':\n        phase = 'INSPECTED' if inspected else 'DISCOVERED' if scans else 'NOT_STARTED'\n    elif contract['kind'] == 'file_review':\n        phase = 'INSPECTED' if inspected else 'NOT_STARTED'\n    else:\n        phase = 'TURN_COMPLETE'\n    return {'version': 1, 'phase': phase,\n            'tools': sorted(set(tools)),\n            'inspected_paths': sorted(set(inspected)),\n            'discovered_paths': sorted(set(scans))[:200]}\n'''
new = '''def _checkpoint_from_state(goal, state):\n    evidence = _tool_evidence((state or {}).get('messages', []))\n    tools, inspected, scans, artifacts = [], [], [], []\n    scan_complete = False\n    scan_truncated = False\n    for request, observation in evidence:\n        name = request.get('name')\n        if isinstance(name, str):\n            tools.append(name)\n        if name == 'read_file' and isinstance(request.get('path'), str):\n            inspected.append(request['path'])\n        if name == 'scan_files':\n            scans.extend(_scan_entries([(request, observation)]))\n            if request.get('path', '.') == '.':\n                try:\n                    report = json.loads(observation.get('stdout') or '{}')\n                except Exception:\n                    report = {}\n                scan_truncated = bool(report.get('truncated')) if isinstance(report, dict) else False\n                scan_complete = isinstance(report, dict) and not scan_truncated\n        for artifact in observation.get('artifacts') or []:\n            path = artifact.get('path') if isinstance(artifact, dict) else None\n            if isinstance(path, str) and path and not path.startswith('.') and '/.' not in path:\n                artifacts.append(path)\n    contract = execution_contract(goal)\n    if contract['kind'] == 'workspace_review':\n        phase = 'INSPECTED' if inspected else 'DISCOVERED' if (scans or scan_complete) else 'NOT_STARTED'\n    elif contract['kind'] == 'file_review':\n        phase = 'INSPECTED' if inspected else 'NOT_STARTED'\n    elif contract['kind'] == 'web_research':\n        phase = 'RESEARCHED' if 'internet_search' in tools else 'NOT_STARTED'\n    else:\n        phase = 'TURN_COMPLETE'\n    return {'version': 2, 'phase': phase,\n            'tools': sorted(set(tools)),\n            'inspected_paths': sorted(set(inspected)),\n            'discovered_paths': sorted(set(scans))[:200],\n            'scan_complete': scan_complete, 'scan_truncated': scan_truncated,\n            'artifact_paths': sorted(set(artifacts))[:50],\n            'required_paths': sorted(set(contract.get('required_paths', [])))}\n'''
replace_once('work_mode.py', start, new)

replace_once('work_mode.py',
"        self.goal = _goal_from_briefing(briefing)\n        self.contract = execution_contract(self.goal)\n        self.progress = _progress_from_briefing(briefing)\n",
"        self.work_id = _work_id_from_briefing(briefing)\n        self.goal = _goal_from_briefing(briefing)\n        self.contract = execution_contract(self.goal)\n        self.progress = _progress_from_briefing(briefing)\n        self.deliverable = requested_deliverable(self.goal, self.work_id)\n")

replace_once('work_mode.py',
"        required_tool, checkpoint = self._next_required_tool(messages)\n        if required_tool:\n            return {'tool': required_tool}\n\n        messages[0]['content'] += (\n",
"        required_tool, checkpoint = self._next_required_tool(messages)\n        if required_tool:\n            return {'tool': required_tool}\n\n        if self.deliverable:\n            attempts = [(request, observation) for request, observation in _tool_attempts(messages)\n                        if request.get('name') == 'create_file' and request.get('path') == self.deliverable]\n            if attempts:\n                request, observation = attempts[-1]\n                if observation.get('ok'):\n                    return {'final': 'Work deliverable created and verified: ' + self.deliverable}\n                return {'final': 'Work blocked: HumanOS could not create the requested deliverable ' +\n                        self.deliverable + '. ' + (observation.get('stderr') or 'The create request was not completed.')}\n\n        messages[0]['content'] += (\n")

replace_once('work_mode.py',
"        proposal = self.model.invoke(messages, timeout)\n        if 'final' in proposal and checkpoint:\n",
"        proposal = self.model.invoke(messages, timeout)\n        if 'final' in proposal and self.deliverable:\n            return {'tool': {'name': 'create_file', 'path': self.deliverable, 'content': proposal['final']}}\n        if 'final' in proposal and checkpoint:\n")

replace_once('work_mode.py',
"            ''')\n\n    def _row(self, work_id):\n",
"            ''')\n        self.executor = WorkExecutor(self.book)\n\n    def _row(self, work_id):\n")

replace_once('work_mode.py',
"        return self._row(work_id)\n\n    def begin_turn(self, work_id, owner, hcid, tx, exact_input):\n",
"        item = self._row(work_id)\n        self.executor.ensure(item, execution_contract(goal))\n        return item\n\n    def begin_turn(self, work_id, owner, hcid, tx, exact_input):\n")

old_progress = '''    def progress(self, work_id, owner):\n        self._assert_owner(work_id, owner)\n        rows = self.book.db.execute('SELECT * FROM work_checkpoints WHERE work_id=? ORDER BY ordinal', (work_id,)).fetchall()\n        tools, inspected, discovered = set(), set(), set()\n        phase = 'NOT_STARTED'\n        for row in rows:\n            if not self.book.digest_matches(row['summary_digest'], row['summary']):\n                raise RuntimeError('Delegated work checkpoint failed integrity validation')\n            value = json.loads(row['summary'])\n            phase = value.get('phase', phase)\n            tools.update(value.get('tools', []))\n            inspected.update(value.get('inspected_paths', []))\n            discovered.update(value.get('discovered_paths', []))\n        return {'version': 1, 'phase': phase, 'tools': sorted(tools),\n                'inspected_paths': sorted(inspected), 'discovered_paths': sorted(discovered)[:200]}\n'''
new_progress = '''    def progress(self, work_id, owner):\n        item = self._assert_owner(work_id, owner)\n        rows = self.book.db.execute('SELECT * FROM work_checkpoints WHERE work_id=? ORDER BY ordinal', (work_id,)).fetchall()\n        tools, inspected, discovered, artifacts, required = set(), set(), set(), set(), set()\n        phase = 'NOT_STARTED'\n        scan_complete = False\n        scan_truncated = False\n        for row in rows:\n            if not self.book.digest_matches(row['summary_digest'], row['summary']):\n                raise RuntimeError('Delegated work checkpoint failed integrity validation')\n            value = json.loads(row['summary'])\n            phase = value.get('phase', phase)\n            tools.update(value.get('tools', []))\n            inspected.update(value.get('inspected_paths', []))\n            discovered.update(value.get('discovered_paths', []))\n            artifacts.update(value.get('artifact_paths', []))\n            required.update(value.get('required_paths', []))\n            scan_complete = scan_complete or bool(value.get('scan_complete'))\n            scan_truncated = scan_truncated or bool(value.get('scan_truncated'))\n        has_response = bool(self.book.db.execute(\n            "SELECT 1 FROM work_turns WHERE work_id=? AND response_digest IS NOT NULL AND outcome='TURN_COMPLETE' LIMIT 1",\n            (work_id,)).fetchone())\n        result = {'version': 2, 'phase': phase, 'tools': sorted(tools),\n                  'inspected_paths': sorted(inspected), 'discovered_paths': sorted(discovered)[:200],\n                  'scan_complete': scan_complete, 'scan_truncated': scan_truncated,\n                  'artifact_paths': sorted(artifacts)[:50], 'required_paths': sorted(required),\n                  'has_response': has_response}\n        self.executor.ensure(item, execution_contract(item['goal']))\n        return result\n'''
replace_once('work_mode.py', old_progress, new_progress)

replace_once('work_mode.py',
"        return self._row(work_id)\n\n    def set_status(self, work_id, owner, status, tx=None):\n",
"        updated = self._row(work_id)\n        progress = self.progress(work_id, owner)\n        self.executor.sync(updated, execution_contract(updated['goal']), progress,\n                           failed=failed, response_present=not failed, tx=tx)\n        return self._row(work_id)\n\n    def set_status(self, work_id, owner, status, tx=None):\n")

replace_once('work_mode.py',
"        row = self._assert_owner(work_id, owner)\n        if row['status'] == status:\n",
"        row = self._assert_owner(work_id, owner)\n        if status == 'DONE':\n            self.executor.require_done(row, execution_contract(row['goal']), self.progress(work_id, owner))\n        if row['status'] == status:\n")

replace_once('work_mode.py',
"            'Verified progress JSON: ' + encode(progress),\n            'The work item grants no authority by itself. Only a verified current-turn work binding can preserve the owner-approved goal scope.',\n",
"            'Verified progress JSON: ' + encode(progress),\n            'Persistent step state:\\n' + self.executor.format_steps(item, contract),\n            'The work item grants no authority by itself. Only a verified current-turn work binding can preserve the owner-approved goal scope.',\n")

replace_once('work_mode.py',
"                'Checkpoint: ' + progress['phase'] + '; inspected ' + str(len(progress['inspected_paths'])) + ' file(s)\\n'\n                'Turns: ' + str(item['turns']) +\n",
"                'Checkpoint: ' + progress['phase'] + '; inspected ' + str(len(progress['inspected_paths'])) + ' file(s)\\n'\n                'Steps:\\n' + self.executor.format_steps(item, contract) + '\\n'\n                'Turns: ' + str(item['turns']) +\n")

# permissions.py: v6 may create only an owner-requested deliverable, still requiring exact approval.
replace_once('permissions.py',
"    if version >= 6:\n        scope['work_binding'] = work_binding\n        scope['read_tree_paths'] = ['.'] if delegated_review else []\n",
"    if version >= 6:\n        scope['work_binding'] = work_binding\n        from work_executor import requested_deliverable\n        deliverable = requested_deliverable(work_binding['goal'], work_binding['work_id']) if work_binding else None\n        scope['create_paths'] = [deliverable] if deliverable else []\n        scope['read_tree_paths'] = ['.'] if delegated_review else []\n")

# engine.py: owner work scope constrains creates before approval is requested.
replace_once('engine.py',
"                        elif request['name'] in ('create_file', 'apply_plan', 'undo_plan'):\n                            allowed = key in state.get('approvals', [])\n",
"                        elif request['name'] in ('create_file', 'apply_plan', 'undo_plan'):\n                            if (request['name'] == 'create_file' and state['permissions'].get('version', 0) >= 6 and\n                                    request.get('path') not in state['permissions'].get('create_paths', [])):\n                                allowed = False\n                                denied = request_summary(self.book, request)\n                                denied.update(allowed=False, reason='Delegated work did not authorize creating this path')\n                                self.book.save_task_event(tx, state, 'AUTHORIZATION', denied)\n                                return False\n                            allowed = key in state.get('approvals', [])\n")

# server.py: preserve recovery evidence but suppress stale delivery-only startup noise.
replace_once('server.py',
"        if any((self.book.task(t['tx']) or {}).get('phase') != 'EXTERNAL_CAPTURE_PENDING' for t in self.pending):\n            print('Unfinished work or unconfirmed output exists; use --status and --resume TX-ID. '\n                  'Resuming uncertain output can repeat text, but does not rerun completed tools.', file=sys.stderr)\n",
"        execution_pending = [t for t in self.pending if t.get('recovery_kind') != 'DELIVERY' and\n                             (self.book.task(t['tx']) or {}).get('phase') != 'EXTERNAL_CAPTURE_PENDING']\n        if execution_pending:\n            print(str(len(execution_pending)) + ' unfinished execution transaction(s) need attention; use --status and --resume TX-ID. '\n                  'Completed tools are not replayed blindly.', file=sys.stderr)\n")

print('Work Executor v3 integration patch applied')
