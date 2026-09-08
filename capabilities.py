"""Single supported-tool contract used by the executor, model, and human UI."""
from copy import deepcopy


def definition(name, description, scope, effect='read', parameters=None, required=(), available=True):
    return {'name': name, 'description': description, 'scope': scope, 'effect': effect,
            'available': available, 'parameters': {'type': 'object', 'properties': parameters or {},
            'required': list(required), 'additionalProperties': False}}


REGISTRY = {item['name']: item for item in (
    definition('read_file', 'Read a page of an explicitly requested UTF-8 workspace file (16 KiB per page).', 'workspace',
               parameters={'path': {'type': 'string'}, 'offset': {'type': 'integer'}}, required=('path',)),
    definition('list_files', 'List an authorized workspace directory.', 'workspace',
               parameters={'path': {'type': 'string', 'default': '.'}}),
    definition('create_file', 'Create a new workspace file after exact-request approval; never overwrite.',
               'workspace', 'create', {'path': {'type': 'string'}, 'content': {'type': 'string'}}, ('path', 'content')),
    definition('current_time', 'Read the Mac local date/time and UTC offset.', 'local_clock'),
    definition('read_notebook', 'Read verified counts and a bounded transcript excerpt from the bound session.', 'current_session'),
    definition('runtime_capabilities', 'Report this runtime capability registry.', 'runtime'),
    definition('read_source', 'Read allowlisted HumanOS source code, separate from workspace files.', 'source',
               parameters={'path': {'type': 'string', 'default': 'server.py'}, 'offset': {'type': 'integer', 'default': 0}}),
    definition('scan_files', 'List the folder tree with file sizes; bounded scan, no symlinks or hidden files.', 'workspace',
               parameters={'path': {'type': 'string', 'default': '.'}}),
    definition('find_duplicates', 'Find exact-content duplicate files; report only, never delete.', 'workspace',
               parameters={'path': {'type': 'string', 'default': '.'}}),
    definition('plan_organization', 'Preview a reversible organization plan by file type without moving files.', 'workspace', 'plan',
               parameters={'path': {'type': 'string', 'default': '.'}}),
    definition('understand_file', 'Understand one selected file from a bounded local excerpt and suggest a folder; nothing moves.', 'workspace',
               parameters={'path': {'type': 'string'}}, required=('path',)),
    definition('plan_contextual_organization', 'Preview organization by local content and context with reasons; nothing moves until separately approved.', 'workspace', 'plan',
               parameters={'path': {'type': 'string', 'default': '.'}}),
    definition('plan_inbox_organization', 'Preview inbox classification, destination, and clearer filename suggestions; nothing moves until separately approved.', 'workspace', 'plan',
               parameters={'path': {'type': 'string', 'default': 'inbox'}}),
    definition('plan_move', 'Preview moving a file or folder within the authorized workspace.', 'workspace', 'plan',
               parameters={'source': {'type': 'string'}, 'destination': {'type': 'string'}}, required=('source', 'destination')),
    definition('apply_plan', 'Apply a specific saved organization plan only after human approval of its moves.', 'workspace', 'organize',
               parameters={'plan_id': {'type': 'string'}}, required=('plan_id',)),
    definition('undo_plan', 'Undo a specific organization plan without overwriting changed files; approval required.', 'workspace', 'organize',
               parameters={'plan_id': {'type': 'string'}}, required=('plan_id',)),
    definition('internet_search', 'Internet search', 'public_web', 'network_read', available=False),
    definition('drive_sync', 'Drive synchronization', 'canonical_store', 'sync', available=False),
)}


def describe():
    return deepcopy(list(REGISTRY.values()))


def validate_request(request):
    if not isinstance(request, dict) or not isinstance(request.get('name'), str):
        raise PermissionError('Tool request must have a name')
    spec = REGISTRY.get(request['name'])
    if not spec or not spec['available']:
        raise PermissionError('Tool is unknown or unavailable')
    schema = spec['parameters']
    if set(request) - {'name'} - set(schema['properties']):
        raise PermissionError('Unexpected tool arguments')
    if not set(schema['required']).issubset(request):
        raise PermissionError('Required tool argument missing')
    result = dict(request)
    for name, prop in schema['properties'].items():
        if name not in result and 'default' in prop:
            result[name] = prop['default']
        if name in result:
            expected = int if prop['type'] == 'integer' else str
            if not isinstance(result[name], expected) or isinstance(result[name], bool):
                raise PermissionError('Invalid type for tool argument: ' + name)
            if expected is int and not 0 <= result[name] <= 16777216:
                raise PermissionError('Offset is outside the allowed range')
    return result


def model_instructions():
    from notebook import encode
    lines = ['Available tools and valid JSON examples. Put arguments directly beside name; '
             'never wrap them in parameters or arguments. The registry lists tools, not workspace files.']
    examples = {'path': 'example.txt', 'content': 'text', 'source': 'example.txt',
                'destination': 'Documents/example.txt', 'plan_id': 'ID returned by plan tool', 'offset': 0}
    for spec in describe():
        if not spec['available']:
            lines.append(spec['name'] + ': unavailable; no executor connected.')
            continue
        request = {'name': spec['name']}
        for key, prop in spec['parameters']['properties'].items():
            request[key] = prop.get('default', examples[key])
        lines.append(spec['description'] + '\n' + encode({'tool': request}))
    lines.append('For a final answer: {"final":"answer"}. Return exactly one JSON object.')
    return '\n'.join(lines)


def summary():
    supported = '\n'.join('- ' + item['name'] + ': ' + item['description'] for item in describe() if item['available'])
    missing = ', '.join(item['description'] for item in describe() if not item['available'])
    return ('I’m Mirror, the human-facing interface of HumanOS. I can help with conversation and planning, '
            'read files, inspect folders, understand local file context, find exact duplicates, and organize files using a reviewed plan. '
            'File access stays inside the folder you select. Duplicate checks never delete files.\n' + supported +
            '\n' + missing + ' are not connected. Use /files, /read PATH, /duplicates, /organize, '
            '/understand PATH, /smart-organize, /organize-inbox, /apply PLAN-ID, /undo PLAN-ID, /source, /time, or /notebook.')
