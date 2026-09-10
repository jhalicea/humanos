import tempfile
import unittest
from tests.test_swarm_runtime import ScriptedModel, config
from swarm_runtime import SwarmRuntime


class CompleteModelTests(unittest.TestCase):
    def test_all_roles_final_is_complete(self):
        with tempfile.TemporaryDirectory() as root:
            value = config(root)
            result = SwarmRuntime(value, lambda m: ScriptedModel([{'final': m['model']}])).run()
            self.assertEqual(result['status'], 'COMPLETE')
            self.assertEqual(set(result['finals']), {'coord', 'worker', 'verify'})


if __name__ == '__main__': unittest.main()
