import json
import unittest
import test_runtime
from references import bind_choice, resolve_reference
from runtime_info import format_observation


class ConversationalReferenceTests(unittest.TestCase):
    setUp = test_runtime.RuntimeTests.setUp
    tearDown = test_runtime.RuntimeTests.tearDown
    agent = test_runtime.RuntimeTests.agent
    turn = test_runtime.RuntimeTests.turn

    def _list(self, *names):
        for name in names:
            (self.workspace / name).write_text("content:" + name)
        agent = self.agent(
            {"tool": {"name": "list_files", "path": "."}},
            {"final": "Listed."},
        )
        self.turn(agent, "list files", tx="list-tx")
        frame = self.book.task("list-tx").get("reference_frame")
        self.assertEqual(frame["paths"], sorted(names))

    def test_single_verified_file_resolves_read_that_file(self):
        self._list("runtime-check.txt")
        agent = self.agent()
        result = agent.run("read-tx", self.binding["hcid"], "read that file")
        self.assertIn("File: runtime-check.txt", result)
        self.assertIn("content:runtime-check.txt", result)
        scope = self.book.task("read-tx")["permissions"]
        self.assertEqual(scope["read_paths"], ["runtime-check.txt"])
        self.assertNotIn("that", scope["read_paths"])

    def test_multiple_files_require_clarification_without_tty_choice(self):
        self._list("a.txt", "b.txt")
        agent = self.agent()
        result = agent.run("read-tx", self.binding["hcid"], "read that file")
        self.assertIn("Which file do you mean?", result)
        self.assertIn("a.txt", result)
        self.assertIn("b.txt", result)
        self.assertEqual(agent.model.calls, [])

    def test_verified_human_menu_choice_binds_exact_file(self):
        self._list("a.txt", "b.txt")
        resolution = resolve_reference(
            self.book, self.binding["hcid"], "read-tx", "read that file", self.workspace
        )
        binding = bind_choice(resolution, "b.txt")
        result = self.agent().run(
            "read-tx", self.binding["hcid"], "read that file", reference_binding=binding
        )
        self.assertIn("File: b.txt", result)
        self.assertIn("content:b.txt", result)
        event = self.book.db.execute(
            "SELECT payload FROM events WHERE tx='read-tx' AND kind='REFERENCE_BOUND'"
        ).fetchone()
        self.assertEqual(json.loads(event[0])["mode"], "human_menu")

    def test_reference_frame_tamper_fails_closed(self):
        self._list("a.txt")
        resolution = resolve_reference(
            self.book, self.binding["hcid"], "read-tx", "read that file", self.workspace
        )
        binding = resolution["binding"]
        state = self.book.task("list-tx")
        state["reference_frame"]["paths"].append("secret.txt")
        self.book.save_task("list-tx", state)
        with self.assertRaisesRegex(PermissionError, "integrity"):
            self.agent().run(
                "read-tx", self.binding["hcid"], "read that file", reference_binding=binding
            )

    def test_denial_message_never_claims_workspace_is_read_only(self):
        message = format_observation(
            {"name": "read_file", "path": "secret.txt"},
            {
                "ok": False,
                "stdout": "",
                "stderr": "PermissionError: HumanOS policy did not authorize this request",
                "artifacts": [],
                "authorization": "DENIED",
            },
        )
        self.assertIn("did not authorize that exact request", message)
        self.assertIn("does not mean the workspace is read-only", message)


class ContextReferencePlanTests(unittest.TestCase):
    setUp = test_runtime.RuntimeTests.setUp
    tearDown = test_runtime.RuntimeTests.tearDown
    agent = test_runtime.RuntimeTests.agent
    turn = test_runtime.RuntimeTests.turn

    def _plan(self):
        (self.workspace / "a.txt").write_text("a")
        agent = self.agent(
            {"tool": {"name": "plan_move", "source": "a.txt", "destination": "Archive/a.txt"}},
            {"final": "Plan ready."},
        )
        self.turn(agent, "/move a.txt Archive/a.txt", tx="plan-tx")
        frame = self.book.task("plan-tx").get("reference_frame")
        self.assertEqual(frame["kind"], "plan")
        self.assertEqual(len(frame["paths"]), 1)
        return frame["paths"][0]

    def test_do_it_binds_recent_verified_plan(self):
        plan_id = self._plan()
        resolution = resolve_reference(self.book, self.binding["hcid"], "apply-tx", "do it", self.workspace)
        self.assertEqual(resolution["status"], "resolved")
        self.assertEqual(resolution["binding"]["kind"], "plan")
        self.assertEqual(resolution["binding"]["path"], plan_id)

    def test_do_it_becomes_exact_apply_plan_request(self):
        plan_id = self._plan()
        resolution = resolve_reference(self.book, self.binding["hcid"], "apply-tx", "do it", self.workspace)
        from runtime_info import request_for
        request = request_for("do it", [], reference_binding=resolution["binding"])
        self.assertEqual(request, {"name": "apply_plan", "plan_id": plan_id})

    def test_plan_binding_cannot_be_retyped_as_file_authority(self):
        self._plan()
        resolution = resolve_reference(self.book, self.binding["hcid"], "apply-tx", "do it", self.workspace)
        binding = dict(resolution["binding"])
        binding["kind"] = "file"
        from references import validate_reference_binding
        with self.assertRaisesRegex(PermissionError, "kind"):
            validate_reference_binding(self.book, binding, self.binding["hcid"], "read that file")


class ContextReferenceExplicitAuthorityTests(unittest.TestCase):
    setUp = test_runtime.RuntimeTests.setUp
    tearDown = test_runtime.RuntimeTests.tearDown

    def test_explicit_apply_command_is_never_reference_resolved(self):
        from references import reference_intent
        self.assertIsNone(reference_intent('/apply PLAN-EXACT-123'))
        self.assertIsNone(reference_intent('/undo PLAN-EXACT-123'))
