import unittest
from swarm_models import ModelRouter


class FakeModel:
    def __init__(self, manifest): self.manifest = manifest


class SwarmModelRouterTests(unittest.TestCase):
    def test_routes_distinct_local_models_per_agent(self):
        router = ModelRouter()
        a = router.build({'agent_id': 'a', 'provider': 'ollama', 'model': 'llama3:latest'})
        b = router.build({'agent_id': 'b', 'provider': 'ollama', 'model': 'llama3.2:latest'})
        self.assertEqual(a.name, 'llama3:latest')
        self.assertEqual(b.name, 'llama3.2:latest')

    def test_rejects_remote_ollama_endpoint(self):
        router = ModelRouter()
        with self.assertRaisesRegex(ValueError, 'local HTTP endpoint'):
            router.build({'agent_id': 'a', 'provider': 'ollama', 'model': 'llama3:latest', 'endpoint': 'http://example.com:11434'})

    def test_external_provider_requires_explicit_factory(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported'):
            ModelRouter().build({'agent_id': 'a', 'provider': 'cloud', 'model': 'x'})
        router = ModelRouter(factories={'cloud': FakeModel})
        model = router.build({'agent_id': 'a', 'provider': 'cloud', 'model': 'x'})
        self.assertEqual(model.manifest['model'], 'x')


if __name__ == '__main__': unittest.main()
