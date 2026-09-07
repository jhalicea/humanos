"""Versioned task scope derived from human input, never from model output."""
import re
import shlex
from notebook import digest


def task_scope(row, workspace):
    text = row['input']
    try:
        tokens = shlex.split(text)
    except ValueError:
        tokens = text.split()
    paths = []
    for index, token in enumerate(tokens):
        value = token.strip('.,!?;:`\"\'')
        previous = tokens[index - 1].casefold() if index else ''
        if value and ('.' in value or '/' in value or previous in ('read', 'open', 'inspect', 'view', 'cat')):
            paths.append(value)
    file_read = bool(re.search(r'\b(read|open|inspect|show|view|cat)\b', text, re.I))
    listing = bool(re.search(r'\b(list|files|workspace|folder|directory)\b', text, re.I))
    # A filename mentioned in an exclusion is not consent. Mixed/negative
    # requests require a simpler affirmative request instead of guessing scope.
    if re.search(r"\b(not|never|avoid|except|without|exclude|excluding|don't|don’t)\b", text, re.I):
        file_read = listing = False
    return {'version': 1, 'tx': row['tx'], 'hcid': row['hcid'],
            'input_sha256': digest(text), 'workspace': str(workspace),
            'read_paths': sorted(set(paths)) if file_read else [],
            'list_paths': ['.'] + sorted(set(paths)) if listing else [],
            'runtime_reads': ['current_time', 'read_notebook', 'runtime_capabilities'],
            'writes': 'EXACT_REQUEST_APPROVAL'}


def validate_scope(scope, row, workspace):
    # The source input remains immutable. Reject altered/unsupported saved policy;
    # do not silently widen a task when implementation defaults change.
    expected = task_scope(row, workspace)
    if scope != expected:
        raise PermissionError('Saved task permission scope differs; explicit reconciliation required')


def allows_read(scope, request):
    name = request.get('name')
    if name == 'read_file':
        return request.get('path') in scope['read_paths']
    if name == 'list_files':
        return request.get('path', '.') in scope['list_paths']
    return name in scope['runtime_reads']
