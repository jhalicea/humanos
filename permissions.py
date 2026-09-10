"""Versioned task scope derived from human input and verified human bindings."""
import re
import shlex
from notebook import digest
from references import validate_reference_binding


def _safe_relative(path):
    if not isinstance(path, str) or not path or path.startswith('/'):
        return False
    parts = path.split('/')
    return all(part not in ('', '.', '..') and not part.startswith('.') for part in parts)


def _scope_text(row, work_binding=None):
    text = row['input']
    if work_binding:
        # The preserved goal is authoritative only after validate_scope verifies
        # the binding against the owner-selected work turn in the Notebook.
        text += '\n' + work_binding['goal']
    return text


def task_scope(row, workspace, version=4, reference_binding=None, work_binding=None):
    text = _scope_text(row, work_binding if version >= 6 else None)
    try:
        tokens = shlex.split(text)
    except ValueError:
        tokens = text.split()
    paths = []
    for index, token in enumerate(tokens):
        value = token.strip('.,!?;:`\"\'')
        previous = tokens[index - 1].casefold() if index else ''
        deictic = value.casefold() in ('it', 'that', 'this', 'file', 'one', 'the')
        if value and not deictic and ('.' in value or '/' in value or previous in ('read', 'open', 'inspect', 'view', 'cat')):
            paths.append(value)
    if version >= 5 and reference_binding and reference_binding.get('kind', 'file') == 'file':
        paths.append(reference_binding['path'])

    file_read = bool(re.search(r'\b(read|open|inspect|show|view|cat)\b', text, re.I))
    listing = bool(re.search(r'\b(list|files|workspace|folder|directory)\b', text, re.I))
    delegated_review = False
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

    # A filename mentioned in an exclusion is not consent. Mixed/negative
    # requests require a simpler affirmative request instead of guessing scope.
    if re.search(r"\b(not|never|avoid|except|without|exclude|excluding|don't|don’t)\b", text, re.I):
        file_read = listing = delegated_review = delegated_file_review = False

    scope = {'version': version, 'tx': row['tx'], 'hcid': row['hcid'],
            'input_sha256': digest(row['input']), 'workspace': str(workspace),
            'read_paths': sorted(set(paths)) if file_read else [],
            'list_paths': ['.'] + sorted(set(paths)) if listing else [],
            'runtime_reads': ['current_time', 'read_notebook', 'runtime_capabilities'],
            'browser_enabled': bool(re.search(r'\bbrowser\b', text, re.I)),
            'writes': 'EXACT_REQUEST_APPROVAL'}
    if version >= 2:
        from runtime_info import request_for
        direct = request_for(row['input'], [], reference_binding=reference_binding) or {}
        scope['source_paths'] = [direct.get('path', 'server.py')] if direct.get('name') == 'read_source' else []
        scope['scan_paths'] = [direct.get('path', '.')] if direct.get('name') in (
            'scan_files', 'find_duplicates', 'plan_organization') else []
        scope['move_request'] = direct if direct.get('name') == 'plan_move' else None
        scope['plan_action'] = direct if direct.get('name') in ('apply_plan', 'undo_plan') else None
    if version >= 3:
        scope['contextual_paths'] = [direct.get('path', '.')] if direct.get('name') in (
            'understand_file', 'plan_contextual_organization', 'plan_inbox_organization') else []
    if version >= 4:
        scope['recall_request'] = direct if direct.get('name') == 'recall_notebook' else None
    if version >= 5:
        scope['reference_binding'] = reference_binding
    if version >= 6:
        scope['work_binding'] = work_binding
        from work_executor import requested_deliverable
        deliverable = requested_deliverable(work_binding['goal'], work_binding['work_id']) if work_binding else None
        scope['create_paths'] = [deliverable] if deliverable else []
        scope['read_tree_paths'] = ['.'] if delegated_review else []
        if delegated_review and '.' not in scope.get('scan_paths', []):
            scope.setdefault('scan_paths', []).append('.')
            scope['scan_paths'] = sorted(set(scope['scan_paths']))
    return scope


def validate_scope(scope, row, workspace, book=None):
    # The source input remains immutable. Reject altered/unsupported saved policy;
    # do not silently widen a task when implementation defaults change.
    if scope.get('version') not in (1, 2, 3, 4, 5, 6):
        raise PermissionError('Unsupported saved task policy version')
    reference_binding = scope.get('reference_binding') if scope.get('version', 0) >= 5 else None
    if reference_binding:
        if book is None:
            raise PermissionError('Reference-bound scope requires Notebook verification')
        validate_reference_binding(book, reference_binding, row['hcid'], row['input'])
    work_binding = scope.get('work_binding') if scope.get('version', 0) >= 6 else None
    if work_binding:
        if book is None:
            raise PermissionError('Delegated work scope requires Notebook verification')
        from work_mode import validate_work_binding
        validate_work_binding(book, work_binding, row['hcid'], row['input'])
    expected = task_scope(row, workspace, scope['version'],
                          reference_binding=reference_binding, work_binding=work_binding)
    if scope != expected:
        raise PermissionError('Saved task permission scope differs; explicit reconciliation required')


def allows_read(scope, request):
    name = request.get('name')
    if name == 'browser_inspect':
        return scope.get('browser_enabled', False)
    if name == 'read_file':
        path = request.get('path')
        if path in scope['read_paths']:
            return True
        return bool(scope.get('version', 0) >= 6 and scope.get('read_tree_paths') and _safe_relative(path))
    if name == 'list_files':
        return request.get('path', '.') in scope['list_paths']
    if name == 'read_source':
        return request.get('path', 'server.py') in scope.get('source_paths', [])
    if name in ('scan_files', 'find_duplicates', 'plan_organization'):
        return request.get('path', '.') in scope.get('scan_paths', [])
    if name == 'plan_move':
        return request == scope.get('move_request')
    if name in ('understand_file', 'plan_contextual_organization', 'plan_inbox_organization'):
        return request.get('path', '.') in scope.get('contextual_paths', [])
    if name == 'recall_notebook':
        return scope.get('version', 0) >= 4 and request == scope.get('recall_request')
    return name in scope['runtime_reads']
