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
        self.assertEqual([a["tool"] for a in result["actions"]
                          if a["event"] == "TOOL_OBSERVED"],
                         ["list_files", "inspect_diff", "read_file", "run_test"])
        self.assertTrue(all(a["status"] in ("OK", "PASS") for a in result["actions"]))
        self.assertIn("return x + 2", model.calls[3])
        self.assertIn("OBS-004", model.calls[-1])
        self.assertNotIn("return x + 2", json.dumps(result))
        self.assertFalse(result["release_authorized"])
        self.assertEqual(self.git("rev-parse", "runtime-0.1"), self.base)

    def test_model_authored_declarative_probe_checks_guard(self):
        model = ScriptedInvestigator(
            tool("read_file", path="feature.py"),
            tool("run_probe", case="home_alias_guard", expect="DENY",
                 rationale="Prove canonical home alias is denied"),
            final("OBS-002"),
        )
        result = self.run_agent(model, max_steps=3)
        self.assertEqual(result["state"], "COMPLETED")
        self.assertEqual(result["actions"][1]["status"], "PASS")
        self.assertEqual(result["qa_verdict"], "INCONCLUSIVE")

    def test_probe_detects_unsafe_alias_even_if_model_claims_pass(self):
        (self.repo / "engine.py").write_text(
            "class Tools:\n"
            "    def __init__(self, workspace): pass\n")
        self.git("add", ".")
        self.git("commit", "-qm", "synthetic vulnerable tool")
        self.head = self.git("rev-parse", "HEAD")
        model = ScriptedInvestigator(
            tool("read_file", path="engine.py"),
            tool("run_probe", case="home_alias_guard", expect="DENY",
                 rationale="Verify HOME is forbidden"),
            final("OBS-002"),
        )
        result = self.run_agent(model, max_steps=3)
        self.assertEqual(result["actions"][1]["status"], "FAIL")
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
        model = ScriptedInvestigator(
            tool("read_file", path="tests/test_synthetic.py"),
            tool("run_test", file="test_synthetic.py"),
            final("OBS-002"))
        result = self.run_agent(model, max_steps=3,
                                failure_log_base=evidence / "qa-v2.json")
        self.assertEqual(result["qa_verdict"], "FAIL")
        logs = list(evidence.glob("*.log"))
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].stat().st_mode & 0o077, 0)
        self.assertIn(b"SYNTHETIC_FAILURE", logs[0].read_bytes())
        self.assertNotIn(str(evidence), json.dumps(result))
        self.assertIn("OBS-001", model.calls[1])
        self.assertIn("OBS-002", model.calls[2])


    def test_premature_final_rejected_until_independent_test_performed(self):
        empty = {"final": {"summary": "I finished, but haven't tested the changed code myself.",
                           "findings": []}}
        model = ScriptedInvestigator(
            tool("read_file", path="feature.py"),
            empty,
            tool("run_test", file="test_synthetic.py"),
            final("OBS-002"),
        )
        result = self.run_agent(model, max_steps=4)
        self.assertEqual(result["state"], "COMPLETED")
        self.assertTrue(result["investigation_coverage"]["complete"])
        self.assertIn("PREMATURE_FINAL",
                      [step["event"] for step in result["actions"]])
        self.assertIn("missing_evidence", model.calls[2])
        self.assertEqual([step["tool"] for step in result["actions"]
                          if step["event"] == "TOOL_OBSERVED"],
                         ["read_file", "run_test"])
        self.assertFalse(result["release_authorized"])

    def test_no_targeted_test_never_counts_as_completed(self):
        model = ScriptedInvestigator(
            tool("read_file", path="feature.py"),
            {"final": {"summary": "Source inspected, but no independent test was actually executed.",
                       "findings": []}},
            {"final": {"summary": "Repeating a completion claim without independent test evidence.",
                       "findings": []}},
        )
        result = self.run_agent(model, max_steps=2)
        self.assertEqual(result["state"], "STEP_BUDGET_EXHAUSTED")
        self.assertIsNone(result["final"])
        self.assertFalse(result["investigation_coverage"]["complete"])
        self.assertFalse(result["release_authorized"])


    def test_placeholder_report_rejected_until_specific_report(self):
        placeholder = {"final": {
            "summary": "bounded assessment",
            "findings": [{
                "severity": "LOW", "description": "falsifiable concern",
                "observations": ["OBS-002"]}]
        }}
        model = ScriptedInvestigator(
            tool("read_file", path="feature.py"),
            tool("run_test", file="test_synthetic.py"),
            placeholder,
            final("OBS-002"),
        )
        result = self.run_agent(model, max_steps=4)
        self.assertEqual(result["state"], "COMPLETED")
        self.assertEqual(result["report_origin"], "HOST_VERIFIED_OBSERVATIONS")
        self.assertEqual(result["model_advisory"]["state"], "UNUSABLE_ADVISORY")
        self.assertTrue(result["investigation_coverage"]["complete"])
        self.assertIn("HOST-VERIFIED QA", result["final"]["summary"])

    def test_duplicate_inspection_is_rejected_and_model_can_recover(self):
        model = ScriptedInvestigator(
            tool("read_file", path="feature.py"),
            tool("read_file", path="feature.py"),
            tool("run_test", file="test_synthetic.py"),
            final("OBS-002"),
        )
        result = self.run_agent(model, max_steps=4)
        self.assertEqual(result["state"], "COMPLETED")
        self.assertIn("REPEATED_ACTION_REJECTED",
                      [step["event"] for step in result["actions"]])
        self.assertEqual(sum(step["event"] == "TOOL_OBSERVED"
                             for step in result["actions"]), 2)

    def test_system_policy_stays_present_with_rolling_observations(self):
        model = ScriptedInvestigator(
            tool("list_files"), tool("inspect_diff", path="feature.py"),
            tool("read_file", path="feature.py"),
            tool("run_test", file="test_synthetic.py"),
            final("OBS-004"),
        )
        result = self.run_agent(model, max_steps=5)
        self.assertEqual(result["state"], "COMPLETED")
        import json as _json
        self.assertTrue(all(_json.loads(call)[0]["role"] == "system"
                            for call in model.calls))


    def test_malformed_tool_shape_gets_bounded_repair_and_reaches_test(self):
        model = ScriptedInvestigator(
            tool("read_file", path="feature.py"),
            {"tool": {"name": "run_test"}},
            tool("run_test", file="test_synthetic.py"),
            final("OBS-002"),
        )
        result = self.run_agent(model, max_steps=4)
        self.assertEqual(result["state"], "COMPLETED")
        self.assertEqual(result["schema_repair_attempts"], 1)
        self.assertTrue(result["investigation_coverage"]["complete"])
        self.assertEqual(
            [item["tool"] for item in result["actions"]
             if item["event"] == "TOOL_OBSERVED"],
            ["read_file", "run_test"],
        )
        self.assertIn("INVALID_PROPOSAL_SHAPE", model.calls[2])
        self.assertIn("test_synthetic.py", model.calls[2])
        self.assertFalse(result["release_authorized"])

    def test_local_model_json_format_error_gets_one_retry(self):
        class FormatOnce(ScriptedInvestigator):
            def structured(self, messages, timeout):
                self.calls.append(json.dumps(messages))
                if len(self.calls) == 2:
                    raise ValueError("invalid JSON from synthetic local model")
                return self.actions.pop(0)
        model = FormatOnce(tool("read_file", path="feature.py"),
                           tool("run_test", file="test_synthetic.py"),
                           final("OBS-002"))
        result = self.run_agent(model, max_steps=4)
        self.assertEqual(result["state"], "COMPLETED")
        self.assertEqual(result["schema_repair_attempts"], 1)
        self.assertIn("MODEL_FORMAT_REJECTED",
                      [item["event"] for item in result["actions"]])
        self.assertTrue(result["investigation_coverage"]["complete"])

    def test_three_rejected_model_shapes_fail_closed(self):
        model = ScriptedInvestigator(
            {"tool": {"name": "read_file"}},
            {"tool": {"name": "read_file"}},
            {"tool": {"name": "read_file"}},
        )
        result = self.run_agent(model, max_steps=3)
        self.assertEqual(result["state"], "MODEL_OR_SCHEMA_FAILURE")
        self.assertEqual(result["schema_repair_attempts"], 3)
        self.assertIsNone(result["final"])
        self.assertEqual(result["actions"][-1]["event"], "REJECTED_PROPOSAL")
        self.assertFalse(result["release_authorized"])

    def test_invalid_tool_authority_is_denied_not_retried(self):
        model = ScriptedInvestigator(tool("shell", command="echo unsafe"))
        result = self.run_agent(model)
        self.assertEqual(result["state"], "POLICY_DENIED")
        self.assertEqual(result["schema_repair_attempts"], 0)
        self.assertEqual(len(model.calls), 1)
        self.assertFalse(result["release_authorized"])

    def test_host_test_priority_is_sent_after_changed_source_read(self):
        model = ScriptedInvestigator(
            tool("read_file", path="feature.py"),
            tool("run_test", file="test_synthetic.py"),
            final("OBS-002"),
        )
        result = self.run_agent(model, max_steps=3)
        self.assertEqual(result["state"], "COMPLETED")
        self.assertIn("test_synthetic.py", model.calls[1])
        self.assertIn("Choose a fresh run_test", model.calls[1])
        self.assertNotIn("SYNTHETIC_FAILURE", json.dumps(result))


    def test_weak_final_enters_report_only_and_blocks_unneeded_tools(self):
        model = ScriptedInvestigator(
            tool("read_file", path="feature.py"),
            tool("run_test", file="test_synthetic.py"),
            {"final": {"summary": "bounded assessment", "findings": []}},
            tool("read_file", path="feature.py"),
            final("OBS-002"),
        )
        result = self.run_agent(model, max_steps=5)
        self.assertEqual(result["state"], "COMPLETED")
        self.assertTrue(result["report_phase_entered"])
        self.assertEqual(result["model_advisory"]["state"], "UNUSABLE_ADVISORY")
        self.assertEqual([row["tool"] for row in result["actions"]
                          if row["event"] == "TOOL_OBSERVED"],
                         ["read_file", "run_test"])
        self.assertEqual(len(model.calls), 3)
        self.assertEqual(result["report_origin"], "HOST_VERIFIED_OBSERVATIONS")
        self.assertFalse(result["release_authorized"])

    def test_extra_tool_argument_is_correctable_without_execution(self):
        model = ScriptedInvestigator(
            tool("read_file", path="feature.py"),
            tool("run_test", file="test_synthetic.py"),
            {"final": {"summary": "bounded assessment", "findings": []}},
            {"tool": {"name": "read_file",
                      "arguments": {"path": "feature.py", "note": "extraneous"}}},
            final("OBS-002"),
        )
        result = self.run_agent(model, max_steps=5)
        self.assertEqual(result["state"], "COMPLETED")
        self.assertEqual(result["schema_repair_attempts"], 0)
        self.assertTrue(result["report_phase_entered"])
        self.assertEqual(sum(item["event"] == "TOOL_OBSERVED"
                             for item in result["actions"]), 2)
        self.assertEqual(result["model_advisory"]["state"], "UNUSABLE_ADVISORY")
        self.assertEqual(result["report_origin"], "HOST_VERIFIED_OBSERVATIONS")

    def test_extraneous_arguments_cannot_hide_unsafe_path(self):
        model = ScriptedInvestigator(
            {"tool": {"name": "read_file", "arguments": {
                "path": "../secrets.txt", "note": "extra"}}})
        result = self.run_agent(model)
        self.assertEqual(result["state"], "POLICY_DENIED")
        self.assertEqual(result["schema_repair_attempts"], 0)
        self.assertEqual(len(model.calls), 1)
        self.assertFalse(result["release_authorized"])

    def test_extraneous_arguments_cannot_hide_unapproved_probe(self):
        model = ScriptedInvestigator(
            {"tool": {"name": "run_probe", "arguments": {
                "case": "unapproved_probe", "expect": "DENY",
                "rationale": "Synthetic", "note": "extra"}}})
        result = self.run_agent(model)
        self.assertEqual(result["state"], "POLICY_DENIED")
        self.assertEqual(result["schema_repair_attempts"], 0)
        self.assertFalse(result["release_authorized"])

    def test_reports_cannot_complete_if_model_keeps_asking_for_tools(self):
        model = ScriptedInvestigator(
            tool("read_file", path="feature.py"),
            tool("run_test", file="test_synthetic.py"),
            {"final": {"summary": "bounded assessment", "findings": []}},
            tool("inspect_diff", path="feature.py"),
            tool("list_files"),
        )
        result = self.run_agent(model, max_steps=4)
        self.assertEqual(result["state"], "COMPLETED")
        self.assertTrue(result["report_phase_entered"])
        self.assertEqual(result["report_origin"], "HOST_VERIFIED_OBSERVATIONS")
        self.assertIsNotNone(result["final"])
        self.assertEqual(result["qa_verdict"], "INCONCLUSIVE")
        self.assertEqual(result["model_advisory"]["state"], "UNUSABLE_ADVISORY")
        self.assertFalse(result["release_authorized"])


    def test_bad_model_advisory_cannot_overrule_verified_qa(self):
        model = ScriptedInvestigator(
            tool("read_file", path="feature.py"),
            tool("run_test", file="test_synthetic.py"),
            {"final": {"summary": "bounded assessment", "findings": []}},
        )
        result = self.run_agent(model, max_steps=2)
        self.assertEqual(result["state"], "COMPLETED")
        self.assertEqual(result["report_origin"], "HOST_VERIFIED_OBSERVATIONS")
        self.assertEqual(result["model_advisory"]["state"], "UNUSABLE_ADVISORY")
        self.assertIn("feature.py", result["final"]["summary"])
        self.assertIn("OBS-002", result["final"]["summary"])
        self.assertEqual(result["final"]["findings"], [])
        self.assertFalse(result["release_authorized"])

    def test_offline_during_synthesis_preserves_verified_observations(self):
        class FailsSynthesis(ScriptedInvestigator):
            def structured(self, messages, timeout):
                self.calls.append(json.dumps(messages))
                if len(self.calls) == 3:
                    raise OSError("Synthetic local model unavailable")
                return self.actions.pop(0)
        model = FailsSynthesis(
            tool("read_file", path="feature.py"),
            tool("run_test", file="test_synthetic.py"))
        result = self.run_agent(model, max_steps=2)
        self.assertEqual(result["state"], "COMPLETED")
        self.assertEqual(result["model_advisory"]["state"],
                         "MODEL_FORMAT_OR_PROVIDER_FAILED")
        self.assertEqual(result["report_origin"], "HOST_VERIFIED_OBSERVATIONS")
        self.assertFalse(result["release_authorized"])

    def test_shell_request_after_coverage_still_hard_denied(self):
        model = ScriptedInvestigator(
            tool("read_file", path="feature.py"),
            tool("run_test", file="test_synthetic.py"),
            tool("shell", command="rm -rf /"),
        )
        result = self.run_agent(model, max_steps=2)
        self.assertEqual(result["state"], "POLICY_DENIED")
        self.assertEqual(result["model_advisory"]["state"],
                         "UNAUTHORIZED_TOOL_PROPOSED")
        self.assertIsNone(result["final"])
        self.assertFalse(result["release_authorized"])

    def test_failed_focused_check_cannot_be_promoted_by_host_report(self):
        (self.repo / "tests/test_synthetic.py").write_text(
            "import unittest\nclass Demo(unittest.TestCase):\n"
            "    def test_example(self): self.fail('SYNTHETIC_BUG')\n")
        self.git("add", ".")
        self.git("commit", "-qm", "known broken target")
        self.head = self.git("rev-parse", "HEAD")
        model = ScriptedInvestigator(
            tool("read_file", path="tests/test_synthetic.py"),
            tool("run_test", file="test_synthetic.py"),
            {"final": {"summary": "The tested build passed completely.",
                       "findings": []}},
        )
        result = self.run_agent(model, max_steps=2)
        self.assertEqual(result["state"], "COMPLETED")
        self.assertTrue(result["tests_failed"])
        self.assertEqual(result["qa_verdict"], "FAIL")
        self.assertEqual(result["final"]["findings"][0]["severity"], "HIGH")
        self.assertEqual(result["final"]["findings"][0]["observations"], ["OBS-002"])
        self.assertFalse(result["release_authorized"])


    def test_unsafe_postcoverage_path_request_is_still_denied(self):
        model = ScriptedInvestigator(
            tool("read_file", path="feature.py"),
            tool("run_test", file="test_synthetic.py"),
            tool("read_file", path="../secret.py"),
        )
        result = self.run_agent(model, max_steps=2)
        self.assertEqual(result["state"], "POLICY_DENIED")
        self.assertEqual(result["model_advisory"]["state"],
                         "UNAUTHORIZED_TOOL_PROPOSED")
        self.assertIsNone(result["final"])
        self.assertEqual(sum(a["event"] == "TOOL_OBSERVED"
                             for a in result["actions"]), 2)
        self.assertFalse(result["release_authorized"])

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
        self.assertEqual([x["tool"] for x in report["agentic"]["actions"]
                          if x["event"] == "TOOL_OBSERVED"],
                         ["read_file", "run_test"])
        self.assertFalse(report["release_authorized"])
        self.assertFalse(report["agentic"]["release_authorized"])
