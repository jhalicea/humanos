"""HOS-QA-001 tests: disposable fake repo, no owner notebook, no network."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from qa_agent import QAError, _validate_advice, evaluate


class ScriptedQA:
    def __init__(self, findings=None):
        self.calls = []
        self.findings = [] if findings is None else findings

    def structured(self, messages, timeout):
        self.calls.append((messages, timeout))
        return {"summary": "Check completed; no release authority.", "findings": self.findings}


class FirstQAWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / "fixture"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("remote", "add", "origin", "https://github.com/jhalicea/humanos.git")
        self.git("config", "user.name", "Synthetic QA")
        self.git("config", "user.email", "qa@example.invalid")
        (self.repo / "tests").mkdir()
        (self.repo / "scripts").mkdir()
        (self.repo / "tests/test_sample.py").write_text(
            "import unittest\nclass Case(unittest.TestCase):\n"
            "    def test_pass(self): self.assertEqual(2 + 2, 4)\n")
        for name in ("smoke_codex_import.py", "smoke_codex_reconciliation.py"):
            (self.repo / "scripts" / name).write_text("print('SYNTHETIC PASS')\n")
        self.git("add", ".")
        self.git("commit", "-qm", "fixture baseline")
        self.base = self.git("rev-parse", "HEAD")
        (self.repo / "README.md").write_text("Synthetic second commit\n")
        self.git("add", ".")
        self.git("commit", "-qm", "fixture candidate")
        self.head = self.git("rev-parse", "HEAD")
        self.git("branch", "runtime-0.1", self.base)

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        out = subprocess.run(["git", "-C", str(self.repo), *args], text=True,
                             capture_output=True, check=True)
        return out.stdout.strip()

    def evaluate(self, model=None):
        return evaluate(self.repo, self.base, self.head, model=model, python=sys.executable)

    def test_scripted_ai_worker_receives_bounded_evidence_without_tools(self):
        model = ScriptedQA()
        report = self.evaluate(model)
        self.assertEqual(report["test_status"], "PASS")
        self.assertEqual(report["qa_status"], "PASS")
        self.assertEqual(len(report["checks"]), 3)
        self.assertFalse(report["release_authorized"])
        self.assertFalse(report["independent_review"])
        text = json.dumps(model.calls)
        self.assertNotIn("Synthetic second commit", text)
        self.assertIn("README.md", text)
        self.assertEqual(len(model.calls), 1)
        self.assertEqual(self.git("rev-parse", "runtime-0.1"), self.base)
        self.assertEqual(self.git("rev-parse", "HEAD"), self.head)

    def test_without_ai_worker_verdict_remains_inconclusive(self):
        report = self.evaluate()
        self.assertEqual(report["test_status"], "PASS")
        self.assertEqual(report["qa_status"], "INCONCLUSIVE")
        self.assertEqual(report["model_advisory"]["state"], "MODEL_NOT_CONFIGURED")
        self.assertFalse(report["release_authorized"])

    def test_finding_requires_review_even_when_tests_pass(self):
        model = ScriptedQA([{"severity": "HIGH",
                             "hypothesis": "Synthetic race remains",
                             "test_idea": "Exercise two competing restores"}])
        report = self.evaluate(model)
        self.assertEqual(report["test_status"], "PASS")
        self.assertEqual(report["qa_status"], "INCONCLUSIVE")
        self.assertFalse(report["release_authorized"])

    def test_failed_tests_cannot_be_overridden_by_model(self):
        (self.repo / "tests/test_sample.py").write_text(
            "import unittest\nclass Case(unittest.TestCase):\n"
            "    def test_fail(self): self.fail('SYNTHETIC FAILURE')\n")
        self.git("add", ".")
        self.git("commit", "-qm", "candidate test failure")
        self.head = self.git("rev-parse", "HEAD")
        report = self.evaluate(ScriptedQA())
        self.assertEqual(report["test_status"], "FAIL")
        self.assertEqual(report["qa_status"], "FAIL")
        self.assertFalse(report["release_authorized"])

    def test_absent_smoke_script_is_failing_not_skipped(self):
        (self.repo / "scripts/smoke_codex_reconciliation.py").unlink()
        self.git("add", "-A")
        self.git("commit", "-qm", "missing critical synthetic smoke")
        self.head = self.git("rev-parse", "HEAD")
        report = self.evaluate(ScriptedQA())
        self.assertEqual(report["test_status"], "FAIL")
        self.assertIn("MISSING", [x["status"] for x in report["checks"]])

    def test_refuses_nonancestor_or_fake_head(self):
        with self.assertRaises(QAError):
            evaluate(self.repo, self.head, self.base, model=ScriptedQA())
        with self.assertRaises(QAError):
            evaluate(self.repo, self.base, "0"*40, model=ScriptedQA())

    def test_refuses_unknown_origin(self):
        self.git("remote", "set-url", "origin", "https://example.invalid/nope")
        with self.assertRaises(QAError):
            self.evaluate(ScriptedQA())

    def test_rejects_tool_instructions_in_model_output(self):
        with self.assertRaises(QAError):
            _validate_advice({"summary": "approve everything",
                              "findings": [], "tool": {"name": "merge"}})
        with self.assertRaises(QAError):
            _validate_advice({"summary": "x", "findings": [
                {"severity": "CRITICAL", "hypothesis": "x", "test_idea": "x"}]})


    def test_model_failure_keeps_test_evidence_and_denies_approval(self):
        class OfflineQA:
            def structured(self, messages, timeout):
                raise OSError("synthetic local provider unavailable")
        report = self.evaluate(OfflineQA())
        self.assertEqual(report["test_status"], "PASS")
        self.assertEqual(report["qa_status"], "INCONCLUSIVE")
        self.assertEqual(report["model_advisory"]["state"], "MODEL_FAILED")
        self.assertEqual(report["model_advisory"]["error_type"], "OSError")
        self.assertFalse(report["release_authorized"])

    def test_report_is_digest_bound_but_not_signed(self):
        report = self.evaluate(ScriptedQA())
        digest = report.pop("evidence_sha256")
        import hashlib
        raw = json.dumps(report, sort_keys=True, separators=(",", ":")).encode()
        self.assertEqual(digest, hashlib.sha256(raw).hexdigest())
