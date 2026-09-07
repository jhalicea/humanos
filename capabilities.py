"""Single supported-tool contract used by the executor, model, and human UI."""
from copy import deepcopy


def definition(name, description, scope, effect='read', parameters=None, required=(), available=True):
    return {'name': name, 'description': description, 'scope': scope, 'effect': effect,
            'available': available, 'parameters': {'type': 'object', 'properties': parameters or {},
            'required': list(required), 'additionalProperties': False}}


REGISTRY = {item['name']: item for item in (
    definition('read_file', 'Read an explicitly requested workspace file (16 KiB maximum).', 'workspace',
               parameters={'path': {'type': 'string'}}, required=('path',)),
    definition('list_files', 'List an authorized workspace directory.', 'workspace',
               parameters={'path': {'type': 'string', 'default': '.'}}),
    definition('create_file', 'Create a new workspace file after exact-request approval; never overwrite.',
               'workspace', 'create', {'path': {'type': 'string'}, 'content': {'type': 'string'}}, ('path', 'content')),
    definition('current_time', 'Read the Mac local date/time and UTC offset.', 'local_clock'),
    definition('read_notebook', 'Read verified counts and a bounded transcript excerpt from the bound session.', 'current_session'),
    definition('runtime_capabilities', 'Report this runtime capability registry.', 'runtime'),
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
        if name in result and not isinstance(result[name], str):
            raise PermissionError('Tool argument must be text: ' + name)
    return result


def model_instructions():
    from notebook import encode
    lines = ['Available tools and valid JSON examples. Put arguments directly beside name; '
             'never wrap them in parameters or arguments. The registry lists tools, not workspace files.']
    examples = {'path': 'example.txt', 'content': 'text'}
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
    return ('HumanOS uses the configured local model for conversation. Available capabilities:\n' + supported +
            '\n' + missing + ' are not connected. Use /time, /notebook, or /capabilities.')
