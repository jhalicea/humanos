import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from make_swarm_local_demo import build, main
from swarm_runtime import validate_runtime_config


class LocalDemoTests(unittest.TestCase):
    def test_demo_is_valid_and_no_agent_can_probe_network(self):
        with tempfile.TemporaryDirectory() as root:
            value = build(Path(root))
            validate_runtime_config(value)
            for agent in value['broker']['agents']:
                self.assertNotIn('tcp_probe', agent['capabilities'])
            self.assertEqual(value['orchestration']['roles'], {'coord': 'coordinator', 'worker': 'worker', 'verify': 'verifier'})

    def test_demo_uses_three_distinct_local_model_assignments(self):
        with tempfile.TemporaryDirectory() as root:
            value = build(Path(root))
            models = {a['agent_id']: a['model'] for a in value['broker']['agents']}
            self.assertEqual(models['coord'], 'llama3:latest')
            self.assertEqual(models['worker'], 'llama3.2:latest')
            self.assertEqual(models['verify'], 'qwen3-coder:30b')
            self.assertEqual(len(set(models.values())), 3)
            self.assertEqual(value['orchestration']['model_roles'], models)

    def test_demo_uses_selected_qwen_fallback_for_manifest_and_model_roles(self):
        with tempfile.TemporaryDirectory() as root:
            selected = {'coord': 'llama3:latest', 'worker': 'llama3.2:latest', 'verify': 'qwen3-coder:16k'}
            value = build(Path(root), selected)
            models = {a['agent_id']: a['model'] for a in value['broker']['agents']}
            self.assertEqual(models, selected)
            self.assertEqual(value['orchestration']['model_roles'], selected)

    def test_main_stops_before_writing_config_when_preflight_is_missing_models(self):
        with tempfile.TemporaryDirectory() as root:
            missing = {'ready': False, 'missing': ['qwen3-coder:30b'], 'assignment': {}}
            with patch('make_swarm_local_demo.preflight', return_value=missing), patch('pathlib.Path.home', return_value=Path(root)):
                self.assertEqual(main(), 2)
            self.assertEqual(list(Path(root).rglob('config.json')), [])


if __name__ == '__main__': unittest.main()
