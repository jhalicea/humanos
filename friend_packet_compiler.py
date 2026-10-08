"""Deterministic compiler from a bounded assignment to a FRIEND packet.

This compiler inherits authority, privacy, baseline, constraints, unknowns, and
acceptance criteria from an already-approved Work Order. It does not dispatch.
"""
from __future__ import annotations

import copy

from execution_contracts import ContractError, validate_friend_packet, validate_work_order


ASSIGNMENT_KIND = "FRIEND_ASSIGNMENT"
ASSIGNMENT_SCHEMA_VERSION = 1
ASSIGNMENT_REQUIRED = frozenset({
    "schema_version",
    "kind",
    "packet_id",
    "worker_role",
    "task",
    "known_evidence",
    "allowed_paths",
    "expected_output",
    "verification_required",
    "ownership_mode",
})

_PROTECTED_ACTIONS = (
    "merge without owner approval",
    "deploy without owner approval",
    "delete data",
    "widen approved scope",
    "change approval or privacy classification",
)


class FriendCompilerError(ContractError):
    """Raised when a bounded assignment cannot compile safely."""


def _string(value, label):
    if not isinstance(value, str) or not value.strip():
        raise FriendCompilerError(f"{label} must be a non-empty string")
    return value


def _string_list(value, label, *, nonempty=False):
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise FriendCompilerError(f"{label} must be a list of strings")
    if nonempty and not value:
        raise FriendCompilerError(f"{label} must not be empty")
    if any(not item.strip() for item in value):
        raise FriendCompilerError(f"{label} must not contain empty strings")
    return value


def validate_friend_assignment(assignment):
    if not isinstance(assignment, dict):
        raise FriendCompilerError("assignment must be an object")
    missing = sorted(ASSIGNMENT_REQUIRED - set(assignment))
    unknown = sorted(set(assignment) - ASSIGNMENT_REQUIRED)
    if missing:
        raise FriendCompilerError(
            "assignment missing required field(s): " + ", ".join(missing))
    if unknown:
        raise FriendCompilerError(
            "assignment contains unknown field(s): " + ", ".join(unknown))
    if assignment["schema_version"] != ASSIGNMENT_SCHEMA_VERSION:
        raise FriendCompilerError(
            f"unsupported assignment schema_version: {assignment['schema_version']!r}")
    if assignment["kind"] != ASSIGNMENT_KIND:
        raise FriendCompilerError(f"assignment.kind must be {ASSIGNMENT_KIND}")

    _string(assignment["packet_id"], "packet_id")
    _string(assignment["worker_role"], "worker_role")
    _string(assignment["task"], "task")
    _string_list(assignment["known_evidence"], "known_evidence")
    _string_list(assignment["allowed_paths"], "allowed_paths", nonempty=True)
    _string(assignment["expected_output"], "expected_output")
    _string_list(
        assignment["verification_required"],
        "verification_required",
        nonempty=True,
    )
    if assignment["ownership_mode"] not in {"READ_ONLY", "BOUNDED_WRITE"}:
        raise FriendCompilerError("ownership_mode is unsupported")
    return assignment


def _bounded_paths(work_order, assignment):
    relevant = set(work_order["relevant_files"])
    requested = set(assignment["allowed_paths"])
    if not relevant:
        raise FriendCompilerError(
            "Work Order must name relevant_files before a FRIEND assignment can compile")
    outside = sorted(requested - relevant)
    if outside:
        raise FriendCompilerError(
            "assignment path(s) exceed Work Order relevant_files: " + ", ".join(outside))
    return copy.deepcopy(assignment["allowed_paths"])


def _prohibited_actions(work_order):
    values = list(_PROTECTED_ACTIONS)
    values.extend(work_order["out_of_scope"])
    return list(dict.fromkeys(values))


def compile_friend_packet(work_order, assignment):
    """Compile one bounded worker packet from an approved Work Order."""
    validate_work_order(work_order)
    validate_friend_assignment(assignment)
    if work_order["status"] != "APPROVED":
        raise FriendCompilerError("Work Order must be APPROVED before FRIEND compilation")

    allowed_paths = _bounded_paths(work_order, assignment)
    packet = {
        "schema_version": 1,
        "kind": "FRIEND_PACKET",
        "packet_id": assignment["packet_id"],
        "work_order_id": work_order["work_order_id"],
        "baseline_commit_sha": work_order["baseline"]["commit_sha"],
        "worker_role": assignment["worker_role"],
        "privacy_classification": work_order["privacy_classification"],
        "task": assignment["task"],
        "known_evidence": copy.deepcopy(assignment["known_evidence"]),
        "constraints": copy.deepcopy(work_order["constraints"]),
        "unknown_do_not_assume": copy.deepcopy(work_order["known_unknowns"]),
        "allowed_scope": allowed_paths,
        "prohibited_actions": _prohibited_actions(work_order),
        "acceptance_criteria": copy.deepcopy(work_order["acceptance_tests"]),
        "expected_output": assignment["expected_output"],
        "verification_required": copy.deepcopy(assignment["verification_required"]),
        "ownership": {
            "mode": assignment["ownership_mode"],
            "paths": copy.deepcopy(allowed_paths),
        },
        "content_authority": "DATA_ONLY",
        "output_trust": "PROPOSAL_UNVERIFIED",
    }
    validate_friend_packet(packet, work_order)
    return packet
