"""HOS-QA-001 v2 model-selected investigation against fully synthetic Git fixtures."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
import io
import qa_agent

from qa_agent import QAError
from qa_investigator import investigate, _proposal, SYSTEM


class ScriptedInvestigator:
    def __init__(self, *actions):
        self.actions = list(actions)
        self.calls = []

    def structured(self, messages, timeout):
        self.calls.append(json.dumps(messages))
        return self.actions.pop(0)


def tool(name, **arguments):
    return {"tool": {"name": name, "arguments": arguments}}


def final(evidence="OBS-001"):
    return {"final": {"summary": "Bounded synthetic investigation complete.",
                      "findings": [{"severity": "LOW",
                                    "description": "Tested behavior is limited to fixtures.",
                                    "observations": [evidence]}]}}


class QAInvestigationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / "repository"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Synthetic Investigator")
        self.git("config", "user.email", "local@example.invalid")
        self.git("remote", "add", "origin", "https://github.com/jhalicea/humanos.git")
        (self.repo / "tests").mkdir()
        (self.repo / "scripts").mkdir()
        for name in ("smoke_codex_import.py", "smoke_codex_reconciliation.py"):
            (self.repo / "scripts" / name).write_text(
                "print('SYNTHETIC QA SMOKE PASS')\n", encoding="utf-8")
        (self.repo / "tests/test_synthetic.py").write_text(
            "import unittest\nclass Demo(unittest.TestCase):\n"
            "    def test_example(self): self.assertTrue(True)\n", encoding="utf-8")
        (self.repo / "engine.py").write_text(
            "class Tools:\n"
            "    def __init__(self, workspace):\n"
            "        from pathlib import Path\n"
            "        if Path(workspace).resolve() == Path.home().resolve():\n"
            "            raise PermissionError('dedicated work folder')\n",
            encoding="utf-8")
        (self.repo / "feature.py").write_text("def calculate(x): return x + 1\n")
        self.git("add", ".")
        self.git("commit", "-qm", "synthetic baseline")
        self.base = self.git("rev-parse", "HEAD")
        (self.repo / "feature.py").write_text("def calculate(x): return x + 2\n")
        self.git("add", ".")
        self.git("commit", "-qm", "synthetic target")
        self.head = self.git("rev-parse", "HEAD")
        self.git("branch", "runtime-0.1", self.base)

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args],
                              check=True, capture_output=True, text=True).stdout.strip()

    def run_agent(self, model, **opts):
        return investigate(self.repo, self.base, self.head, model,
                           python=sys.executable, **opts)

    def test_model_selects_inspects_runs_and_adapts(self):
        model = ScriptedInvestigator(
            tool("list_files"),
            tool("inspect_diff", path="feature.py"),
            tool("read_file", path="feature.py"),
            tool("run_test", file="test_synthetic.py"),
            final("OBS-004"),
        )
        result = self.run_agent(model, max_steps=5)
        self.assertEqual(result["state"], "COMPLETED")
        self.assertEqual(result["qa_verdict"], "INCONCLUSIVE")
        self.assertEqual([a["tool"] for a in result["actions"]],
                         ["list_files", "inspect_diff", "read_file", "run_test"])
        self.assertTrue(all(a["status"] in ("OK", "PASS") for a in result["actions"]))
        self.assertIn("return x + 2", model.calls[3])
        self.assertIn("OBS-004", model.calls[-1])
        self.assertNotIn("return x + 2", json.dumps(result))
        self.assertFalse(result["release_authorized"])
        self.assertEqual(self.git("rev-parse", "runtime-0.1"), self.base)

    def test_model_authored_declarative_probe_checks_guard(self):
        model = ScriptedInvestigator(
            tool("run_probe", case="home_alias_guard", expect="DENY",
                 rationale="Prove canonical home alias is denied"),
            final(),
        )
        result = self.run_agent(model, max_steps=2)
        self.assertEqual(result["state"], "COMPLETED")
        self.assertEqual(result["actions"][0]["status"], "PASS")
        self.assertEqual(result["qa_verdict"], "INCONCLUSIVE")

    def test_probe_detects_unsafe_alias_even_if_model_claims_pass(self):
        (self.repo / "engine.py").write_text(
            "class Tools:\n"
            "    def __init__(self, workspace): pass\n")
        self.git("add", ".")
        self.git("commit", "-qm", "synthetic vulnerable tool")
        self.head = self.git("rev-parse", "HEAD")
        model = ScriptedInvestigator(
            tool("run_probe", case="home_alias_guard", expect="DENY",
                 rationale="Verify HOME is forbidden"),
            final(),
        )
        result = self.run_agent(model, max_steps=2)
        self.assertEqual(result["actions"][0]["status"], "FAIL")
        self.assertEqual(result["qa_verdict"], "FAIL")
        self.assertTrue(result["tests_failed"])
        self.assertFalse(result["release_authorized"])

    def test_model_cannot_run_commands_or_escape_paths(self):
        with self.assertRaisesRegex(QAError, "allowlisted"):
            _proposal(tool("shell", command="rm -rf /"), {})
        with self.assertRaisesRegex(QAError, "normalized"):
            _proposal(tool("read_file", path="../.env"), {})
        with self.assertRaisesRegex(QAError, "preapproved"):
            _proposal(tool("run_probe", case="home_alias_guard", expect="ALLOW",
                           rationale="Change the policy"), {})

    def test_unknown_observation_cannot_support_finding(self):
        model = ScriptedInvestigator(final("OBS-999"))
        result = self.run_agent(model)
        self.assertEqual(result["state"], "MODEL_OR_SCHEMA_FAILURE")
        self.assertIsNone(result["final"])
        self.assertEqual(result["qa_verdict"], "INCONCLUSIVE")

    def test_nontracked_source_rejected(self):
        model = ScriptedInvestigator(tool("read_file", path="secret.py"))
        report = self.run_agent(model)
        self.assertEqual(report["state"], "POLICY_DENIED")
        self.assertEqual(report["actions"][0]["tool"], "read_file")
        self.assertFalse(report["release_authorized"])

    def test_budget_enforced_without_implicit_completion(self):
        model = ScriptedInvestigator(tool("list_files"), tool("list_files"),
                                     tool("list_files"))
        report = self.run_agent(model, max_steps=2)
        self.assertEqual(report["state"], "STEP_BUDGET_EXHAUSTED")
        self.assertEqual(len(report["actions"]), 2)
        self.assertIsNone(report["final"])

    def test_offline_model_fails_closed(self):
        class Offline:
            def structured(self, messages, timeout):
                raise OSError("No model")
        report = self.run_agent(Offline())
        self.assertEqual(report["state"], "MODEL_OR_SCHEMA_FAILURE")
        self.assertFalse(report["release_authorized"])

    def test_private_failure_log_not_promoted_to_receipt(self):
        evidence = self.root / "evidence"
        evidence.mkdir(mode=0o700)
        (self.repo / "tests/test_synthetic.py").write_text(
            "import unittest\nclass Demo(unittest.TestCase):\n"
            "    def test_example(self): self.fail('SYNTHETIC_FAILURE')\n")
        self.git("add", ".")
        self.git("commit", "-qm", "synthetic failing test")
        self.head = self.git("rev-parse", "HEAD")
        model = ScriptedInvestigator(tool("run_test", file="test_synthetic.py"), final())
        result = self.run_agent(model, max_steps=2,
                                failure_log_base=evidence / "qa-v2.json")
        self.assertEqual(result["qa_verdict"], "FAIL")
        logs = list(evidence.glob("*.log"))
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].stat().st_mode & 0o077, 0)
        self.assertIn(b"SYNTHETIC_FAILURE", logs[0].read_bytes())
        self.assertNotIn(str(evidence), json.dumps(result))
        self.assertIn("OBS-001", model.calls[1])

    def test_cli_agentic_executes_real_tool_loop_and_reports_advisory_status(self):
        private = self.root / "evidence"
        private.mkdir(mode=0o700)
        output_path = private / "investigation-v2.json"
        proposals = [
            tool("read_file", path="feature.py"),
            tool("run_test", file="test_synthetic.py"),
            final("OBS-002"),
        ]
        argv = [
            "qa_agent.py", "--agentic", "--model", "synthetic-local-fixture",
            "--repo", str(self.repo), "--baseline", self.base,
            "--target", self.head, "--python", sys.executable,
            "--report", str(output_path),
        ]
        with patch("sys.argv", argv), patch(
            "engine.OllamaModel.structured", side_effect=proposals
        ), redirect_stdout(io.StringIO()):
            code = qa_agent.main()
        report = json.loads(output_path.read_text())
        self.assertEqual(code, 0, msg=json.dumps({
            "test_status": report.get("test_status"),
            "checks": report.get("checks"),
            "agentic_state": report.get("agentic", {}).get("state"),
            "agentic_actions": report.get("agentic", {}).get("actions"),
        }, sort_keys=True))
        self.assertEqual(report["test_status"], "PASS")
        self.assertEqual(report["qa_status"], "INCONCLUSIVE")
        self.assertEqual(report["agentic"]["state"], "COMPLETED")
        self.assertEqual([x["tool"] for x in report["agentic"]["actions"]],
                         ["read_file", "run_test"])
        self.assertFalse(report["release_authorized"])
        self.assertFalse(report["agentic"]["release_authorized"])
