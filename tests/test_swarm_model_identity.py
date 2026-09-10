import unittest
from swarm_models import public_model_identity


class IdentityTests(unittest.TestCase):
    def test_public_identity_excludes_credentials_and_endpoint(self):
        value = public_model_identity({'agent_id': 'a', 'provider': 'ollama', 'model': 'llama3:latest', 'version': '1', 'token': 'secret', 'endpoint': 'http://localhost:11434'})
        self.assertEqual(value, {'agent_id': 'a', 'provider': 'ollama', 'model': 'llama3:latest', 'version': '1'})


if __name__ == '__main__': unittest.main()
