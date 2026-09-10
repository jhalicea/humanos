import unittest
from swarm_models import ModelRouter


class RouterDefaultTests(unittest.TestCase):
    def test_default_endpoint_is_loopback(self):
        self.assertEqual(ModelRouter().default_endpoint, 'http://127.0.0.1:11434')


if __name__ == '__main__': unittest.main()
