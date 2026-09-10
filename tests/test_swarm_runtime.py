import hashlib
import tempfile
import time
import unittest
from pathlib import Path

from swarm import PROFILE, STOPS
from swarm_runtime import SwarmRuntime, validate_runtime_config


class ScriptedModel:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def invoke(self, messages, timeout):
        self.calls.append((messages, timeout))
        return self.responses.pop(0)


def config(root, max_rounds=3):
    now = int(time.time())
    agents = [
        {'agent_id': 'coord', 'model': 'fixture-c', 'version': '1', 'task': 'coordinate',
         'capabilities': ['send_message'], 'peers': ['worker'], 'token': 'c' * 32},
        {'agent_id': 'worker', 'model': 'fixture-w', 'version': '1', 'task': 'inspect',
         'capabilities': ['receive_messages', 'tcp_probe'], 'peers': [], 'token': 'w' * 32},
        {'agent_id': 'verify', 'model': 'fixture-v', 'version': '1', 'task': 'verify evidence',
         'capabilities': ['receive_messages'], 'peers': [], 'token': 'v' * 32},
    ]
    return {
        'broker': {
            'profile': PROFILE,
            'envelope': {
                'run_id': 'runtime-v2-test',
                'targets': [{'ip': '127.0.0.1', 'port': 9}],
                'authorization': {
                    'human': 'fixture owner', 'reference': 'fixture authorization',
                    'provenance_sha256': hashlib.sha256(b'fixture authorization').hexdigest(),
                    'owner_attested': True, 'environment': 'authorized_lab'},
                'not_before': now - 5, 'expires': now + 120,
                'permitted_impact': 'connect_only',
                'stop_conditions': sorted(STOPS),
                'max_actions': 20, 'max_message_bytes': 1000,
            },
            'agents': agents,
        },
        'control_state': str(Path(root).resolve() / 'control'),
        'orchestration': {
            'roles': {'coord': 'coordinator', 'worker': 'worker', 'verify': 'verifier'},
            'max_rounds': max_rounds, 'model_timeout': 5,
        },
    }


class SwarmRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp.cleanup()

    def test_role_validation_requires_complete_three_role_swarm(self):
        value = config(self.temp.name)
        value['orchestration']['roles']['verify'] = 'worker'
        with self.assertRaisesRegex(ValueError, 'verifier'):
            validate_runtime_config(value)

    def test_models_coordinate_only_through_broker(self):
        scripts = {
            'coord': [
                {'action': {'tool': 'send_message', 'arguments': {'peer': 'worker', 'message': 'check target'}}},
                {'final': 'coord complete'},
            ],
            'worker': [
                {'action': {'tool': 'receive_messages', 'arguments': {}}},
                {'final': 'worker complete'},
            ],
            'verify': [{'final': 'verification complete'}],
        }
        models = {}
        def factory(manifest):
            model = ScriptedModel(scripts[manifest['agent_id']])
            models[manifest['agent_id']] = model
            return model
        runtime = SwarmRuntime(config(self.temp.name), factory)
        result = runtime.run()
        self.assertEqual(result['status'], 'COMPLETE')
        self.assertEqual(result['rounds'], 2)
        self.assertEqual(set(result['finals']), {'coord', 'worker', 'verify'})
        worker_messages = '\n'.join(m['content'] for call, _ in models['worker'].calls for m in call)
        self.assertIn('check target', worker_messages)
        # Authorization evidence remains trusted-host data and is not exposed to model prompts.
        all_model_text = '\n'.join(m['content'] for model in models.values() for call, _ in model.calls for m in call)
        self.assertNotIn('fixture authorization', all_model_text)

    def test_effectful_action_is_attributed_by_existing_control_plane(self):
        scripts = {
            'coord': [{'final': 'done'}],
            'worker': [
                {'action': {'tool': 'tcp_probe', 'arguments': {'ip': '127.0.0.1', 'port': 9}}},
                {'final': 'probe observed'},
            ],
            'verify': [{'final': 'checked'}],
        }
        runtime = SwarmRuntime(config(self.temp.name), lambda manifest: ScriptedModel(scripts[manifest['agent_id']]))
        result = runtime.run()
        self.assertEqual(result['status'], 'COMPLETE')
        ledger = Path(self.temp.name) / 'control' / 'actions.jsonl'
        text = ledger.read_text()
        self.assertIn('"agent_id":"worker"', text)
        self.assertIn('"tool":"tcp_probe"', text)
        self.assertNotIn('w' * 32, text)

    def test_scope_escape_poison_stops_orchestration(self):
        scripts = {
            'coord': [{'final': 'done'}],
            'worker': [{'action': {'tool': 'tcp_probe', 'arguments': {'ip': '192.0.2.1', 'port': 9}}}],
            'verify': [{'final': 'should not run'}],
        }
        models = {}
        def factory(manifest):
            model = ScriptedModel(scripts[manifest['agent_id']])
            models[manifest['agent_id']] = model
            return model
        runtime = SwarmRuntime(config(self.temp.name), factory)
        with self.assertRaisesRegex(PermissionError, 'scope_escape'):
            runtime.run()
        self.assertEqual(models['verify'].calls, [])
        self.assertIn('scope_escape', (Path(self.temp.name) / 'control' / 'actions.jsonl').read_text())

    def test_round_limit_is_truthful_not_implicit_success(self):
        scripts = {
            'coord': [{'action': {'tool': 'send_message', 'arguments': {'peer': 'worker', 'message': 'continue'}}}],
            'worker': [{'action': {'tool': 'receive_messages', 'arguments': {}}}],
            'verify': [{'final': 'partial verification'}],
        }
        runtime = SwarmRuntime(config(self.temp.name, max_rounds=1),
                               lambda manifest: ScriptedModel(scripts[manifest['agent_id']]))
        result = runtime.run()
        self.assertEqual(result['status'], 'ROUND_LIMIT')
        self.assertEqual(set(result['finals']), {'verify'})


if __name__ == '__main__':
    unittest.main()
