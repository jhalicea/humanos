import unittest
from swarm_models import ModelRouter


class UnknownProviderTests(unittest.TestCase):
    def test_unknown_provider_fails_closed(self):
        with self.assertRaisesRegex(ValueError, 'Unsupported swarm model provider'):
            ModelRouter().build({'agent_id': 'x', 'provider': 'not-installed', 'model': 'whatever'})


if __name__ == '__main__': unittest.main()
