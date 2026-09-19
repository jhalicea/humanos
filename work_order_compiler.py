"""Deterministic compiler from approved architecture decisions to Work Orders.

The compiler performs no semantic inference and grants no execution authority.
Every required execution field must already exist in the approved decision record.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re

from execution_contracts import (
    ContractError,
    PRIVACY_CLASSES,
    observed_git_commit,
    validate_work_order,
)


DECISION_KIND = "APPROVED_ARCHITECTURE_DECISION"
DECISION_SCHEMA_VERSION = 1
SHA40 = re.compile(r"^[0-9A-Fa-f]{40}$")

DECISION_REQUIRED = frozenset({
    "schema_version",
    "kind",
    "decision_id",
    "work_order_id",
    "status",
    "objective",
    "scope",
    "out_of_scope",
    "relevant_files",
    "constraints",
    "acceptance_tests",
    "security_requirements",
    "rollback",
    "assigned_workers",
    "known_unknowns",
    "provenance_references",
    "done_condition",
    "approval",
    "privacy_classification",
})


class CompilerError(ContractError):
    """Raised when an approved decision cannot be compiled deterministically."""


def _strict_keys(value, required, label):
    if not isinstance(value, dict):
        raise CompilerError(f"{label} must be an object")
    missing = sorted(required - set(value))
    unknown = sorted(set(value) - required)
    if missing:
        raise CompilerError(f"{label} missing required field(s): {', '.join(missing)}")
    if unknown:
        raise CompilerError(f"{label} contains unknown field(s): {', '.join(unknown)}")


def _string(value, label):
    if not isinstance(value, str) or not value.strip():
        raise CompilerError(f"{label} must be a non-empty string")
    return value


def _string_list(value, label, *, nonempty=False):
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise CompilerError(f"{label} must be a list of strings")
    if nonempty and not value:
        raise CompilerError(f"{label} must not be empty")
    if any(not item.strip() for item in value):
        raise CompilerError(f"{label} must not contain empty strings")
    return value


def _provenance(value):
    if not isinstance(value, list):
        raise CompilerError("provenance_references must be a list")
    allowed = {"decision", "file", "commit", "test", "artifact", "source"}
    for index, item in enumerate(value):
        if not isinstance(item, dict) or set(item) != {"type", "reference"}:
            raise CompilerError(
                f"provenance_references[{index}] must contain exactly type and reference")
        if item["type"] not in allowed:
            raise CompilerError(f"provenance_references[{index}].type is unsupported")
        _string(item["reference"], f"provenance_references[{index}].reference")
    return value


def validate_approved_decision(decision):
    """Validate the compiler input without altering it."""
    _strict_keys(decision, DECISION_REQUIRED, "decision")
    if decision["schema_version"] != DECISION_SCHEMA_VERSION:
        raise CompilerError(
            f"unsupported decision schema_version: {decision['schema_version']!r}")
    if decision["kind"] != DECISION_KIND:
        raise CompilerError(f"decision.kind must be {DECISION_KIND}")
    if decision["status"] != "APPROVED":
        raise CompilerError("decision.status must be APPROVED before compilation")

    _string(decision["decision_id"], "decision_id")
    _string(decision["work_order_id"], "work_order_id")
    _string(decision["objective"], "objective")
    _string_list(decision["scope"], "scope", nonempty=True)
    _string_list(decision["out_of_scope"], "out_of_scope")
    _string_list(decision["relevant_files"], "relevant_files")
    _string_list(decision["constraints"], "constraints")
    _string_list(decision["acceptance_tests"], "acceptance_tests", nonempty=True)
    _string_list(decision["security_requirements"], "security_requirements")
    _string(decision["rollback"], "rollback")
    _string_list(decision["assigned_workers"], "assigned_workers")
    _string_list(decision["known_unknowns"], "known_unknowns")
    _provenance(decision["provenance_references"])
    _string(decision["done_condition"], "done_condition")

    if decision["privacy_classification"] not in PRIVACY_CLASSES:
        raise CompilerError("privacy_classification is unsupported")

    approval = decision["approval"]
    if not isinstance(approval, dict) or set(approval) != {"approved_by", "approved_at"}:
        raise CompilerError("approval must contain exactly approved_by and approved_at")
    _string(approval["approved_by"], "approval.approved_by")
    _string(approval["approved_at"], "approval.approved_at")
    return decision


def _fingerprint_material(decision):
    """Return canonical decision content without its self-referential fingerprint."""
    material = copy.deepcopy(decision)
    prefix = f"{decision['decision_id']}#sha256:"
    material["provenance_references"] = [
        item
        for item in material["provenance_references"]
        if not (item["type"] == "decision" and item["reference"].startswith(prefix))
    ]
    return material


def decision_fingerprint(decision):
    """Return stable SHA-256 over canonical approved decision content.

    The compiler-generated fingerprint reference for this same decision ID is
    excluded from hash material; including it would create a circular hash.
    Other provenance remains part of the fingerprint.
    """
    validate_approved_decision(decision)
    canonical = json.dumps(
        _fingerprint_material(decision),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _normalized_sha(value):
    if not isinstance(value, str) or not SHA40.fullmatch(value):
        raise CompilerError("baseline_commit_sha must be a 40-character hexadecimal commit SHA")
    return value.lower()


def _decision_provenance(decision):
    fingerprint = decision_fingerprint(decision)
    prefix = f"{decision['decision_id']}#sha256:"
    expected = prefix + fingerprint

    provenance = copy.deepcopy(decision["provenance_references"])
    for item in provenance:
        if item["type"] == "decision" and item["reference"].startswith(prefix):
            if item["reference"] != expected:
                raise CompilerError(
                    "decision provenance fingerprint conflicts with the approved decision record")
            return provenance
    provenance.append({"type": "decision", "reference": expected})
    return provenance


def compile_work_order(
    decision,
    *,
    repository,
    ref,
    baseline_commit_sha,
):
    """Compile an approved decision into the promoted Execution Work Order v1 contract."""
    validate_approved_decision(decision)
    _string(repository, "repository")
    _string(ref, "ref")
    baseline = _normalized_sha(baseline_commit_sha)

    work_order = {
        "schema_version": 1,
        "kind": "EXECUTION_WORK_ORDER",
        "work_order_id": decision["work_order_id"],
        "status": "APPROVED",
        "objective": decision["objective"],
        "scope": copy.deepcopy(decision["scope"]),
        "out_of_scope": copy.deepcopy(decision["out_of_scope"]),
        "baseline": {
            "repository": repository,
            "ref": ref,
            "commit_sha": baseline,
        },
        "relevant_files": copy.deepcopy(decision["relevant_files"]),
        "constraints": copy.deepcopy(decision["constraints"]),
        "acceptance_tests": copy.deepcopy(decision["acceptance_tests"]),
        "security_requirements": copy.deepcopy(decision["security_requirements"]),
        "rollback": decision["rollback"],
        "assigned_workers": copy.deepcopy(decision["assigned_workers"]),
        "known_unknowns": copy.deepcopy(decision["known_unknowns"]),
        "provenance_references": _decision_provenance(decision),
        "done_condition": decision["done_condition"],
        "approval": copy.deepcopy(decision["approval"]),
        "privacy_classification": decision["privacy_classification"],
    }
    validate_work_order(work_order)
    return work_order


def compile_repository_work_order(
    decision,
    *,
    repository,
    ref,
    repo_root,
):
    """Compile using the exact currently observed repository HEAD as baseline."""
    return compile_work_order(
        decision,
        repository=repository,
        ref=ref,
        baseline_commit_sha=observed_git_commit(repo_root),
    )
