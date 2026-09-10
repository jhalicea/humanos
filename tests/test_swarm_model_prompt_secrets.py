import tempfile
import unittest
from tests.test_swarm_runtime import ScriptedModel, config
from swarm_runtime import SwarmRuntime


class PromptSecretTests(unittest.TestCase):
    def test_agent_tokens_never_enter_model_messages(self):
        with tempfile.TemporaryDirectory() as root:
            value = config(root)
            models = {}
            def factory(manifest):
                model = ScriptedModel([{'final': 'done'}]); models[manifest['agent_id']] = model; return model
            SwarmRuntime(value, factory).run()
            text = '\n'.join(str(messages) for model in models.values() for messages, _ in model.calls)
            for manifest in value['broker']['agents']:
                self.assertNotIn(manifest['token'], text)


if __name__ == '__main__': unittest.main()
