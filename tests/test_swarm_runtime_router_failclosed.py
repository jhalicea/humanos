import tempfile
import unittest
from tests.test_swarm_runtime import config
from swarm_runtime import SwarmRuntime


class RouterFailClosedTests(unittest.TestCase):
    def test_runtime_rejects_undeclared_provider_field_in_broker_manifest(self):
        with tempfile.TemporaryDirectory() as root:
            value = config(root)
            value['broker']['agents'][0]['provider'] = 'uninstalled'
            with self.assertRaisesRegex(ValueError, 'Unexpected or missing fields'):
                SwarmRuntime(value)


if __name__ == '__main__': unittest.main()
