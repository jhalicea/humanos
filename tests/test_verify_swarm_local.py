import unittest
from unittest.mock import patch
import json
import io
import verify_swarm_local


class Response:
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self, limit): return json.dumps({'models': [{'name': 'llama3:latest'}, {'name': 'llama3.2:latest'}]}).encode()


class Opener:
    def open(self, request, timeout): return Response()


class LocalPreflightTests(unittest.TestCase):
    def test_ready_when_both_expected_models_are_installed(self):
        with patch('urllib.request.build_opener', return_value=Opener()), patch('sys.stdout', new=io.StringIO()) as out:
            self.assertEqual(verify_swarm_local.main(), 0)
            self.assertTrue(json.loads(out.getvalue())['ready'])


if __name__ == '__main__': unittest.main()
