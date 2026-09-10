import tempfile
import unittest
from pathlib import Path
from tests.test_swarm_runtime import ScriptedModel, config
from swarm_runtime import SwarmRuntime


class RuntimeModelIdentityTests(unittest.TestCase):
    def test_runtime_reports_model_assignment_without_tokens(self):
        with tempfile.TemporaryDirectory() as root:
            value = config(root)
            value['broker']['agents'][0]['model'] = 'llama3:latest'
            value['broker']['agents'][1]['model'] = 'llama3.2:latest'
            value['broker']['agents'][2]['model'] = 'llama3:latest'
            scripts = {a['agent_id']: [{'final': 'done'}] for a in value['broker']['agents']}
            result = SwarmRuntime(value, lambda m: ScriptedModel(scripts[m['agent_id']])).run()
            self.assertEqual(result['models']['coord'], 'llama3:latest')
            self.assertEqual(result['models']['worker'], 'llama3.2:latest')
            self.assertNotIn('token', str(result))


if __name__ == '__main__': unittest.main()
