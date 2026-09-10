from pathlib import Path


def replace(path, old, new, count=1):
    p = Path(path)
    text = p.read_text()
    actual = text.count(old)
    if actual != count:
        raise SystemExit(f'{path}: expected {count} matches, found {actual}: {old[:80]!r}')
    p.write_text(text.replace(old, new))


# Agent accepts a verified work binding and persists a v6 scope derived from the
# exact current human input plus the integrity-checked original delegated goal.
replace('engine.py',
"    def run(self, tx, hcid=None, user_input=None, context=(), reference_binding=None):\n",
"    def run(self, tx, hcid=None, user_input=None, context=(), reference_binding=None, work_binding=None):\n")
replace('engine.py',
"            if not state:\n                packet = load_context(self.core, context)\n",
"            if not state:\n                if work_binding is not None:\n                    from work_mode import validate_work_binding\n                    validate_work_binding(self.book, work_binding, row['hcid'], row['input'])\n                packet = load_context(self.core, context)\n")
replace('engine.py',
"                         'permissions': task_scope(row, self.tools.workspace,\n                                                   version=5 if reference_binding else 4,\n                                                   reference_binding=reference_binding),\n                         'reference_binding': reference_binding, 'approvals': []}\n",
"                         'permissions': task_scope(row, self.tools.workspace,\n                                                   version=6 if work_binding else (5 if reference_binding else 4),\n                                                   reference_binding=reference_binding, work_binding=work_binding),\n                         'reference_binding': reference_binding, 'work_binding': work_binding, 'approvals': []}\n")
replace('engine.py',
"            if state['model'] != self.model.name or state['workspace'] != str(self.tools.workspace):\n",
"            if work_binding is not None and state.get('work_binding') != work_binding:\n                raise PermissionError('Delegated work binding differs from preserved task state')\n            if state['model'] != self.model.name or state['workspace'] != str(self.tools.workspace):\n")

# Work start, continue and crash-resume all carry the binding for the exact
# work_turn row. Ordinary chat continues to call Agent without a work binding.
replace('server.py',
"            response = agent.run(args.resume)\n",
"            response = agent.run(args.resume, work_binding=work.binding_for_tx(args.resume) if item else None)\n")
replace('server.py',
"                        response = agent.run(tx)\n",
"                        response = agent.run(tx, work_binding=self.work.binding_for_tx(tx))\n",
count=2)

# Scope v6 distinguishes broad workspace review from explicit-file review.
old = """    delegated_review = False
    if version >= 6 and work_binding:
        delegated_review = bool(
            re.search(r'\\b(review|analyse|analyze|audit|inspect|check|assess|summari[sz]e|understand)\\w*\\b', text, re.I)
            and re.search(r'\\b(files?|workspace|folders?|director(?:y|ies))\\b', text, re.I))
        if delegated_review:
            file_read = True
            listing = True
"""
new = """    delegated_review = False
    delegated_file_review = False
    if version >= 6 and work_binding:
        from work_mode import execution_contract
        contract = execution_contract(work_binding['goal'])
        delegated_review = contract.get('kind') == 'workspace_review'
        delegated_file_review = contract.get('kind') == 'file_review'
        if delegated_review:
            file_read = True
            listing = True
        if delegated_file_review:
            file_read = True
            paths.extend(contract.get('required_paths', []))
"""
replace('permissions.py', old, new)
replace('permissions.py',
"        file_read = listing = delegated_review = False\n",
"        file_read = listing = delegated_review = delegated_file_review = False\n")

# Stop after a bounded inspection batch. Remaining files stay explicitly pending
# for the next continue turn instead of exhausting the agent loop or pretending
# the whole workspace was reviewed.
old = """            remaining = [path for path in paths if path not in previously and path not in current]
            if remaining:
                return {'name': 'read_file', 'path': remaining[0]}, {
                    'visible_text_files': len(paths),
                    'already_inspected': len(previously | current),
                    'remaining': len(remaining)}
            return None, {'visible_text_files': len(paths), 'already_inspected': len(previously | current), 'remaining': 0}
"""
new = """            remaining = [path for path in paths if path not in previously and path not in current]
            current_reads = len([request for request, _ in evidence if request.get('name') == 'read_file'])
            limit = int(self.contract.get('inspect_limit', MAX_INSPECTIONS_PER_TURN))
            if remaining and current_reads < limit:
                return {'name': 'read_file', 'path': remaining[0]}, {
                    'visible_text_files': len(paths),
                    'already_inspected': len(previously | current),
                    'remaining': len(remaining)}
            return None, {'visible_text_files': len(paths),
                          'already_inspected': len(previously | current),
                          'remaining': len(remaining)}
"""
replace('work_mode.py', old, new)
old = """            if self.contract['kind'] == 'workspace_review':
                final += ('\\n\\nWork checkpoint: verified workspace scan completed; '
                          + str(checkpoint.get('already_inspected', 0)) + ' text file(s) inspected in this work history.')
"""
new = """            if self.contract['kind'] == 'workspace_review':
                remaining = int(checkpoint.get('remaining', 0))
                final += ('\\n\\nWork checkpoint: verified workspace scan completed; '
                          + str(checkpoint.get('already_inspected', 0)) + ' text file(s) inspected in this work history.')
                if remaining:
                    final += (' ' + str(remaining) + ' visible text file(s) remain; this is not a complete workspace review. '
                              'Use continue that work for the next verified batch.')
"""
replace('work_mode.py', old, new)

# Retry marker: focused tests now run with tests/ on PYTHONPATH.
