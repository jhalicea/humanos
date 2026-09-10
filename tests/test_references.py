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
