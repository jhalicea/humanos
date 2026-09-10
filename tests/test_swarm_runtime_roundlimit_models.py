import tempfile
import unittest
from tests.test_swarm_runtime import ScriptedModel, config
from swarm_runtime import SwarmRuntime


class RoundLimitModelTests(unittest.TestCase):
    def test_model_identity_does_not_change_round_limit_semantics(self):
        with tempfile.TemporaryDirectory() as root:
            value = config(root, max_rounds=1)
            scripts = {'coord': [{'action': {'tool': 'send_message', 'arguments': {'peer': 'worker', 'message': 'continue'}}}], 'worker': [{'action': {'tool': 'receive_messages', 'arguments': {}}}], 'verify': [{'final': 'partial'}]}
            result = SwarmRuntime(value, lambda m: ScriptedModel(scripts[m['agent_id']])).run()
            self.assertEqual(result['status'], 'ROUND_LIMIT')


if __name__ == '__main__': unittest.main()
