import tempfile
import unittest
from tests.test_swarm_runtime import ScriptedModel, config
from swarm_runtime import SwarmRuntime


class AuthorizationBoundaryTests(unittest.TestCase):
    def test_authorization_reference_stays_outside_all_model_prompts(self):
        with tempfile.TemporaryDirectory() as root:
            value = config(root); models = {}
            def factory(m):
                x = ScriptedModel([{'final': 'done'}]); models[m['agent_id']] = x; return x
            SwarmRuntime(value, factory).run()
            text = str([call for model in models.values() for call in model.calls])
            self.assertNotIn('fixture authorization', text)


if __name__ == '__main__': unittest.main()
