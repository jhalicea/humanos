import json
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from context_registry import load_registry
from context_runtime import RuntimeContextRouter
from engine import Agent, Tools
from notebook import Notebook
from server import _ContextAwareAgent


class FakeModel:
    name = "test-model"

    def __init__(self):
        self.calls = []

    def invoke(self, messages, timeout):
        self.calls.append(json.loads(json.dumps(messages)))
        return {"final": "done"}


class NotebookContextRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        source = Path(__file__).resolve().parents[1] / "config" / "context_registry.public.json"
        self.public = self.root / "registry.json"
        self.public.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def _fixture(self):
        vault = self.root / "vault"
        book = Notebook(vault)
        book.recover()
        binding = book.bind("Jon", "opening")
        workspace = self.root / "workspace"
        tools = Tools(workspace)
        core = self.root / "core"
        core.mkdir(exist_ok=True)
        (core / "constitution.md").write_text("Human owns HumanOS.", encoding="utf-8")
        model = FakeModel()
        agent = Agent(book, model, tools, core)
        router = RuntimeContextRouter(load_registry(self.public))
        wrapped = _ContextAwareAgent(agent, router, None)
        return vault, book, binding, model, wrapped, router

    def test_cross_hcid_historical_continuation_resolves_verified_workstream(self):
        vault, book, first, model, wrapped, router = self._fixture()
        try:
            wrapped.run("tx-old", first["hcid"], "continue the sharded model loader manifest verification")
            second = book.bind("Jon", "new conversation")
            route = router.inspect_history(
                book, "continue what we were doing earlier", current_tx="tx-new")
            self.assertTrue(route.applicable)
            self.assertEqual(route.origin, "NOTEBOOK_RECOVERY")
            self.assertEqual(route.decision, "CONTINUE")
            self.assertEqual(route.selected_workstream, "HOS-MAL-001")
            self.assertEqual(route.source_tx, "tx-old")

            wrapped.run("tx-new", second["hcid"], "continue what we were doing earlier")
            self.assertEqual(book.get_transaction("tx-new")["input"], "continue what we were doing earlier")
            self.assertEqual(len(model.calls), 2)
            self.assertIn("NOTEBOOK_RECOVERY", json.dumps(model.calls[1]))
            event = book.db.execute(
                "SELECT payload FROM events WHERE tx='tx-new' AND kind='CONTEXT_NOTEBOOK_RECOVERED'"
            ).fetchone()
            self.assertIsNotNone(event)
            self.assertEqual(json.loads(event["payload"])["source_tx"], "tx-old")
        finally:
            book.close()

    def test_multiple_verified_topics_require_human_friendly_confirmation_and_no_model_call(self):
        vault, book, binding, model, wrapped, router = self._fixture()
        try:
            wrapped.run("tx-model", binding["hcid"], "continue the sharded model loader manifest verification")
            wrapped.run("tx-inbox", binding["hcid"], "improve inbox classifier automation")
            before = len(model.calls)
            response = wrapped.run("tx-recover", binding["hcid"], "continue the earlier work")
            self.assertEqual(len(model.calls), before)
            self.assertIn("Context confirmation required", response)
            self.assertIn("Verified Sharded Model Artifact Loader", response)
            self.assertIn("Inbox Librarian", response)
            self.assertNotIn("tx-model", response)
            self.assertNotIn("tx-inbox", response)
            self.assertEqual(book.get_transaction("tx-recover")["status"], "CHECKPOINTED")
        finally:
            book.close()

    def test_tampered_notebook_evidence_fails_closed_without_model_call(self):
        vault, book, binding, model, wrapped, router = self._fixture()
        try:
            wrapped.run("tx-model", binding["hcid"], "continue the sharded model loader manifest verification")
            before = len(model.calls)
            with mock.patch.object(book, "verify", side_effect=RuntimeError("audit chain tamper")):
                route = router.inspect_history(
                    book, "continue what we were doing earlier", current_tx="tx-recover")
            self.assertEqual(len(model.calls), before)
            self.assertTrue(route.requires_confirmation)
            self.assertIn("failed integrity verification", route.reason)
        finally:
            book.close()

    def test_unverified_or_unfinished_transaction_is_not_historical_authority(self):
        vault, book, binding, model, wrapped, router = self._fixture()
        try:
            book.start(binding["hcid"], "tx-open", "continue the model loader")
            book.event("tx-open", "CONTEXT_ROUTE", {
                "applicable": True, "workspace_id": "WS-HUMANOS", "decision": "CONTINUE",
                "selected_workstream": "HOS-MAL-001", "candidates": [],
                "reason": "test", "requires_confirmation": False, "origin": "REQUEST",
            })
            route = router.inspect_history(book, "continue what we were doing earlier", current_tx="tx-new")
            self.assertTrue(route.requires_confirmation)
            self.assertIsNone(route.selected_workstream)
        finally:
            book.close()

    def test_historical_source_tx_is_host_only(self):
        vault, book, binding, model, wrapped, router = self._fixture()
        try:
            wrapped.run("tx-model", binding["hcid"], "continue the sharded model loader manifest verification")
            route = router.inspect_history(book, "go back to that model thing from earlier", current_tx="tx-new")
            self.assertEqual(route.source_tx, "tx-model")
            self.assertNotIn("tx-model", json.dumps(route.model_context()))
        finally:
            book.close()

    def test_most_recent_history_resolves_newest_eligible_workstream(self):
        vault, book, binding, model, wrapped, router = self._fixture()
        try:
            wrapped.run("tx-model", binding["hcid"], "continue the sharded model loader manifest verification")
            wrapped.run("tx-inbox", binding["hcid"], "improve inbox classifier automation")
            route = router.inspect_history(
                book, "continue the most recent work", current_tx="tx-new")
            self.assertEqual(route.origin, "NOTEBOOK_RECOVERY")
            self.assertEqual(route.decision, "CONTINUE")
            self.assertEqual(route.selected_workstream, "HOS-INBOX-001")
            self.assertEqual(route.source_tx, "tx-inbox")
        finally:
            book.close()

    def test_ordinary_new_chat_does_not_trigger_historical_recovery(self):
        vault, book, binding, model, wrapped, router = self._fixture()
        try:
            wrapped.run("tx-model", binding["hcid"], "continue the sharded model loader manifest verification")
            route = router.inspect_history(book, "hello, how are you?", current_tx="tx-new")
            self.assertNotEqual(route.origin, "NOTEBOOK_RECOVERY")
        finally:
            book.close()


if __name__ == "__main__":
    unittest.main()
