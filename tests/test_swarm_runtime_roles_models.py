import tempfile
import unittest
from tests.test_swarm_runtime import config
from swarm_runtime import validate_runtime_config


class RoleModelTests(unittest.TestCase):
    def test_model_provider_fields_do_not_relax_role_requirements(self):
        with tempfile.TemporaryDirectory() as root:
            value = config(root); value['broker']['agents'][0]['provider'] = 'ollama'; value['orchestration']['roles']['verify'] = 'worker'
            with self.assertRaisesRegex(ValueError, 'verifier'): validate_runtime_config(value)

    def test_model_role_mapping_cannot_disagree_with_manifest(self):
        with tempfile.TemporaryDirectory() as root:
            value = config(root)
            value['orchestration']['model_roles'] = {a['agent_id']: a['model'] for a in value['broker']['agents']}
            value['orchestration']['model_roles']['worker'] = 'qwen3-coder:30b'
            with self.assertRaisesRegex(ValueError, 'match broker model manifests'):
                validate_runtime_config(value)


if __name__ == '__main__': unittest.main()
