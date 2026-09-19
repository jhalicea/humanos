import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from execution_contracts import (
    ContractError,
    FRIEND_PACKET_REQUIRED,
    StaleWorkOrderError,
    WORK_ORDER_REQUIRED,
    assert_executable_work_order,
    assert_work_order_fresh,
    observed_git_commit,
    validate_friend_packet,
    validate_work_order,
)


BASELINE = "13f22ee4310e4385b164d163d72c251e39a92055"
OTHER = "0" * 40


def work_order(status="APPROVED"):
    return {
        "schema_version": 1,
        "kind": "EXECUTION_WORK_ORDER",
        "work_order_id": "WO-TEST-001",
        "status": status,
        "objective": "Implement one bounded test slice.",
        "scope": ["execution contract validation"],
        "out_of_scope": ["dispatch"],
        "baseline": {
            "repository": "jhalicea/humanos",
            "ref": "runtime-0.1",
            "commit_sha": BASELINE,
        },
        "relevant_files": ["execution_contracts.py"],
        "constraints": ["No automatic dispatch."],
        "acceptance_tests": ["fresh baseline is accepted"],
        "security_requirements": ["fail closed on stale baseline"],
        "rollback": "Revert the candidate.",
        "assigned_workers": [],
        "known_unknowns": ["UNKNOWN: future dispatcher integration"],
        "provenance_references": [
            {"type": "commit", "reference": BASELINE},
            {"type": "test", "reference": "tests/test_execution_contracts.py"},
        ],
        "done_condition": "Schemas and enforcement tests pass.",
        "approval": {
            "approved_by": "Jon",
            "approved_at": "2026-09-18T22:07:00-04:00",
        },
        "privacy_classification": "INTERNAL",
    }


def friend_packet():
    return {
        "schema_version": 1,
        "kind": "FRIEND_PACKET",
        "packet_id": "FP-TEST-001",
        "work_order_id": "WO-TEST-001",
        "baseline_commit_sha": BASELINE,
        "worker_role": "implementation worker",
        "privacy_classification": "INTERNAL",
        "task": "Implement only the bounded test slice.",
        "known_evidence": ["Baseline commit is pinned."],
        "constraints": ["Do not widen scope."],
        "unknown_do_not_assume": ["UNKNOWN: future dispatcher integration"],
        "allowed_scope": ["execution_contracts.py"],
        "prohibited_actions": ["merge", "deploy", "delete"],
        "acceptance_criteria": ["tests pass"],
        "expected_output": "Patch plus verification evidence.",
        "verification_required": ["test output", "git diff"],
        "ownership": {
            "mode": "BOUNDED_WRITE",
            "paths": ["execution_contracts.py"],
        },
        "content_authority": "DATA_ONLY",
        "output_trust": "PROPOSAL_UNVERIFIED",
    }


class ExecutionContractTests(unittest.TestCase):
    def test_valid_approved_work_order_is_executable_at_exact_baseline(self):
        order = work_order()
        self.assertIs(validate_work_order(order), order)
        self.assertTrue(assert_executable_work_order(order, BASELINE))

    def test_missing_and_unknown_work_order_fields_fail_closed(self):
        missing = work_order()
        missing.pop("known_unknowns")
        with self.assertRaisesRegex(ContractError, "missing required"):
            validate_work_order(missing)
        extra = work_order()
        extra["helpful_guess"] = True
        with self.assertRaisesRegex(ContractError, "unknown field"):
            validate_work_order(extra)

    def test_invalid_baseline_sha_is_rejected(self):
        order = work_order()
        order["baseline"]["commit_sha"] = "main"
        with self.assertRaisesRegex(ContractError, "40-character"):
            validate_work_order(order)

    def test_stale_baseline_fails_closed(self):
        with self.assertRaises(StaleWorkOrderError):
            assert_work_order_fresh(work_order(), OTHER)

    def test_nonapproved_work_order_cannot_execute_even_when_fresh(self):
        with self.assertRaisesRegex(ContractError, "not executable"):
            assert_executable_work_order(work_order("DRAFT"), BASELINE)

    def test_friend_packet_binds_to_exact_work_order_and_baseline(self):
        packet = friend_packet()
        self.assertIs(validate_friend_packet(packet, work_order()), packet)
        packet["baseline_commit_sha"] = OTHER
        with self.assertRaisesRegex(ContractError, "baseline differs"):
            validate_friend_packet(packet, work_order())

    def test_friend_packet_cannot_rebind_to_another_work_order(self):
        packet = friend_packet()
        packet["work_order_id"] = "WO-OTHER"
        with self.assertRaisesRegex(ContractError, "different Work Order"):
            validate_friend_packet(packet, work_order())

    def test_friend_packet_content_is_data_and_output_is_unverified(self):
        packet = friend_packet()
        packet["content_authority"] = "SYSTEM"
        with self.assertRaisesRegex(ContractError, "DATA_ONLY"):
            validate_friend_packet(packet)
        packet = friend_packet()
        packet["output_trust"] = "VERIFIED"
        with self.assertRaisesRegex(ContractError, "PROPOSAL_UNVERIFIED"):
            validate_friend_packet(packet)

    def test_bounded_write_requires_explicit_owned_paths(self):
        packet = friend_packet()
        packet["ownership"]["paths"] = []
        with self.assertRaisesRegex(ContractError, "requires at least one path"):
            validate_friend_packet(packet)

    def test_unknown_do_not_assume_field_is_mandatory(self):
        packet = friend_packet()
        packet.pop("unknown_do_not_assume")
        with self.assertRaisesRegex(ContractError, "missing required"):
            validate_friend_packet(packet)

    def test_json_schemas_and_runtime_validator_require_same_top_level_fields(self):
        root = Path(__file__).resolve().parents[1]
        work_schema = json.loads((root / "schemas" / "execution-work-order-v1.schema.json").read_text())
        friend_schema = json.loads((root / "schemas" / "friend-packet-v1.schema.json").read_text())
        self.assertEqual(set(work_schema["required"]), set(WORK_ORDER_REQUIRED))
        self.assertEqual(set(friend_schema["required"]), set(FRIEND_PACKET_REQUIRED))
        self.assertFalse(work_schema["additionalProperties"])
        self.assertFalse(friend_schema["additionalProperties"])

    def test_observed_git_commit_uses_argument_vector_not_shell(self):
        completed = subprocess.CompletedProcess(
            ["git"], 0, stdout=BASELINE + "\n", stderr="")
        with patch("execution_contracts.subprocess.run", return_value=completed) as run:
            self.assertEqual(observed_git_commit("."), BASELINE)
        args, kwargs = run.call_args
        self.assertEqual(args[0][0], "git")
        self.assertIn("rev-parse", args[0])
        self.assertNotIn("shell", kwargs)

    def test_observed_git_commit_rejects_untrusted_output(self):
        completed = subprocess.CompletedProcess(
            ["git"], 0, stdout="not-a-sha\n", stderr="")
        with patch("execution_contracts.subprocess.run", return_value=completed):
            with self.assertRaises(ContractError):
                observed_git_commit(".")


if __name__ == "__main__":
    unittest.main()
