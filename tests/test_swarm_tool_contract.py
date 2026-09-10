import tempfile
import unittest
from tests.test_swarm_runtime import ScriptedModel, config
from swarm_runtime import SwarmRuntime, tool_contract, validate_proposal


class SwarmToolContractTests(unittest.TestCase):
    def test_contract_lists_only_granted_tools_and_declared_peers(self):
        manifest = {'agent_id': 'coord', 'task': 'x', 'model': 'm', 'version': 'v', 'capabilities': ['send_message'], 'peers': ['worker']}
        self.assertEqual(tool_contract(manifest), [{'tool': 'send_message', 'arguments': {'peer': '<one of: worker>', 'message': '<text>'}}])

    def test_final_text_does_not_override_valid_action(self):
        proposal = {'action': {'tool': 'receive_messages', 'arguments': {}}, 'final': 'done'}
        self.assertEqual(validate_proposal(proposal), {'action': {'tool': 'receive_messages', 'arguments': {}}})

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

    def test_invalid_model_json_gets_one_repair_prompt_before_validation(self):
        with tempfile.TemporaryDirectory() as root:
            scripts = {
                'coord': [{'final': {}}, {'action': {'tool': 'send_message', 'arguments': {'peer': 'worker', 'message': 'hello'}}}, {'final': 'coord done'}],
                'worker': [{'final': 'worker done'}],
                'verify': [{'final': 'verify done'}],
            }
            models = {}
            def factory(manifest):
                model = ScriptedModel(scripts[manifest['agent_id']]); models[manifest['agent_id']] = model; return model
            result = SwarmRuntime(config(root), factory).run()
            self.assertEqual(result['status'], 'COMPLETE')
            self.assertEqual(len(models['coord'].calls), 3)
            repaired_messages = models['coord'].calls[1][0]
            self.assertIn('Rejected JSON', repaired_messages[-1]['content'])
            self.assertEqual(set(result['finals']), {'coord', 'worker', 'verify'})


if __name__ == '__main__': unittest.main()
