import tempfile
import unittest
from tests.test_swarm_runtime import ScriptedModel, config
from swarm_runtime import SwarmRuntime


class ScopeModelTests(unittest.TestCase):
    def test_model_assignment_cannot_widen_scope(self):
        with tempfile.TemporaryDirectory() as root:
            value = config(root)
            scripts = {'coord': [{'final': 'done'}], 'worker': [{'action': {'tool': 'tcp_probe', 'arguments': {'ip': '192.0.2.1', 'port': 9}}}], 'verify': [{'final': 'no'}]}
            runtime = SwarmRuntime(value, lambda m: ScriptedModel(scripts[m['agent_id']]))
            with self.assertRaisesRegex(PermissionError, 'scope_escape'): runtime.run()


if __name__ == '__main__': unittest.main()
