import tempfile
import unittest
from tests.test_swarm_runtime import config
from swarm_runtime import SwarmRuntime


class RouterFailClosedTests(unittest.TestCase):
    def test_runtime_rejects_uninstalled_provider_before_run(self):
        with tempfile.TemporaryDirectory() as root:
            value = config(root); value['broker']['agents'][0]['provider'] = 'uninstalled'
            with self.assertRaisesRegex(ValueError, 'Unsupported'): SwarmRuntime(value)


if __name__ == '__main__': unittest.main()
