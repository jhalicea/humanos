import tempfile
import unittest
from tests.test_swarm_runtime import ScriptedModel, config
from swarm_runtime import SwarmRuntime
from swarm_models import ModelRouter


class RouterRuntimeTests(unittest.TestCase):
    def test_runtime_uses_explicit_ollama_factory_without_authority_change(self):
        with tempfile.TemporaryDirectory() as root:
            value = config(root)
            scripts = {a['agent_id']: [{'final': 'done'}] for a in value['broker']['agents']}
            router = ModelRouter(factories={'ollama': lambda m: ScriptedModel(scripts[m['agent_id']])})
            result = SwarmRuntime(value, model_router=router).run()
            self.assertEqual(result['status'], 'COMPLETE')
            self.assertEqual(result['ledger_records'], 0)


if __name__ == '__main__': unittest.main()
