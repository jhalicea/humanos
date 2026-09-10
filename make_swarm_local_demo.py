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
from verify_swarm_local import preflight

MODEL_ASSIGNMENT = {
    'coord': 'llama3:latest',
    'worker': 'llama3.2:latest',
    'verify': 'qwen3-coder:30b',
}


def manifest(agent_id, model, task, capabilities, peers):
    return {'agent_id': agent_id, 'model': model, 'version': 'local-demo', 'task': task,
            'capabilities': capabilities, 'peers': peers, 'token': secrets.token_urlsafe(32)}


def build(root, models=None):
    now = int(time.time())
    models = dict(models or MODEL_ASSIGNMENT)
    statement = b'HumanOS local messaging-only swarm demo; no network probing authorized'
    agents = [
        manifest('coord', models['coord'],
                 'First return exactly this broker action with your own short message: {"action":{"tool":"send_message","arguments":{"peer":"worker","message":"Summarize this brokered local demo for verifier."}}}. After the broker confirms delivery, return a final string.',
                 ['send_message'], ['worker']),
        manifest('worker', models['worker'],
                 'First return exactly this broker action: {"action":{"tool":"receive_messages","arguments":{}}}. After receiving a coordinator message, return exactly this broker action with a short summary: {"action":{"tool":"send_message","arguments":{"peer":"verify","message":"Brokered local demo summary received from coordinator."}}}. After the broker confirms delivery, return a final string.',
                 ['receive_messages', 'send_message'], ['verify']),
        manifest('verify', models['verify'],
                 'First return exactly this broker action: {"action":{"tool":"receive_messages","arguments":{}}}. If no worker message is present, return the same receive_messages action again on the next round. After receiving a worker message, verify the chain used broker observations and return a final string.',
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
            'model_roles': models,
            'max_rounds': 8,
            'model_timeout': 60,
        },
    }


def main():
    model_check = preflight()
    if not model_check['ready']:
        print(json.dumps(model_check, indent=2, sort_keys=True))
        return 2
    root = Path.home() / '.humanos' / 'swarm-demo' / ('run-' + time.strftime('%Y%m%d-%H%M%S'))
    root.mkdir(parents=True, mode=0o700, exist_ok=False)
    os.chmod(root, 0o700)
    config = root / 'config.json'
    config.write_text(json.dumps(build(root, model_check['assignment']), indent=2) + '\n')
    os.chmod(config, 0o600)
    print(config)
    return 0


if __name__ == '__main__': raise SystemExit(main())
