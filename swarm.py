"""Owner-controlled, data-only swarm tool broker. No agent code runs here.

The trust boundary is JSON proposals, not a Python sandbox. Run only this fixed
broker with trusted code; never give agent programs access to its OS account.
"""
import fcntl
import hashlib
import hmac
import ipaddress
import json
import os
from pathlib import Path
import secrets
import socket
import stat
import sys
import threading
import time

PROFILE = 'AUTHORIZED_RED_TEAM_SWARM'
STOPS = frozenset({'ambiguous_scope', 'unexpected_privilege', 'high_impact',
                   'scope_escape', 'operator_stop'})
TOOLS = frozenset({'tcp_probe', 'send_message', 'receive_messages'})


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def exact(value, keys):
    if not isinstance(value, dict) or set(value) != set(keys.split()):
        raise ValueError('Unexpected or missing fields')


def nonempty(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 1024:
        raise ValueError('Nonempty bounded text required')


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('Integer outside permitted range')


def validate(config):
    exact(config, 'profile envelope agents')
    if config['profile'] != PROFILE:
        raise ValueError('Unknown swarm profile')
    e = config['envelope']
    exact(e, 'run_id targets authorization not_before expires permitted_impact stop_conditions max_actions max_message_bytes')
    nonempty(e['run_id'])
    a = e['authorization']
    exact(a, 'human reference provenance_sha256 owner_attested environment')
    for key in ('human', 'reference'):
        nonempty(a[key])
    if a['owner_attested'] is not True or a['environment'] not in ('owned_system', 'authorized_lab', 'ctf'):
        raise ValueError('Explicit owner authorization required')
    if not isinstance(a['provenance_sha256'], str) or len(a['provenance_sha256']) != 64:
        raise ValueError('Authorization evidence SHA-256 required')
    int(a['provenance_sha256'], 16)
    for key in ('not_before', 'expires'):
        integer(e[key], 0, 2**53)
    if e['expires'] <= e['not_before']:
        raise ValueError('Invalid time window')
    if e['permitted_impact'] != 'connect_only' or not isinstance(e['stop_conditions'], list) or set(e['stop_conditions']) != STOPS:
        raise ValueError('Only connect_only impact and mandatory stop conditions supported')
    integer(e['max_actions'], 1, 100000)
    integer(e['max_message_bytes'], 0, 10000000)
    if not isinstance(e['targets'], list) or not e['targets']:
        raise ValueError('Exact target allowlist required')
    targets = set()
    for t in e['targets']:
        exact(t, 'ip port')
        if not isinstance(t['ip'], str) or str(ipaddress.ip_address(t['ip'])) != t['ip'] or '%' in t['ip']:
            raise ValueError('Canonical literal IP required; DNS and zones forbidden')
        integer(t['port'], 1, 65535)
        pair = (t['ip'], t['port'])
        if pair in targets:
            raise ValueError('Duplicate target')
        targets.add(pair)
    if not isinstance(config['agents'], list) or not config['agents']:
        raise ValueError('Agent manifests required')
    ids, tokens = set(), set()
    for m in config['agents']:
        exact(m, 'agent_id model version task capabilities peers token')
        for key in ('agent_id', 'model', 'version', 'task', 'token'):
            nonempty(m[key])
        if len(m['token']) < 32 or m['token'] in tokens or m['agent_id'] in ids:
            raise ValueError('Unique identities and strong independent tokens required')
        ids.add(m['agent_id']); tokens.add(m['token'])
        if not isinstance(m['capabilities'], list) or not set(m['capabilities']) <= TOOLS:
            raise ValueError('Unknown capabilities')
        if not isinstance(m['peers'], list) or any(not isinstance(p, str) for p in m['peers']):
            raise ValueError('Declared peers required')
    for m in config['agents']:
        if not set(m['peers']) <= ids or m['agent_id'] in m['peers']:
            raise ValueError('Invalid peer route')


class Ledger:
    """Fsync append + keyed chain + separately persisted head; uncertainty stops.

    Protects against untrusted proposal access and detects edits/truncation while
    trusted key/head remain intact. Not resistant to a compromised host owner.
    """
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.root.is_symlink() or self.root.resolve() != self.root.absolute():
            raise PermissionError('Control directory must be a canonical non-symlink path')
        s = self.root.stat()
        if s.st_uid != os.getuid() or stat.S_IMODE(s.st_mode) != 0o700:
            raise PermissionError('Control directory must be owner-only (0700)')
        self.lock = self.open('lock', os.O_RDWR | os.O_CREAT)
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            names = [self.root / n for n in ('key', 'actions.jsonl', 'head')]
            if not any(p.exists() for p in names):
                self.write_new('key', secrets.token_bytes(32))
                self.write_new('actions.jsonl', b'')
                self.write_new('head', b'0' * 64)
            self.key = self.read('key')
            if len(self.key) != 32:
                raise PermissionError('Invalid ledger key')
            self.records = self.verify()
        except BaseException:
            self.close()
            raise

    def open(self, name, flags):
        fd = os.open(self.root / name, flags | os.O_NOFOLLOW, 0o600)
        s = os.fstat(fd)
        if not stat.S_ISREG(s.st_mode) or s.st_nlink != 1 or s.st_uid != os.getuid() or stat.S_IMODE(s.st_mode) != 0o600:
            os.close(fd)
            raise PermissionError('Unsafe control file')
        return fd

    def read(self, name):
        with os.fdopen(self.open(name, os.O_RDONLY), 'rb') as f:
            return f.read()

    def write_new(self, name, value):
        with os.fdopen(self.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL), 'wb') as f:
            f.write(value); f.flush(); os.fsync(f.fileno())

    def verify(self):
        previous, records = '0' * 64, []
        for line in self.read('actions.jsonl').splitlines():
            row = json.loads(line)
            exact(row, 'event mac')
            event = row['event']
            if event['seq'] != len(records) or event['previous'] != previous:
                raise PermissionError('Ledger sequence mismatch')
            signature = hmac.new(self.key, encode(event).encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, row['mac']):
                raise PermissionError('Ledger authentication failed')
            records.append(row); previous = signature
        if self.read('head').decode() != previous:
            raise PermissionError('Ledger head mismatch; reconciliation required')
        return records

    def append(self, payload):
        records = self.verify()
        event = dict(payload, seq=len(records), previous=records[-1]['mac'] if records else '0' * 64)
        signature = hmac.new(self.key, encode(event).encode(), hashlib.sha256).hexdigest()
        row = {'event': event, 'mac': signature}
        with os.fdopen(self.open('actions.jsonl', os.O_WRONLY | os.O_APPEND), 'ab') as f:
            f.write((encode(row) + '\n').encode()); f.flush(); os.fsync(f.fileno())
        # A crash between append and head update fails closed on restart.
        with os.fdopen(self.open('head', os.O_WRONLY | os.O_TRUNC), 'wb') as f:
            f.write(signature.encode()); f.flush(); os.fsync(f.fileno())
        self.records = self.verify()

    def close(self):
        if self.lock is not None:
            os.close(self.lock); self.lock = None


class ControlPlane:
    def __init__(self, config, state_dir):
        config = json.loads(encode(config))  # detach caller-owned mutable inputs
        validate(config)
        self._config = encode(config)
        self._mutex = threading.Lock()
        self._killed = threading.Event()
        self.ledger = Ledger(state_dir)
        fingerprint = hashlib.sha256(self._config.encode()).hexdigest()
        try:
            events = [r['event'] for r in self.ledger.records]
            if events and events[0].get('config_sha256') != fingerprint:
                raise PermissionError('Immutable run configuration differs')
            if not events:
                self.ledger.append({'kind': 'RUN', 'config_sha256': fingerprint,
                                    'profile': PROFILE, 'envelope': config['envelope']})
            self._used = sum(e['kind'] == 'ATTEMPT' for e in events)
            self._bytes = sum(e.get('message_bytes', 0) for e in events)
            attempts = {e['action_id'] for e in events if e['kind'] == 'ATTEMPT'}
            results = {e['action_id'] for e in events if e['kind'] == 'RESULT'}
            if attempts - results or any(e['kind'] == 'STOP' for e in events):
                self._killed.set()
            # Messages deliberately expire on restart; ledger retains observations.
            self._mail = {m['agent_id']: [] for m in config['agents']}
        except BaseException:
            self.ledger.close()
            raise

    @property
    def envelope(self):
        return json.loads(self._config)['envelope']

    def stop(self, reason='operator_stop'):
        if reason not in STOPS:
            raise ValueError('Unknown stop condition')
        self._killed.set()  # immediately denies queued work
        with self._mutex:
            self.ledger.append({'kind': 'STOP', 'reason': reason, 'time': time.time()})

    def execute(self, token, request):
        with self._mutex:
            config = json.loads(self._config)
            manifest = next((m for m in config['agents'] if isinstance(token, str) and hmac.compare_digest(m['token'], token)), None)
            identity = {k: v for k, v in manifest.items() if k != 'token'} if manifest else {'agent_id': 'UNAUTHENTICATED'}
            e = config['envelope']
            # Roundtrip forbids Python objects and keeps the audited/executed input identical.
            request = json.loads(encode(request))
            if len(encode(request).encode()) > 16384:
                request = {'invalid': 'request exceeds 16 KiB'}
            action_id = secrets.token_hex(16)
            args_for_size = request.get('arguments', {}) if isinstance(request, dict) else {}
            message = args_for_size.get('message', '') if isinstance(args_for_size, dict) else ''
            size = len(message.encode()) if isinstance(message, str) else 0
            self.ledger.append({'kind': 'ATTEMPT', 'action_id': action_id, 'time': time.time(),
                                'identity': identity, 'authorization': e['authorization'],
                                'run_id': e['run_id'], 'request': request, 'message_bytes': size})
            self._used += 1; self._bytes += size
            try:
                if not manifest:
                    raise PermissionError('Unknown agent credential')
                if (self.ledger.root / 'STOP').exists():
                    self._escalate('operator_stop')
                if self._killed.is_set():
                    raise PermissionError('Kill switch active')
                if not e['not_before'] <= time.time() < e['expires']:
                    raise PermissionError('Outside authorization time window')
                if self._used > e['max_actions'] or self._bytes > e['max_message_bytes']:
                    raise PermissionError('Budget exhausted')
                if not isinstance(request, dict) or set(request) != {'tool', 'arguments'}:
                    self._escalate('ambiguous_scope')
                tool, args = request['tool'], request['arguments']
                if tool == 'escalate':
                    exact(args, 'reason')
                    if args['reason'] not in STOPS:
                        raise ValueError('Unknown escalation reason')
                    self._escalate(args['reason'])
                if tool not in TOOLS:
                    self._escalate('unexpected_privilege')
                if isinstance(args, dict) and any(k in args for k in ('irreversible', 'high_impact')):
                    self._escalate('high_impact')
                if isinstance(args, dict) and any(k in args for k in ('privilege', 'sudo', 'credential')):
                    self._escalate('unexpected_privilege')
                if tool not in manifest['capabilities']:
                    raise PermissionError('Capability not granted')
                if tool == 'tcp_probe':
                    exact(args, 'ip port')
                    if args not in e['targets'] or type(args['port']) is not int:
                        self._escalate('scope_escape')
                    if self._killed.is_set():
                        raise PermissionError('Kill switch active')
                    # Fixed numeric destination; no DNS, redirects, proxies, shell,
                    # arbitrary payload, or adapter-selected secondary connection.
                    family = socket.AF_INET6 if ':' in args['ip'] else socket.AF_INET
                    with socket.socket(family, socket.SOCK_STREAM) as sock:
                        sock.settimeout(min(1.0, max(0.001, e['expires'] - time.time())))
                        code = sock.connect_ex((args['ip'], args['port']))
                    observation = {'connected': code == 0, 'error_code': code}
                elif tool == 'send_message':
                    exact(args, 'peer message')
                    if args['peer'] not in manifest['peers']:
                        raise PermissionError('Undeclared peer communication')
                    if not isinstance(args['message'], str):
                        raise ValueError('Message must be text')
                    size = len(args['message'].encode())
                    if self._bytes > e['max_message_bytes']:
                        raise PermissionError('Message budget exhausted')
                    self._mail[args['peer']].append({'sender': manifest['agent_id'], 'message': args['message']})
                    observation = {'delivered': True}
                else:
                    exact(args, '')
                    observation = {'messages': self._mail[manifest['agent_id']][:]}
                    self._mail[manifest['agent_id']].clear()
                result = {'ok': True, 'observation': observation}
            except (ValueError, TypeError, KeyError, PermissionError, OSError) as error:
                result = {'ok': False, 'error': str(error)}
            try:
                self.ledger.append({'kind': 'RESULT', 'action_id': action_id, 'time': time.time(),
                                'identity': identity, 'authorization': e['authorization'],
                                    'result': result})
            except BaseException:
                self._killed.set()
                raise
            return result

    def _escalate(self, reason):
        self._killed.set()
        self.ledger.append({'kind': 'STOP', 'reason': reason, 'time': time.time()})
        raise PermissionError('ESCALATION_REQUIRED: ' + reason)

    def close(self):
        self.ledger.close()


def serve(config, state_dir, source=None, sink=None):
    """Dedicated runtime entrypoint: trusted startup config, untrusted JSON stdin.

    Per-agent tokens are delivered by the trusted host, never model-generated.
    No runtime notebook or general Tools executor is opened by this profile.
    """
    source, sink = source or sys.stdin, sink or sys.stdout
    plane = ControlPlane(config, state_dir)
    try:
        while True:
            line = source.readline(32769)
            if not line:
                break
            if len(line) > 32768:
                plane.stop('ambiguous_scope')
                raise ValueError('Oversize broker frame')
            try:
                frame = json.loads(line)
                exact(frame, 'token request')
            except (ValueError, TypeError):
                plane.stop('ambiguous_scope')
                raise ValueError('Malformed broker frame')
            result = plane.execute(frame['token'], frame['request'])
            sink.write(encode(result) + '\n'); sink.flush()
    finally:
        plane.close()
