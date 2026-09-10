"""Non-effectful preflight for local HumanOS swarm models."""
import json
import os
import urllib.request


def main():
    endpoint = os.environ.get('HUMANOS_ENDPOINT', 'http://127.0.0.1:11434').rstrip('/')
    req = urllib.request.Request(endpoint + '/api/tags')
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=5) as response:
        data = json.loads(response.read(1000000))
    installed = sorted(m.get('name') for m in data.get('models', []) if m.get('name'))
    expected = ['llama3:latest', 'llama3.2:latest']
    result = {'endpoint': endpoint, 'installed': installed, 'expected': expected,
              'ready': all(name in installed for name in expected),
              'missing': [name for name in expected if name not in installed]}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['ready'] else 2


if __name__ == '__main__': raise SystemExit(main())
