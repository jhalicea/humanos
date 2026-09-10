import tempfile
import unittest
from pathlib import Path
from tests.test_swarm_runtime import ScriptedModel, config
from swarm_runtime import SwarmRuntime, validate_runtime_config


class RoleModelTests(unittest.TestCase):
    def test_model_provider_fields_do_not_relax_role_requirements(self):
        with tempfile.TemporaryDirectory() as root:
            value = config(root); value['broker']['agents'][0]['provider'] = 'ollama'; value['orchestration']['roles']['verify'] = 'worker'
            with self.assertRaisesRegex(ValueError, 'verifier'): validate_runtime_config(value)

    def test_model_role_mapping_cannot_disagree_with_manifest(self):
        with tempfile.TemporaryDirectory() as root:
            value = config(root)
            value['orchestration']['model_roles'] = {a['agent_id']: a['model'] for a in value['broker']['agents']}
            value['orchestration']['model_roles']['worker'] = 'qwen3-coder:30b'
            with self.assertRaisesRegex(ValueError, 'match broker model manifests'):
                validate_runtime_config(value)

    def test_heterogeneous_models_cannot_widen_tools_peers_or_authorization(self):
        with tempfile.TemporaryDirectory() as root:
            value = config(root)
            value['broker']['agents'][0]['model'] = 'llama3:latest'
            value['broker']['agents'][1]['model'] = 'llama3.2:latest'
            value['broker']['agents'][2]['model'] = 'qwen3-coder:30b'
            value['orchestration']['model_roles'] = {a['agent_id']: a['model'] for a in value['broker']['agents']}
            scripts = {
                'coord': [{'action': {'tool': 'send_message', 'arguments': {'peer': 'verify', 'message': 'bypass worker'}}}],
                'worker': [{'action': {'tool': 'shell', 'arguments': {'command': 'id'}}}],
                'verify': [{'final': 'should not run'}],
            }
            models = {}
            def factory(manifest):
                model = ScriptedModel(scripts[manifest['agent_id']]); models[manifest['agent_id']] = model; return model
            runtime = SwarmRuntime(value, factory)
            with self.assertRaisesRegex(PermissionError, 'unexpected_privilege'):
                runtime.run()
            text = (Path(root) / 'control' / 'actions.jsonl').read_text()
            self.assertIn('"model":"llama3:latest"', text)
            self.assertIn('"model":"llama3.2:latest"', text)
            self.assertIn('"error":"Undeclared peer communication"', text)
            self.assertIn('"reason":"unexpected_privilege"', text)
            self.assertEqual(models['verify'].calls, [])
            self.assertNotIn('fixture authorization', str(runtime.transcript))

    def test_heterogeneous_models_cannot_widen_targets(self):
        with tempfile.TemporaryDirectory() as root:
            value = config(root)
            value['broker']['agents'][0]['model'] = 'llama3:latest'
            value['broker']['agents'][1]['model'] = 'llama3.2:latest'
            value['broker']['agents'][2]['model'] = 'qwen3-coder:30b'
            value['orchestration']['model_roles'] = {a['agent_id']: a['model'] for a in value['broker']['agents']}
            scripts = {
                'coord': [{'final': 'done'}],
                'worker': [{'action': {'tool': 'tcp_probe', 'arguments': {'ip': '192.0.2.1', 'port': 9}}}],
                'verify': [{'final': 'should not run'}],
            }
            runtime = SwarmRuntime(value, lambda manifest: ScriptedModel(scripts[manifest['agent_id']]))
            with self.assertRaisesRegex(PermissionError, 'scope_escape'):
                runtime.run()
            text = (Path(root) / 'control' / 'actions.jsonl').read_text()
            self.assertIn('"reason":"scope_escape"', text)
            self.assertIn('"ip":"192.0.2.1"', text)


if __name__ == '__main__': unittest.main()
