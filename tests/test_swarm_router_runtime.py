import tempfile
import unittest
from tests.test_swarm_runtime import ScriptedModel, config
from swarm_runtime import SwarmRuntime
from swarm_models import ModelRouter


class RouterRuntimeTests(unittest.TestCase):
    def test_runtime_can_mix_explicit_adapter_factories_without_authority_change(self):
        with tempfile.TemporaryDirectory() as root:
            value = config(root)
            value['broker']['agents'][0]['provider'] = 'external-test'
            scripts = {a['agent_id']: [{'final': 'done'}] for a in value['broker']['agents']}
            router = ModelRouter(factories={'external-test': lambda m: ScriptedModel(scripts[m['agent_id']])})
            def local_fixture(manifest): return ScriptedModel(scripts[manifest['agent_id']])
            router.factories['ollama'] = local_fixture
            result = SwarmRuntime(value, model_router=router).run()
            self.assertEqual(result['status'], 'COMPLETE')
            self.assertEqual(result['ledger_records'], 0)


if __name__ == '__main__': unittest.main()
