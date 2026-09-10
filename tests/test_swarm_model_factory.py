import unittest
from swarm_models import ModelRouter


class FactoryTests(unittest.TestCase):
    def test_explicit_factory_can_override_named_provider(self):
        marker = object()
        router = ModelRouter(factories={'ollama': lambda manifest: marker})
        self.assertIs(router.build({'agent_id': 'x', 'provider': 'ollama', 'model': 'fixture'}), marker)


if __name__ == '__main__': unittest.main()
