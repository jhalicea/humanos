import tempfile
import unittest
from pathlib import Path

from engine import Agent, Tools
from notebook import Notebook


A4 = (
    "HUMANOS JOB HOS-R1-LOCAL-001-A4. Act as the local HumanOS capability auditor. "
    "First request the runtime capability registry using the appropriate available tool. "
    "Then report exactly: 1) verified working features; 2) five most important missing or incomplete features; "
    "3) one feature to build next; 4) evidence supporting each conclusion; "
    "5) exact local model identity only if directly observable, otherwise UNKNOWN."
)

GOOD = (
    "1) Working: runtime capability registry was observed.\n"
    "2) Missing: web research, provider routing, local vision, connectors, richer retrieval.\n"
    "3) Build next: a verified research workflow.\n"
    "4) Evidence: the host-provided runtime capability observation in this turn.\n"
    "5) UNKNOWN"
)


class SequenceModel:
    name = "local-test-model"

    def __init__(self):
        self.calls = 0

    def invoke(self, messages, timeout):
        self.calls += 1
        if self.calls == 1:
            return {"final": "Auditing Report: HOS-R1-LOCAL-001-A4"}
        return {"final": GOOD}


class AgentAcceptanceIntegrationTests(unittest.TestCase):
    def test_a4_bad_final_is_retried_without_fake_model_call_for_host_evidence(self):
        """Regression for the real A4 failure: host evidence is not a model call."""
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            vault = root / "vault"
            workspace = root / "workspace"
            core = root / "core"
            core.mkdir()
            model = SequenceModel()
            book = Notebook(vault)
            try:
                agent = Agent(book, model, Tools(workspace), core,
                              max_steps=3, max_seconds=30, finalize_on_error=False)
                binding = book.bind("Jon", A4)
                tx = "TX-ACCEPTANCE-A4"
                result = agent.run(tx, binding["hcid"], A4)

                self.assertEqual(result, GOOD)
                self.assertEqual(model.calls, 2)

                kinds = [row["kind"] for row in book.db.execute(
                    "SELECT kind FROM events WHERE tx=? ORDER BY seq", (tx,)).fetchall()]
                self.assertEqual(kinds.count("ACCEPTANCE_EVIDENCE_REQUIRED"), 1)
                self.assertEqual(kinds.count("ACCEPTANCE_EVIDENCE"), 1)
                self.assertEqual(kinds.count("ACCEPTANCE_FINAL_REJECTED"), 1)
                self.assertEqual(kinds.count("ACCEPTANCE_FINAL_PASSED"), 1)
                self.assertEqual(kinds.count("MODEL_REQUEST"), 2)
                self.assertEqual(kinds.count("MODEL_RESPONSE"), 2)

                state = book.task(tx)
                self.assertEqual(state["phase"], "COMPLETE")
                self.assertEqual(state["acceptance_evidence"], {"runtime_capabilities": "VERIFIED"})
            finally:
                book.close()


if __name__ == "__main__":
    unittest.main()
