"""HumanOS browser broker protocol and native-host transport.

The browser extension is a capability adapter.  It does not decide which
actions are allowed and it never receives the control-plane secret.  A local
broker owns the secret and speaks to the native host over an owner-only Unix
socket.  The native host forwards only broker-authenticated commands to the
extension's native-messaging port.
"""
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import socket
import stat
import struct
import time
from swarm import Ledger


TOOLS = frozenset({'inspect', 'navigate', 'click', 'type', 'scroll', 'screenshot', 'download'})
READ_ONLY = frozenset({'inspect', 'screenshot'})
RISKY = frozenset({'navigate', 'click', 'type', 'download'})
MAX_FRAME = 1_048_576


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def exact(value, names):
    if not isinstance(value, dict) or set(value) != set(names.split()):
        raise ValueError('Unexpected or missing fields')


def bounded_text(value, maximum, name):
    if not isinstance(value, str) or not value or len(value.encode()) > maximum:
        raise ValueError(name + ' must be nonempty bounded text')


def valid_url(value, allowlist):
    bounded_text(value, 4096, 'url')
    from urllib.parse import urlparse
    parsed = urlparse(value)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise PermissionError('Only clean HTTPS URLs are allowed')
    host = parsed.hostname.lower().rstrip('.')
    if host not in allowlist and not any(host.endswith('.' + item) for item in allowlist):
        raise PermissionError('URL host is outside the immutable allowlist')


class BrowserEnvelope:
    """Immutable run authority; an action is always scoped to one active tab."""
    def __init__(self, data):
        exact(data, 'run_id authorization expires hosts capabilities max_actions max_bytes')
        bounded_text(data['run_id'], 128, 'run_id')
        bounded_text(data['authorization'], 2048, 'authorization')
        if type(data['expires']) is not int or data['expires'] <= int(time.time()):
            raise ValueError('A future authorization expiry is required')
        if not isinstance(data['hosts'], list) or not data['hosts']:
            raise ValueError('A nonempty host allowlist is required')
        if any(not isinstance(host, str) or not host or '/' in host for host in data['hosts']):
            raise ValueError('Invalid host allowlist')
        if not isinstance(data['capabilities'], list) or not set(data['capabilities']) <= TOOLS:
            raise ValueError('Invalid browser capabilities')
        if type(data['max_actions']) is not int or not 1 <= data['max_actions'] <= 10000:
            raise ValueError('Invalid action budget')
        if type(data['max_bytes']) is not int or not 0 <= data['max_bytes'] <= MAX_FRAME:
            raise ValueError('Invalid byte budget')
        self.data = json.loads(canonical(data))


class BrowserBroker:
    """Policy boundary for a powerful but bounded browser tool set.

    `approve` is only called for side effects.  A user interface can provide a
    visible confirmation implementation; tests use a deterministic callback.
    """
    def __init__(self, envelope, state_dir, send, approve=None, clock=time.time):
        self.envelope = BrowserEnvelope(envelope)
        self.state = Path(state_dir).resolve()
        self.state.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(self.state, 0o700)
        if self.state.is_symlink() or stat.S_IMODE(self.state.stat().st_mode) != 0o700:
            raise PermissionError('Browser state directory must be owner-only')
        self.send, self.approve, self.clock = send, approve or (lambda _: False), clock
        self.actions = 0
        self.bytes = 0
        self.stopped = False
        self.ledger = Ledger(self.state / 'ledger')

    def stop(self):
        self.stopped = True
        self._record({'kind': 'STOP', 'time': self.clock()})

    def execute(self, request):
        # Canonical roundtrip prevents model-created Python objects crossing the boundary.
        request = json.loads(canonical(request))
        request_bytes = len(canonical(request).encode())
        self.actions += 1
        self.bytes += request_bytes
        event = {'kind': 'ATTEMPT', 'time': self.clock(), 'run_id': self.envelope.data['run_id'], 'request': request}
        self._record(event)
        try:
            if self.stopped:
                raise PermissionError('Browser kill switch is active')
            if self.clock() >= self.envelope.data['expires']:
                raise PermissionError('Browser authorization window expired')
            if self.actions > self.envelope.data['max_actions'] or self.bytes > self.envelope.data['max_bytes']:
                raise PermissionError('Browser budget exhausted')
            exact(request, 'tool tab_id arguments')
            if request['tool'] not in self.envelope.data['capabilities']:
                raise PermissionError('Browser capability not granted')
            if type(request['tab_id']) is not int or request['tab_id'] < 0:
                raise ValueError('Active tab id required')
            self._validate(request)
            if request['tool'] in RISKY and not self.approve({'authorization': self.envelope.data['authorization'], **request}):
                raise PermissionError('Human browser approval required')
            observation = self.send(request)
            result = {'ok': True, 'observation': observation}
        except (PermissionError, ValueError, TypeError, OSError) as error:
            result = {'ok': False, 'error': str(error)}
        self._record({'kind': 'RESULT', 'time': self.clock(), 'run_id': self.envelope.data['run_id'], 'result': result})
        return result

    def _validate(self, request):
        tool, args = request['tool'], request['arguments']
        if tool in ('inspect', 'screenshot'):
            exact(args, '')
        elif tool == 'navigate':
            exact(args, 'url'); valid_url(args['url'], self.envelope.data['hosts'])
        elif tool == 'click':
            exact(args, 'selector')
            bounded_text(args['selector'], 512, 'selector')
        elif tool == 'type':
            exact(args, 'selector text')
            bounded_text(args['selector'], 512, 'selector')
            bounded_text(args['text'], 16384, 'text')
        elif tool == 'scroll':
            exact(args, 'x y')
            if type(args['x']) is not int or type(args['y']) is not int or abs(args['x']) > 10000 or abs(args['y']) > 10000:
                raise ValueError('Invalid scroll distance')
        elif tool == 'download':
            exact(args, 'url')
            valid_url(args['url'], self.envelope.data['hosts'])

    def _record(self, event):
        # This is an independent keyed, fsync'd chain and head. It detects
        # truncation/edits while the control directory's key and head survive.
        self.ledger.append(event)


def native_read(stream):
    size = stream.read(4)
    if len(size) != 4:
        raise EOFError()
    length = struct.unpack('<I', size)[0]
    if length > MAX_FRAME:
        raise ValueError('Oversize native message')
    raw = stream.read(length)
    if len(raw) != length:
        raise EOFError()
    return json.loads(raw)


def native_write(stream, message):
    raw = canonical(message).encode()
    if len(raw) > MAX_FRAME:
        raise ValueError('Oversize native message')
    stream.write(struct.pack('<I', len(raw)) + raw); stream.flush()


class NativeBridge:
    """One extension port plus one authenticated owner-only Unix socket."""
    def __init__(self, socket_path, secret_path, extension_in, extension_out):
        self.socket_path = Path(socket_path)
        self.secret_path = Path(secret_path)
        self.extension_in, self.extension_out = extension_in, extension_out
        if self.secret_path.exists():
            self.secret = self.secret_path.read_bytes()
        else:
            self.secret_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            self.secret = secrets.token_bytes(32)
            fd = os.open(self.secret_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.write(fd, self.secret); os.close(fd)
        if len(self.secret) != 32:
            raise PermissionError('Invalid browser bridge secret')

    def serve_once(self, connection):
        raw = connection.recv(MAX_FRAME)
        message = json.loads(raw)
        exact(message, 'request mac')
        expected = hmac.new(self.secret, canonical(message['request']).encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, message['mac']):
            raise PermissionError('Unauthenticated browser broker request')
        native_write(self.extension_out, message['request'])
        response = native_read(self.extension_in)
        connection.sendall(canonical(response).encode())


def bridge_sender(socket_path, secret_path):
    """Build the broker's only transport function; no browser socket reaches a model."""
    secret = Path(secret_path).read_bytes()
    def send(request):
        mac = hmac.new(secret, canonical(request).encode(), hashlib.sha256).hexdigest()
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(str(socket_path))
            client.sendall(canonical({'request': request, 'mac': mac}).encode())
            raw = client.recv(MAX_FRAME)
        return json.loads(raw)
    return send
