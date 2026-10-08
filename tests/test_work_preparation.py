import copy
import json
import unittest
from pathlib import Path

from friend_packet_compiler import (
    ASSIGNMENT_REQUIRED,
    FriendCompilerError,
    compile_friend_packet,
)
from friend_privacy import ExternalDisclosureBlocked
from work_preparation import prepare_work


BASELINE = "563cd3abd3a9af6c2ebd85b4c790a41d4a6880aa"


def decision(privacy="INTERNAL"):
    return {
        "schema_version": 1,
        "kind": "APPROVED_ARCHITECTURE_DECISION",
        "decision_id": "AD-FLOW-TEST",
        "work_order_id": "WO-FLOW-TEST",
        "status": "APPROVED",
        "objective": "Polish the HumanOS work preparation experience.",
        "scope": ["prepare bounded work"],
        "out_of_scope": ["automatic dispatch"],
        "relevant_files": ["src/a.py", "tests/test_a.py"],
        "constraints": ["Do not widen scope."],
        "acceptance_tests": ["all focused tests pass", "full suite remains green"],
        "security_requirements": ["preserve owner authority"],
        "rollback": "Revert the candidate.",
        "assigned_workers": [],
        "known_unknowns": ["UNKNOWN: future dispatch integration"],
        "provenance_references": [{"type": "commit", "reference": BASELINE}],
        "done_condition": "Prepared work is concise and validator-clean.",
        "approval": {
            "approved_by": "Jon",
            "approved_at": "2026-09-19T18:00:00-04:00",
        },
        "privacy_classification": privacy,
    }


def assignment():
    return {
        "schema_version": 1,
        "kind": "FRIEND_ASSIGNMENT",
        "packet_id": "FP-FLOW-TEST",
        "worker_role": "implementation worker",
        "task": "Implement the bounded preparation change.",
        "known_evidence": ["Current baseline is verified."],
        "allowed_paths": ["src/a.py", "tests/test_a.py"],
        "expected_output": "Patch plus verification evidence.",
        "verification_required": ["test output", "git diff"],
        "ownership_mode": "BOUNDED_WRITE",
    }


class EffortlessWorkPreparationTests(unittest.TestCase):
    def test_friend_compiler_inherits_governance_from_work_order(self):
        prepared = prepare_work(
            decision(),
            assignment(),
            repository="jhalicea/humanos",
            ref="runtime-0.1",
            baseline_commit_sha=BASELINE,
        )
        packet = prepared.friend_packet
        self.assertEqual(packet["work_order_id"], "WO-FLOW-TEST")
        self.assertEqual(packet["baseline_commit_sha"], BASELINE)
        self.assertEqual(packet["privacy_classification"], "INTERNAL")
        self.assertEqual(packet["constraints"], ["Do not widen scope."])
        self.assertEqual(packet["unknown_do_not_assume"], ["UNKNOWN: future dispatch integration"])
        self.assertEqual(packet["acceptance_criteria"], decision()["acceptance_tests"])
        self.assertEqual(packet["content_authority"], "DATA_ONLY")
        self.assertEqual(packet["output_trust"], "PROPOSAL_UNVERIFIED")

    def test_friend_compiler_adds_protected_actions_and_out_of_scope(self):
        prepared = prepare_work(
            decision(),
            assignment(),
            repository="jhalicea/humanos",
            ref="runtime-0.1",
            baseline_commit_sha=BASELINE,
        )
        prohibited = prepared.friend_packet["prohibited_actions"]
        self.assertIn("merge without owner approval", prohibited)
        self.assertIn("deploy without owner approval", prohibited)
        self.assertIn("delete data", prohibited)
        self.assertIn("widen approved scope", prohibited)
        self.assertIn("automatic dispatch", prohibited)

    def test_assignment_cannot_escape_work_order_relevant_files(self):
        bad = assignment()
        bad["allowed_paths"].append("src/not-approved.py")
        with self.assertRaisesRegex(FriendCompilerError, "exceed Work Order"):
            prepare_work(
                decision(),
                bad,
                repository="jhalicea/humanos",
                ref="runtime-0.1",
                baseline_commit_sha=BASELINE,
            )

    def test_work_order_without_relevant_files_cannot_spawn_assignment(self):
        source = decision()
        source["relevant_files"] = []
        with self.assertRaisesRegex(FriendCompilerError, "must name relevant_files"):
            prepare_work(
                source,
                assignment(),
                repository="jhalicea/humanos",
                ref="runtime-0.1",
                baseline_commit_sha=BASELINE,
            )

    def test_inputs_are_not_mutated(self):
        source = decision()
        job = assignment()
        source_before = copy.deepcopy(source)
        job_before = copy.deepcopy(job)
        prepare_work(
            source,
            job,
            repository="jhalicea/humanos",
            ref="runtime-0.1",
            baseline_commit_sha=BASELINE,
        )
        self.assertEqual(source, source_before)
        self.assertEqual(job, job_before)

    def test_default_review_card_uses_progressive_disclosure(self):
        prepared = prepare_work(
            decision(),
            assignment(),
            repository="jhalicea/humanos",
            ref="runtime-0.1",
            baseline_commit_sha=BASELINE,
        )
        card = prepared.review_card()
        self.assertTrue(card.startswith("Ready\n"))
        self.assertIn("Scope: 2 items · Bounded Write", card)
        self.assertIn("Privacy: Internal · On this Mac", card)
        self.assertIn("Nothing has run yet.", card)
        for hidden in (
            BASELINE,
            "schema_version",
            "FRIEND_PACKET",
            "work_order_id",
            "packet_id",
            "sha256:",
        ):
            self.assertNotIn(hidden, card)
        self.assertLessEqual(len(card.splitlines()), 8)

    def test_details_keep_full_audit_artifacts(self):
        prepared = prepare_work(
            decision(),
            assignment(),
            repository="jhalicea/humanos",
            ref="runtime-0.1",
            baseline_commit_sha=BASELINE,
        )
        details = prepared.details()
        self.assertEqual(details["status"], "READY")
        self.assertEqual(details["work_order"]["baseline"]["commit_sha"], BASELINE)
        self.assertEqual(details["friend_packet"]["packet_id"], "FP-FLOW-TEST")
        self.assertEqual(details["prepared_packet"], details["friend_packet"])

    def test_external_preparation_redacts_without_leaking_value_in_card(self):
        job = assignment()
        job["known_evidence"] = ["contact jon@example.com"]
        prepared = prepare_work(
            decision(),
            job,
            repository="jhalicea/humanos",
            ref="runtime-0.1",
            baseline_commit_sha=BASELINE,
            destination="EXTERNAL",
        )
        self.assertNotIn("jon@example.com", json.dumps(prepared.prepared_packet))
        card = prepared.review_card()
        self.assertIn("External, privacy-filtered", card)
        self.assertIn("1 sensitive value removed", card)
        self.assertNotIn("jon@example.com", card)

    def test_sensitive_class_external_preparation_fails_closed(self):
        with self.assertRaises(ExternalDisclosureBlocked):
            prepare_work(
                decision("CONFIDENTIAL"),
                assignment(),
                repository="jhalicea/humanos",
                ref="runtime-0.1",
                baseline_commit_sha=BASELINE,
                destination="EXTERNAL",
            )

    def test_assignment_schema_and_runtime_validator_require_same_fields(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads(
            (root / "schemas" / "friend-assignment-v1.schema.json").read_text()
        )
        self.assertEqual(set(schema["required"]), set(ASSIGNMENT_REQUIRED))
        self.assertFalse(schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
