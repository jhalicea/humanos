"""Per-agent model routing for HumanOS Swarm Runtime.

Model selection is configuration, not authority. All proposed effects still pass
through the swarm ControlPlane.
"""
import urllib.parse

from engine import OllamaModel


class ModelRouter:
    """Build model adapters from a small explicit provider allowlist."""
    def __init__(self, default_endpoint='http://127.0.0.1:11434', factories=None):
        self.default_endpoint = default_endpoint
        self.factories = dict(factories or {})

    def build(self, manifest):
        provider = manifest.get('provider', 'ollama')
        if provider in self.factories:
            return self.factories[provider](manifest)
        if provider != 'ollama':
            raise ValueError('Unsupported swarm model provider: ' + str(provider))
        endpoint = manifest.get('endpoint', self.default_endpoint)
        url = urllib.parse.urlparse(endpoint)
        if url.scheme != 'http' or url.hostname not in ('127.0.0.1', 'localhost', '::1') or url.username or url.password:
            raise ValueError('Ollama swarm models require a local HTTP endpoint')
        return OllamaModel(manifest['model'], endpoint)


def public_model_identity(manifest):
    """Return model identity without broker credential material."""
    return {key: manifest[key] for key in ('agent_id', 'provider', 'model', 'version') if key in manifest}
