import copy
import json
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from execution_contracts import validate_work_order
from work_order_compiler import (
    CompilerError,
    DECISION_REQUIRED,
    compile_repository_work_order,
    compile_work_order,
    decision_fingerprint,
    validate_approved_decision,
)


BASELINE = "2c45256128aed441724660243019643d02e59ec8"


def decision():
    return {
        "schema_version": 1,
        "kind": "APPROVED_ARCHITECTURE_DECISION",
        "decision_id": "AD-TEST-001",
        "work_order_id": "WO-TEST-001",
        "status": "APPROVED",
        "objective": "Implement one bounded compiler slice.",
        "scope": ["compile approved decisions"],
        "out_of_scope": ["dispatch"],
        "relevant_files": ["work_order_compiler.py"],
        "constraints": ["No semantic inference."],
        "acceptance_tests": ["compiled Work Order validates"],
        "security_requirements": ["missing data fails closed"],
        "rollback": "Revert the candidate branch.",
        "assigned_workers": [],
        "known_unknowns": ["UNKNOWN: future dispatcher integration"],
        "provenance_references": [
            {"type": "commit", "reference": BASELINE},
        ],
        "done_condition": "Compiler and regressions pass.",
        "approval": {
            "approved_by": "Jon",
            "approved_at": "2026-09-19T17:44:00-04:00",
        },
        "privacy_classification": "INTERNAL",
    }


class WorkOrderCompilerTests(unittest.TestCase):
    def test_valid_decision_compiles_to_promoted_contract(self):
        source = decision()
        result = compile_work_order(
            source,
            repository="jhalicea/humanos",
            ref="runtime-0.1",
            baseline_commit_sha=BASELINE,
        )
        self.assertEqual(result["status"], "APPROVED")
        self.assertEqual(result["work_order_id"], source["work_order_id"])
        self.assertEqual(result["baseline"]["commit_sha"], BASELINE)
        self.assertEqual(result["approval"], source["approval"])
        self.assertEqual(result["privacy_classification"], "INTERNAL")
        self.assertIs(validate_work_order(result), result)

    def test_compiler_does_not_mutate_source(self):
        source = decision()
        before = copy.deepcopy(source)
        compile_work_order(
            source,
            repository="jhalicea/humanos",
            ref="runtime-0.1",
            baseline_commit_sha=BASELINE,
        )
        self.assertEqual(source, before)

    def test_missing_and_unknown_decision_fields_fail_closed(self):
        missing = decision()
        missing.pop("known_unknowns")
        with self.assertRaisesRegex(CompilerError, "missing required"):
            validate_approved_decision(missing)

        extra = decision()
        extra["assistant_guess"] = "probably fine"
        with self.assertRaisesRegex(CompilerError, "unknown field"):
            validate_approved_decision(extra)

    def test_unapproved_decision_cannot_compile(self):
        source = decision()
        source["status"] = "DRAFT"
        with self.assertRaisesRegex(CompilerError, "must be APPROVED"):
            compile_work_order(
                source,
                repository="jhalicea/humanos",
                ref="runtime-0.1",
                baseline_commit_sha=BASELINE,
            )

    def test_invalid_baseline_fails_closed(self):
        with self.assertRaisesRegex(CompilerError, "40-character"):
            compile_work_order(
                decision(),
                repository="jhalicea/humanos",
                ref="runtime-0.1",
                baseline_commit_sha="runtime-0.1",
            )

    def test_fingerprint_is_deterministic_across_dictionary_key_order(self):
        source = decision()
        reversed_source = dict(reversed(list(source.items())))
        self.assertEqual(decision_fingerprint(source), decision_fingerprint(reversed_source))

    def test_compiler_adds_exact_decision_fingerprint_provenance(self):
        source = decision()
        expected = f"{source['decision_id']}#sha256:{decision_fingerprint(source)}"
        result = compile_work_order(
            source,
            repository="jhalicea/humanos",
            ref="runtime-0.1",
            baseline_commit_sha=BASELINE,
        )
        self.assertIn(
            {"type": "decision", "reference": expected},
            result["provenance_references"],
        )

    def test_conflicting_existing_decision_fingerprint_fails_closed(self):
        source = decision()
        source["provenance_references"].append({
            "type": "decision",
            "reference": f"{source['decision_id']}#sha256:" + ("0" * 64),
        })
        with self.assertRaisesRegex(CompilerError, "fingerprint conflicts"):
            compile_work_order(
                source,
                repository="jhalicea/humanos",
                ref="runtime-0.1",
                baseline_commit_sha=BASELINE,
            )

    def test_matching_existing_decision_fingerprint_is_not_duplicated(self):
        source = decision()
        reference = f"{source['decision_id']}#sha256:{decision_fingerprint(source)}"
        source["provenance_references"].append({
            "type": "decision",
            "reference": reference,
        })
        result = compile_work_order(
            source,
            repository="jhalicea/humanos",
            ref="runtime-0.1",
            baseline_commit_sha=BASELINE,
        )
        self.assertEqual(
            sum(1 for item in result["provenance_references"]
                if item == {"type": "decision", "reference": reference}),
            1,
        )

    def test_repository_compiler_pins_observed_head(self):
        completed = subprocess.CompletedProcess(
            ["git"], 0, stdout=BASELINE + "\n", stderr="")
        with patch("execution_contracts.subprocess.run", return_value=completed):
            result = compile_repository_work_order(
                decision(),
                repository="jhalicea/humanos",
                ref="runtime-0.1",
                repo_root=".",
            )
        self.assertEqual(result["baseline"]["commit_sha"], BASELINE)

    def test_json_schema_and_runtime_validator_require_same_fields(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads(
            (root / "schemas" / "approved-architecture-decision-v1.schema.json").read_text()
        )
        self.assertEqual(set(schema["required"]), set(DECISION_REQUIRED))
        self.assertFalse(schema["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
