import tempfile
import unittest
from tests.test_swarm_runtime import ScriptedModel, config
from swarm_runtime import SwarmRuntime


class ModelOutputTests(unittest.TestCase):
    def test_result_model_map_has_no_tokens(self):
        with tempfile.TemporaryDirectory() as root:
            value = config(root); result = SwarmRuntime(value, lambda m: ScriptedModel([{'final': 'done'}])).run()
            self.assertEqual(result['models'], {m['agent_id']: m['model'] for m in value['broker']['agents']})
            self.assertNotIn('token', str(result['models']))


if __name__ == '__main__': unittest.main()
