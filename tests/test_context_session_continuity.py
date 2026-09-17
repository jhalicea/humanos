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

    def __init__(self):
        self.calls = []

    def invoke(self, messages, timeout):
        self.calls.append(json.loads(json.dumps(messages)))
        return {'final': 'done'}


class SessionContextContinuityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        source = Path(__file__).resolve().parents[1] / 'config' / 'context_registry.public.json'
        self.public = self.root / 'registry.json'
        self.public.write_text(source.read_text(encoding='utf-8'), encoding='utf-8')

    def tearDown(self):
        self.tmp.cleanup()

    def _fixture(self):
        vault = self.root / 'vault'
        book = Notebook(vault)
        book.recover()
        binding = book.bind('Jon', 'opening')
        workspace = self.root / 'workspace'
        tools = Tools(workspace)
        core = self.root / 'core'
        core.mkdir(exist_ok=True)
        (core / 'constitution.md').write_text('Human owns HumanOS.', encoding='utf-8')
        model = FakeModel()
        agent = Agent(book, model, tools, core)
        router = RuntimeContextRouter(load_registry(self.public))
        wrapped = _ContextAwareAgent(agent, router, None)
        return vault, book, binding, model, wrapped, router

    def test_do_it_inherits_immediately_preceding_verified_workstream(self):
        vault, book, binding, model, wrapped, router = self._fixture()
        try:
            wrapped.run('tx-route', binding['hcid'], 'continue the sharded model loader manifest verification')
            self.assertEqual(book.get_transaction('tx-route')['status'], 'CHECKPOINTED')

            wrapped.run('tx-followup', binding['hcid'], 'do it')
            self.assertEqual(book.get_transaction('tx-followup')['input'], 'do it')
            self.assertEqual(len(model.calls), 2)
            second_prompt = json.dumps(model.calls[1])
            self.assertIn('HOS-MAL-001', second_prompt)
            self.assertIn('SESSION_CONTINUITY', second_prompt)

            event = book.db.execute(
                "SELECT payload FROM events WHERE tx='tx-followup' AND kind='CONTEXT_SESSION_CONTINUED'"
            ).fetchone()
            self.assertIsNotNone(event)
            payload = json.loads(event['payload'])
            self.assertEqual(payload['source_tx'], 'tx-route')
            self.assertEqual(payload['workstream_id'], 'HOS-MAL-001')
        finally:
            book.close()

    def test_intervening_ordinary_turn_breaks_implicit_inheritance(self):
        vault, book, binding, model, wrapped, router = self._fixture()
        try:
            wrapped.run('tx-route', binding['hcid'], 'continue the sharded model loader manifest verification')
            wrapped.run('tx-chat', binding['hcid'], 'hello, how are you?')
            wrapped.run('tx-followup', binding['hcid'], 'do it')

            third_prompt = json.dumps(model.calls[2])
            self.assertNotIn('SESSION_CONTINUITY', third_prompt)
            event = book.db.execute(
                "SELECT 1 FROM events WHERE tx='tx-followup' AND kind='CONTEXT_SESSION_CONTINUED'"
            ).fetchone()
            self.assertIsNone(event)
        finally:
            book.close()

    def test_explicit_new_workstream_route_wins_over_session_binding(self):
        vault, book, binding, model, wrapped, router = self._fixture()
        try:
            wrapped.run('tx-route', binding['hcid'], 'continue the sharded model loader manifest verification')
            wrapped.run('tx-inbox', binding['hcid'], 'improve inbox classifier automation')

            second_prompt = json.dumps(model.calls[1])
            self.assertIn('HOS-INBOX-001', second_prompt)
            self.assertIn('"origin": "REQUEST"', second_prompt)
            event = book.db.execute(
                "SELECT 1 FROM events WHERE tx='tx-inbox' AND kind='CONTEXT_SESSION_CONTINUED'"
            ).fetchone()
            self.assertIsNone(event)
        finally:
            book.close()

    def test_bare_yes_is_not_a_workstream_continuation_command(self):
        vault, book, binding, model, wrapped, router = self._fixture()
        try:
            wrapped.run('tx-route', binding['hcid'], 'continue the sharded model loader manifest verification')
            wrapped.run('tx-yes', binding['hcid'], 'yes')
            second_prompt = json.dumps(model.calls[1])
            self.assertNotIn('SESSION_CONTINUITY', second_prompt)
        finally:
            book.close()

    def test_unfinished_immediately_prior_turn_breaks_inheritance(self):
        vault, book, binding, model, wrapped, router = self._fixture()
        try:
            wrapped.run('tx-route', binding['hcid'], 'continue the sharded model loader manifest verification')
            book.start(binding['hcid'], 'tx-open', 'unfinished ordinary turn')
            route = router.inspect_session(book, binding['hcid'], 'do it', current_tx='tx-next')
            self.assertFalse(route.applicable)
        finally:
            book.close()

    def test_verified_session_binding_survives_notebook_reopen(self):
        vault, book, binding, model, wrapped, router = self._fixture()
        hcid = binding['hcid']
        wrapped.run('tx-route', hcid, 'continue the sharded model loader manifest verification')
        book.close()

        reopened = Notebook(vault)
        try:
            reopened.recover()
            route = RuntimeContextRouter(load_registry(self.public)).inspect_session(
                reopened, hcid, 'keep going', current_tx='tx-future')
            self.assertTrue(route.applicable)
            self.assertEqual(route.origin, 'SESSION_CONTINUITY')
            self.assertEqual(route.selected_workstream, 'HOS-MAL-001')
            self.assertEqual(route.source_tx, 'tx-route')
        finally:
            reopened.close()

    def test_reference_or_work_binding_can_disable_implicit_inheritance(self):
        vault, book, binding, model, wrapped, router = self._fixture()
        try:
            wrapped.run('tx-route', binding['hcid'], 'continue the sharded model loader manifest verification')
            route = router.inspect_session(
                book, binding['hcid'], 'do it', current_tx='tx-future', allow_inherit=False)
            self.assertFalse(route.applicable)
        finally:
            book.close()


if __name__ == '__main__':
    unittest.main()
