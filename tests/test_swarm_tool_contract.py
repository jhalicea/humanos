import tempfile
import unittest
from tests.test_swarm_runtime import ScriptedModel, config
from swarm_runtime import SwarmRuntime, tool_contract


class SwarmToolContractTests(unittest.TestCase):
    def test_contract_lists_only_granted_tools_and_declared_peers(self):
        manifest = {'agent_id': 'coord', 'task': 'x', 'model': 'm', 'version': 'v', 'capabilities': ['send_message'], 'peers': ['worker']}
        self.assertEqual(tool_contract(manifest), [{'tool': 'send_message', 'arguments': {'peer': ['worker'], 'message': '<text>'}}])

    def test_model_prompt_contains_exact_allowed_actions_without_token(self):
        with tempfile.TemporaryDirectory() as root:
            value = config(root); models = {}
            def factory(manifest):
                model = ScriptedModel([{'final': 'done'}]); models[manifest['agent_id']] = model; return model
            SwarmRuntime(value, factory).run()
            for manifest in value['broker']['agents']:
                messages = models[manifest['agent_id']].calls[0][0]
                text = str(messages)
                self.assertIn('allowed_actions', text)
                self.assertNotIn(manifest['token'], text)
                for capability in manifest['capabilities']:
                    self.assertIn(capability, text)


if __name__ == '__main__': unittest.main()
