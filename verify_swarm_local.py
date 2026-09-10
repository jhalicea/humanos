"""Non-effectful preflight for local HumanOS swarm models."""
import json
import os
from urllib.parse import urlparse
import urllib.request

QWEN_PREFERENCE = ('qwen3-coder:30b', 'qwen3-coder:16k', 'qwen3-coder:latest')


def choose_models(installed):
    installed = set(installed)
    qwen = next((name for name in QWEN_PREFERENCE if name in installed), None)
    expected = ['llama3:latest', 'llama3.2:latest', qwen or QWEN_PREFERENCE[0]]
    assignment = {'coord': expected[0], 'worker': expected[1], 'verify': expected[2]}
    return expected, assignment


def local_endpoint(value):
    parsed = urlparse(value)
    if parsed.scheme != 'http' or parsed.hostname not in {'127.0.0.1', 'localhost', '::1'}:
        raise ValueError('HUMANOS_ENDPOINT must be a local http Ollama endpoint')
    return value.rstrip('/')


def installed_models(endpoint=None):
    endpoint = local_endpoint(endpoint or os.environ.get('HUMANOS_ENDPOINT', 'http://127.0.0.1:11434'))
    req = urllib.request.Request(endpoint + '/api/tags')
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=5) as response:
        data = json.loads(response.read(1000000))
    return sorted(m.get('name') for m in data.get('models', []) if m.get('name'))


def preflight(endpoint=None):
    installed = installed_models(endpoint)
    expected, assignment = choose_models(installed)
    return {'endpoint': local_endpoint(endpoint or os.environ.get('HUMANOS_ENDPOINT', 'http://127.0.0.1:11434')),
            'installed': installed, 'expected': expected, 'assignment': assignment,
            'ready': all(name in installed for name in expected),
            'missing': [name for name in expected if name not in installed]}


def main():
    endpoint = os.environ.get('HUMANOS_ENDPOINT', 'http://127.0.0.1:11434').rstrip('/')
    result = preflight(endpoint)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['ready'] else 2


if __name__ == '__main__': raise SystemExit(main())
