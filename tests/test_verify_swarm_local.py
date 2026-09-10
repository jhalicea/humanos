import unittest
from unittest.mock import patch
import json
import io
import verify_swarm_local


class Response:
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self, limit): return json.dumps({'models': [{'name': 'llama3:latest'}, {'name': 'llama3.2:latest'}, {'name': 'qwen3-coder:16k'}]}).encode()


class Opener:
    def open(self, request, timeout): return Response()


class LocalPreflightTests(unittest.TestCase):
    def test_ready_when_both_expected_models_are_installed(self):
        with patch('urllib.request.build_opener', return_value=Opener()), patch('sys.stdout', new=io.StringIO()) as out:
            self.assertEqual(verify_swarm_local.main(), 0)
            self.assertTrue(json.loads(out.getvalue())['ready'])
            self.assertEqual(json.loads(out.getvalue())['assignment']['verify'], 'qwen3-coder:16k')

    def test_qwen_preference_falls_back_to_latest(self):
        self.assertEqual(verify_swarm_local.choose_models(['llama3:latest', 'llama3.2:latest', 'qwen3-coder:latest'])[1]['verify'], 'qwen3-coder:latest')

    def test_missing_qwen_reports_preferred_missing_model(self):
        expected, assignment = verify_swarm_local.choose_models(['llama3:latest', 'llama3.2:latest'])
        self.assertEqual(expected, ['llama3:latest', 'llama3.2:latest', 'qwen3-coder:30b'])
        self.assertEqual(assignment['verify'], 'qwen3-coder:30b')

    def test_preflight_rejects_non_local_endpoint(self):
        with self.assertRaisesRegex(ValueError, 'local http'):
            verify_swarm_local.preflight('https://example.com')


if __name__ == '__main__': unittest.main()
