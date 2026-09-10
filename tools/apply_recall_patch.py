#!/usr/bin/env python3
"""One-shot guarded patch for owner-directed Notebook recall on the feature branch."""
from pathlib import Path


def replace_once(path, old, new):
    p = Path(path)
    text = p.read_text(encoding='utf-8')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{path}: expected exactly one patch anchor, found {count}')
    p.write_text(text.replace(old, new), encoding='utf-8')


replace_once('capabilities.py',
"from copy import deepcopy\n\n\n",
"from copy import deepcopy\n\n\nHUMAN_ONLY = frozenset({'recall_notebook'})\n\n\n")

replace_once('capabilities.py',
"    definition('read_notebook', 'Read verified counts and a bounded transcript excerpt from the bound session.', 'current_session'),\n    definition('runtime_capabilities', 'Report this runtime capability registry.', 'runtime'),",
"    definition('read_notebook', 'Read verified counts and a bounded transcript excerpt from the bound session.', 'current_session'),\n    definition('recall_notebook', 'Search bounded authoritative Life Notebook transcript evidence across the owner’s sessions. Human-direct only.', 'notebook_global',\n               parameters={'query': {'type': 'string'}}, required=('query',)),\n    definition('runtime_capabilities', 'Report this runtime capability registry.', 'runtime'),")

replace_once('capabilities.py',
"    for spec in describe():\n        if not spec['available']:",
"    for spec in describe():\n        if spec['name'] in HUMAN_ONLY:\n            continue\n        if not spec['available']:")

replace_once('capabilities.py',
"            '\\n' + missing + ' are not connected. Use /files, /read PATH, /duplicates, /organize, '\n            '/understand PATH, /smart-organize, /organize-inbox, /apply PLAN-ID, /undo PLAN-ID, /source, /time, or /notebook.')",
"            '\\n' + missing + ' are not connected. Use /files, /read PATH, /duplicates, /organize, '\n            '/understand PATH, /smart-organize, /organize-inbox, /apply PLAN-ID, /undo PLAN-ID, /source, /time, /notebook, or /recall QUERY.')")

replace_once('permissions.py',
"def task_scope(row, workspace, version=3):",
"def task_scope(row, workspace, version=4):")

replace_once('permissions.py',
"    if version >= 3:\n        scope['contextual_paths'] = [direct.get('path', '.')] if direct.get('name') in (\n            'understand_file', 'plan_contextual_organization', 'plan_inbox_organization') else []\n    return scope",
"    if version >= 3:\n        scope['contextual_paths'] = [direct.get('path', '.')] if direct.get('name') in (\n            'understand_file', 'plan_contextual_organization', 'plan_inbox_organization') else []\n    if version >= 4:\n        scope['recall_request'] = direct if direct.get('name') == 'recall_notebook' else None\n    return scope")

replace_once('permissions.py',
"    if scope.get('version') not in (1, 2, 3):",
"    if scope.get('version') not in (1, 2, 3, 4):")

replace_once('permissions.py',
"    if name in ('understand_file', 'plan_contextual_organization', 'plan_inbox_organization'):\n        return request.get('path', '.') in scope.get('contextual_paths', [])\n    return name in scope['runtime_reads']",
"    if name in ('understand_file', 'plan_contextual_organization', 'plan_inbox_organization'):\n        return request.get('path', '.') in scope.get('contextual_paths', [])\n    if name == 'recall_notebook':\n        return scope.get('version', 0) >= 4 and request == scope.get('recall_request')\n    return name in scope['runtime_reads']")

replace_once('runtime_info.py',
"from capabilities import summary\n",
"from capabilities import summary\nfrom notebook_recall import format_recall, search_notebook\n")

replace_once('runtime_info.py',
"    except ValueError:\n        words = []\n    commands = {'/files': 'scan_files', '/duplicates': 'find_duplicates', '/organize': 'plan_organization',",
"    except ValueError:\n        words = []\n    if re.match(r'^\\s*/recall(?:\\s|$)', text):\n        if not words or words[0] != '/recall':\n            return {'name': 'recall_notebook', 'query': ''}\n        return {'name': 'recall_notebook', 'query': ' '.join(words[1:])}\n    commands = {'/files': 'scan_files', '/duplicates': 'find_duplicates', '/organize': 'plan_organization',")

replace_once('runtime_info.py',
"    elif name == 'runtime_capabilities':\n        result = summary()\n    elif name == 'read_notebook':",
"    elif name == 'runtime_capabilities':\n        result = summary()\n    elif name == 'recall_notebook':\n        state = book.task(tx) or {}\n        request = state.get('permissions', {}).get('recall_request')\n        if not isinstance(request, dict) or request.get('name') != 'recall_notebook':\n            raise PermissionError('Notebook recall requires the exact human-derived recall scope')\n        result = format_recall(search_notebook(book, identity['owner'], tx, request.get('query', '')))\n    elif name == 'read_notebook':")

print('Recall patch applied with all guarded anchors matched exactly.')
