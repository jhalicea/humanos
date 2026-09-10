import tempfile
import unittest
from pathlib import Path
from tests.test_swarm_runtime import ScriptedModel, config
from swarm_runtime import SwarmRuntime


class LedgerModelTests(unittest.TestCase):
    def test_effect_is_still_attributed_to_agent_not_model_router(self):
        with tempfile.TemporaryDirectory() as root:
            value = config(root)
            scripts = {'coord': [{'final': 'done'}], 'worker': [{'action': {'tool': 'tcp_probe', 'arguments': {'ip': '127.0.0.1', 'port': 9}}}, {'final': 'done'}], 'verify': [{'final': 'done'}]}
            SwarmRuntime(value, lambda m: ScriptedModel(scripts[m['agent_id']])).run()
            ledger = (Path(root) / 'control' / 'actions.jsonl').read_text()
            self.assertIn('"agent_id":"worker"', ledger)


if __name__ == '__main__': unittest.main()
