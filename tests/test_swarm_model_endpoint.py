import unittest
from swarm_models import ModelRouter


class EndpointTests(unittest.TestCase):
    def test_loopback_aliases_are_allowed(self):
        for endpoint in ('http://127.0.0.1:11434', 'http://localhost:11434', 'http://[::1]:11434'):
            model = ModelRouter().build({'agent_id': 'x', 'provider': 'ollama', 'model': 'llama3:latest', 'endpoint': endpoint})
            self.assertEqual(model.name, 'llama3:latest')

    def test_credentials_in_endpoint_are_rejected(self):
        with self.assertRaises(ValueError):
            ModelRouter().build({'agent_id': 'x', 'provider': 'ollama', 'model': 'llama3:latest', 'endpoint': 'http://u:p@localhost:11434'})


if __name__ == '__main__': unittest.main()
