import tempfile
import unittest
from pathlib import Path
from make_swarm_local_demo import build
from swarm_runtime import validate_runtime_config


class LocalDemoTests(unittest.TestCase):
    def test_demo_is_valid_and_no_agent_can_probe_network(self):
        with tempfile.TemporaryDirectory() as root:
            value = build(Path(root))
            validate_runtime_config(value)
            for agent in value['broker']['agents']:
                self.assertNotIn('tcp_probe', agent['capabilities'])
            self.assertEqual(value['orchestration']['roles'], {'coord': 'coordinator', 'worker': 'worker', 'verify': 'verifier'})

    def test_demo_uses_two_local_model_assignments(self):
        with tempfile.TemporaryDirectory() as root:
            value = build(Path(root))
            models = {a['agent_id']: a['model'] for a in value['broker']['agents']}
            self.assertEqual(models['coord'], 'llama3:latest')
            self.assertEqual(models['worker'], 'llama3.2:latest')
            self.assertEqual(models['verify'], 'llama3:latest')


if __name__ == '__main__': unittest.main()
