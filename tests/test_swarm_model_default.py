import unittest
from swarm_models import ModelRouter


class DefaultProviderTests(unittest.TestCase):
    def test_provider_defaults_to_local_ollama(self):
        model = ModelRouter().build({'agent_id': 'x', 'model': 'llama3:latest'})
        self.assertEqual(model.name, 'llama3:latest')


if __name__ == '__main__': unittest.main()
