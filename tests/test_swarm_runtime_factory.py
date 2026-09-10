import tempfile
import unittest
from tests.test_swarm_runtime import ScriptedModel, config
from swarm_runtime import SwarmRuntime


class FactoryCompatibilityTests(unittest.TestCase):
    def test_existing_model_factory_contract_remains_supported(self):
        with tempfile.TemporaryDirectory() as root:
            value = config(root); seen = []
            def factory(m): seen.append(m['agent_id']); return ScriptedModel([{'final': 'done'}])
            SwarmRuntime(value, factory).run()
            self.assertEqual(set(seen), {'coord', 'worker', 'verify'})


if __name__ == '__main__': unittest.main()
