"""Create a fresh, messaging-only local HumanOS swarm demo configuration.

The demo grants no tcp_probe capability. It exists only to verify that distinct
local Ollama models can coordinate through the governed broker on the host.
"""
import hashlib
import json
import os
from pathlib import Path
import secrets
import time

from swarm import PROFILE, STOPS


def manifest(agent_id, model, task, capabilities, peers):
    return {'agent_id': agent_id, 'model': model, 'version': 'local-demo', 'task': task,
            'capabilities': capabilities, 'peers': peers, 'token': secrets.token_urlsafe(32)}


def build(root):
    now = int(time.time())
    statement = b'HumanOS local messaging-only swarm demo; no network probing authorized'
    agents = [
        manifest('coord', 'llama3:latest',
                 'Send worker a short task through send_message, then finish after broker confirmation.',
                 ['send_message'], ['worker']),
        manifest('worker', 'llama3.2:latest',
                 'Receive coordinator messages. Send verifier a short summary through send_message, then finish.',
                 ['receive_messages', 'send_message'], ['verify']),
        manifest('verify', 'llama3:latest',
                 'Receive worker messages, verify that the chain used broker observations, then finish.',
                 ['receive_messages'], []),
    ]
    return {
        'broker': {
            'profile': PROFILE,
            'envelope': {
                'run_id': 'local-demo-' + secrets.token_hex(8),
                # Broker schema requires an exact target allowlist, but no agent in this
                # demo has tcp_probe, so this target cannot be used by the models.
                'targets': [{'ip': '127.0.0.1', 'port': 9}],
                'authorization': {
                    'human': os.environ.get('USER', 'local-owner'),
                    'reference': 'generated-local-demo',
                    'provenance_sha256': hashlib.sha256(statement).hexdigest(),
                    'owner_attested': True,
                    'environment': 'authorized_lab'},
                'not_before': now - 5,
                'expires': now + 900,
                'permitted_impact': 'connect_only',
                'stop_conditions': sorted(STOPS),
                'max_actions': 40,
                'max_message_bytes': 8192,
            },
            'agents': agents,
        },
        'control_state': str((Path(root) / 'control').resolve()),
        'orchestration': {
            'roles': {'coord': 'coordinator', 'worker': 'worker', 'verify': 'verifier'},
            'max_rounds': 8,
            'model_timeout': 60,
        },
    }


def main():
    root = Path.home() / '.humanos' / 'swarm-demo' / ('run-' + time.strftime('%Y%m%d-%H%M%S'))
    root.mkdir(parents=True, mode=0o700, exist_ok=False)
    os.chmod(root, 0o700)
    config = root / 'config.json'
    config.write_text(json.dumps(build(root), indent=2) + '\n')
    os.chmod(config, 0o600)
    print(config)
    return 0


if __name__ == '__main__': raise SystemExit(main())
