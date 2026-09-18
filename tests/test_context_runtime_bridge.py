import json
import tempfile
import unittest
from pathlib import Path

from context_registry import load_registry
from context_runtime import RuntimeContextRouter
from engine import Agent, Tools
from notebook import Notebook
from server import _ContextAwareAgent


class FakeModel:
    name = 'test-model'

    def __init__(self, response=None):
        self.response = response or {'final': 'done'}
        self.calls = []

    def invoke(self, messages, timeout):
        self.calls.append(json.loads(json.dumps(messages)))
        return self.response


class ContextRuntimeBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        source = Path(__file__).resolve().parents[1] / 'config' / 'context_registry.public.json'
        self.public = self.root / 'registry.json'
        self.public.write_text(source.read_text(encoding='utf-8'), encoding='utf-8')

    def tearDown(self):
        self.tmp.cleanup()

    def router(self):
        return RuntimeContextRouter(load_registry(self.public))

    def test_model_loader_continuation_exposes_resume_metadata(self):
        route = self.router().inspect('continue the sharded model loader manifest verification')
        self.assertTrue(route.applicable)
        self.assertEqual(route.decision, 'CONTINUE')
        self.assertEqual(route.selected_workstream, 'HOS-MAL-001')
        selected = next(item for item in route.candidates if item['workstream_id'] == 'HOS-MAL-001')
        self.assertIn('trust root', selected['resume_point'])
        self.assertFalse(route.requires_confirmation)

    def test_ordinary_conversation_is_not_forced_into_development_context(self):
        route = self.router().inspect('hello, tell me a joke about a cat')
        self.assertFalse(route.applicable)
        self.assertTrue(route.allow_execution)

    def test_equal_private_workspace_matches_fail_closed(self):
        data = {
            'schema_version': 1,
            'workspaces': [
                {'workspace_id': 'WS-CLIENT-001', 'workspace_type': 'CLIENT', 'public_alias': 'CLIENT-001', 'confidentiality': 'CLIENT_PRIVATE', 'repository': None, 'topics': ['email'], 'cross_workspace_policy': 'DENY'},
                {'workspace_id': 'WS-CLIENT-002', 'workspace_type': 'CLIENT', 'public_alias': 'CLIENT-002', 'confidentiality': 'CLIENT_PRIVATE', 'repository': None, 'topics': ['email'], 'cross_workspace_policy': 'DENY'},
            ],
            'workstreams': [],
        }
        self.public.write_text(json.dumps(data), encoding='utf-8')
        route = self.router().inspect('improve email triage')
        self.assertTrue(route.applicable)
        self.assertEqual(route.decision, 'AMBIGUOUS')
        self.assertTrue(route.requires_confirmation)
        self.assertFalse(route.allow_execution)

    def private_overlay(self):
        overlay = self.root / 'private.json'
        overlay.write_text(json.dumps({
            'schema_version': 1,
            'workspace_metadata': {
                'WS-CLIENT-001': {
                    'display_name': 'SECRET CLIENT NAME',
                    'local_roots': ['/very/private/root'],
                    'notes': 'SECRET NOTE',
                }
            },
            'workspaces': [{
                'workspace_id': 'WS-CLIENT-001', 'workspace_type': 'CLIENT',
                'public_alias': 'CLIENT-001', 'confidentiality': 'CLIENT_PRIVATE',
                'repository': None, 'topics': ['clientalpha', 'email', 'automation'], 'cross_workspace_policy': 'DENY',
            }],
            'workstreams': [{
                'workstream_id': 'CLI-TEST-001', 'workspace_id': 'WS-CLIENT-001',
                'title': 'SECRET PRIVATE STREAM', 'project': 'SECRET PRIVATE PROJECT', 'repository': None,
                'branch': 'private/secret-branch', 'work_order': 'private/secret-order.md', 'status': 'READY',
                'confidentiality': 'CLIENT_PRIVATE', 'topics': ['clientalpha', 'email', 'classifier', 'automation', 'triage'],
                'components': [], 'relations': [], 'last_verified_commit': None,
                'resume_point': 'SECRET RESUME DETAIL', 'next_action': 'SECRET NEXT ACTION',
            }],
        }), encoding='utf-8')
        return overlay

    def test_private_overlay_details_never_enter_model_context(self):
        router = RuntimeContextRouter(load_registry(self.public, self.private_overlay()))
        route = router.inspect('continue clientalpha triage')
        packet = json.dumps(route.model_context())
        for secret in (
            'SECRET CLIENT NAME', '/very/private/root', 'SECRET NOTE',
            'SECRET PRIVATE STREAM', 'SECRET PRIVATE PROJECT', 'private/secret-branch',
            'private/secret-order.md', 'SECRET RESUME DETAIL', 'SECRET NEXT ACTION',
        ):
            self.assertNotIn(secret, packet)
        self.assertIn('CLI-TEST-001', packet)

    def test_public_and_private_related_work_requires_confirmation_even_if_scores_differ(self):
        router = RuntimeContextRouter(load_registry(self.public, self.private_overlay()))
        route = router.inspect('improve email classifier automation')
        self.assertTrue(route.applicable)
        self.assertEqual(route.decision, 'AMBIGUOUS')
        self.assertIsNone(route.workspace_id)
        self.assertTrue(route.requires_confirmation)
        ids = {item['workstream_id'] for item in route.candidates}
        self.assertIn('HOS-INBOX-001', ids)
        self.assertIn('CLI-TEST-001', ids)

    def _agent_fixture(self, registry):
        vault = self.root / 'vault'
        book = Notebook(vault)
        book.recover()
        binding = book.bind('Jon', 'opening')
        workspace = self.root / 'workspace'
        tools = Tools(workspace)
        core = self.root / 'core'
        core.mkdir(exist_ok=True)
        (core / 'constitution.md').write_text('Human owns HumanOS.', encoding='utf-8')
        model = FakeModel({'final': 'routed answer'})
        agent = Agent(book, model, tools, core)
        wrapped = _ContextAwareAgent(agent, RuntimeContextRouter(registry), None)
        return book, binding, model, wrapped

    def test_host_runtime_identity_bypasses_workstream_routing(self):
        book, binding, model, wrapped = self._agent_fixture(load_registry(self.public))
        try:
            answer = wrapped.run('tx-identity', binding['hcid'], 'what model are you?')
            self.assertIn('Current inference model for this transaction: test-model', answer)
            self.assertEqual(model.calls, [])
            kinds = [row[0] for row in book.db.execute(
                "SELECT kind FROM events WHERE tx='tx-identity'")]
            self.assertIn('HOST_INTENT', kinds)
            self.assertNotIn('CONTEXT_ROUTE', kinds)
        finally:
            book.close()

    def test_tools_question_bypasses_browser_or_context_workstream_routing(self):
        book, binding, model, wrapped = self._agent_fixture(load_registry(self.public))
        try:
            answer = wrapped.run('tx-tools', binding['hcid'], 'what tools do we have?')
            self.assertIn('- runtime_capabilities:', answer)
            self.assertEqual(model.calls, [])
            kinds = [row[0] for row in book.db.execute(
                "SELECT kind FROM events WHERE tx='tx-tools'")]
            self.assertIn('HOST_INTENT', kinds)
            self.assertNotIn('CONTEXT_ROUTE', kinds)
        finally:
            book.close()

    def test_bridge_injects_route_without_changing_exact_human_transcript(self):
        book, binding, model, wrapped = self._agent_fixture(load_registry(self.public))
        try:
            exact = '  continue the sharded model loader manifest verification  '
            answer = wrapped.run('tx-route', binding['hcid'], exact)
            self.assertEqual(answer, 'routed answer')
            self.assertEqual(book.get_transaction('tx-route')['input'], exact)
            self.assertEqual(len(model.calls), 1)
            self.assertIn('HOS-MAL-001', model.calls[0][0]['content'])
            kinds = [row[0] for row in book.db.execute("SELECT kind FROM events WHERE tx='tx-route'")]
            self.assertIn('CONTEXT_ROUTE', kinds)
        finally:
            book.close()

    def test_bridge_ambiguity_returns_host_confirmation_without_model_call(self):
        data = {
            'schema_version': 1,
            'workspaces': [
                {'workspace_id': 'WS-CLIENT-001', 'workspace_type': 'CLIENT', 'public_alias': 'CLIENT-001', 'confidentiality': 'CLIENT_PRIVATE', 'repository': None, 'topics': ['email'], 'cross_workspace_policy': 'DENY'},
                {'workspace_id': 'WS-CLIENT-002', 'workspace_type': 'CLIENT', 'public_alias': 'CLIENT-002', 'confidentiality': 'CLIENT_PRIVATE', 'repository': None, 'topics': ['email'], 'cross_workspace_policy': 'DENY'},
            ],
            'workstreams': [],
        }
        self.public.write_text(json.dumps(data), encoding='utf-8')
        book, binding, model, wrapped = self._agent_fixture(load_registry(self.public))
        try:
            answer = wrapped.run('tx-ambiguous', binding['hcid'], 'improve email triage')
            self.assertIn('Context confirmation required', answer)
            self.assertEqual(model.calls, [])
            self.assertEqual(book.task('tx-ambiguous')['phase'], 'COMPLETE')
        finally:
            book.close()


if __name__ == '__main__':
    unittest.main()
