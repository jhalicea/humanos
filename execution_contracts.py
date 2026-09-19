"""Deterministic execution contracts for the HumanOS Work Loop.

This module does not dispatch models or execute work. It defines the bounded
contracts that future dispatchers must validate before execution and provides a
fail-closed baseline freshness check.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path


SHA40 = re.compile(r"^[0-9a-f]{40}$")
WORK_ORDER_KIND = "EXECUTION_WORK_ORDER"
FRIEND_PACKET_KIND = "FRIEND_PACKET"
SCHEMA_VERSION = 1

PRIVACY_CLASSES = (
    "PUBLIC",
    "INTERNAL",
    "CONFIDENTIAL",
    "RESTRICTED",
    "LOCAL_ONLY",
)
WORK_ORDER_STATUSES = ("DRAFT", "APPROVED", "STALE", "COMPLETE")
OWNERSHIP_MODES = ("READ_ONLY", "BOUNDED_WRITE")

WORK_ORDER_REQUIRED = frozenset({
    "schema_version",
    "kind",
    "work_order_id",
    "status",
    "objective",
    "scope",
    "out_of_scope",
    "baseline",
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
FRIEND_PACKET_REQUIRED = frozenset({
    "schema_version",
    "kind",
    "packet_id",
    "work_order_id",
    "baseline_commit_sha",
    "worker_role",
    "privacy_classification",
    "task",
    "known_evidence",
    "constraints",
    "unknown_do_not_assume",
    "allowed_scope",
    "prohibited_actions",
    "acceptance_criteria",
    "expected_output",
    "verification_required",
    "ownership",
    "content_authority",
    "output_trust",
})


class ContractError(ValueError):
    """Raised when an execution contract is malformed or internally inconsistent."""


class StaleWorkOrderError(ContractError):
    """Raised when an approved Work Order no longer matches observed repository state."""


def _strict_keys(value, required, label):
    if not isinstance(value, dict):
        raise ContractError(f"{label} must be an object")
    keys = set(value)
    missing = sorted(required - keys)
    unknown = sorted(keys - required)
    if missing:
        raise ContractError(f"{label} missing required field(s): {', '.join(missing)}")
    if unknown:
        raise ContractError(f"{label} contains unknown field(s): {', '.join(unknown)}")


def _string(value, label, *, allow_empty=False):
    if not isinstance(value, str):
        raise ContractError(f"{label} must be a string")
    if not allow_empty and not value.strip():
        raise ContractError(f"{label} must not be empty")
    return value


def _string_list(value, label, *, nonempty=False):
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ContractError(f"{label} must be a list of strings")
    if nonempty and not value:
        raise ContractError(f"{label} must not be empty")
    if any(not item.strip() for item in value):
        raise ContractError(f"{label} must not contain empty strings")
    return value


def _sha(value, label):
    _string(value, label)
    normalized = value.lower()
    if not SHA40.fullmatch(normalized):
        raise ContractError(f"{label} must be a 40-character lowercase/uppercase hexadecimal commit SHA")
    return normalized


def _provenance(value):
    if not isinstance(value, list):
        raise ContractError("provenance_references must be a list")
    allowed = {"decision", "file", "commit", "test", "artifact", "source"}
    for index, item in enumerate(value):
        if not isinstance(item, dict) or set(item) != {"type", "reference"}:
            raise ContractError(
                f"provenance_references[{index}] must contain exactly type and reference")
        if item["type"] not in allowed:
            raise ContractError(f"provenance_references[{index}].type is unsupported")
        _string(item["reference"], f"provenance_references[{index}].reference")
    return value


def validate_work_order(work_order):
    """Validate and return a Work Order without mutating it."""
    _strict_keys(work_order, WORK_ORDER_REQUIRED, "work_order")
    if work_order["schema_version"] != SCHEMA_VERSION:
        raise ContractError(f"unsupported work_order schema_version: {work_order['schema_version']!r}")
    if work_order["kind"] != WORK_ORDER_KIND:
        raise ContractError(f"work_order.kind must be {WORK_ORDER_KIND}")
    _string(work_order["work_order_id"], "work_order_id")
    if work_order["status"] not in WORK_ORDER_STATUSES:
        raise ContractError("work_order.status is unsupported")
    _string(work_order["objective"], "objective")
    _string_list(work_order["scope"], "scope", nonempty=True)
    _string_list(work_order["out_of_scope"], "out_of_scope")
    _string_list(work_order["relevant_files"], "relevant_files")
    _string_list(work_order["constraints"], "constraints")
    _string_list(work_order["acceptance_tests"], "acceptance_tests", nonempty=True)
    _string_list(work_order["security_requirements"], "security_requirements")
    _string(work_order["rollback"], "rollback")
    _string_list(work_order["assigned_workers"], "assigned_workers")
    _string_list(work_order["known_unknowns"], "known_unknowns")
    _provenance(work_order["provenance_references"])
    _string(work_order["done_condition"], "done_condition")
    if work_order["privacy_classification"] not in PRIVACY_CLASSES:
        raise ContractError("privacy_classification is unsupported")

    baseline = work_order["baseline"]
    if not isinstance(baseline, dict) or set(baseline) != {"repository", "ref", "commit_sha"}:
        raise ContractError("baseline must contain exactly repository, ref, and commit_sha")
    _string(baseline["repository"], "baseline.repository")
    _string(baseline["ref"], "baseline.ref")
    _sha(baseline["commit_sha"], "baseline.commit_sha")

    approval = work_order["approval"]
    if not isinstance(approval, dict) or set(approval) != {"approved_by", "approved_at"}:
        raise ContractError("approval must contain exactly approved_by and approved_at")
    _string(approval["approved_by"], "approval.approved_by", allow_empty=work_order["status"] == "DRAFT")
    _string(approval["approved_at"], "approval.approved_at", allow_empty=work_order["status"] == "DRAFT")
    if work_order["status"] == "APPROVED":
        _string(approval["approved_by"], "approval.approved_by")
        _string(approval["approved_at"], "approval.approved_at")
    return work_order


def validate_friend_packet(packet, work_order=None):
    """Validate a bounded worker packet.

    When a Work Order is supplied, the packet must bind to the exact Work Order,
    approved baseline, and privacy class. This prevents packet drift from silently
    widening or rebasing approved work.
    """
    _strict_keys(packet, FRIEND_PACKET_REQUIRED, "friend_packet")
    if packet["schema_version"] != SCHEMA_VERSION:
        raise ContractError(f"unsupported friend_packet schema_version: {packet['schema_version']!r}")
    if packet["kind"] != FRIEND_PACKET_KIND:
        raise ContractError(f"friend_packet.kind must be {FRIEND_PACKET_KIND}")
    _string(packet["packet_id"], "packet_id")
    _string(packet["work_order_id"], "work_order_id")
    _sha(packet["baseline_commit_sha"], "baseline_commit_sha")
    _string(packet["worker_role"], "worker_role")
    if packet["privacy_classification"] not in PRIVACY_CLASSES:
        raise ContractError("privacy_classification is unsupported")
    _string(packet["task"], "task")
    _string_list(packet["known_evidence"], "known_evidence")
    _string_list(packet["constraints"], "constraints")
    _string_list(packet["unknown_do_not_assume"], "unknown_do_not_assume")
    _string_list(packet["allowed_scope"], "allowed_scope", nonempty=True)
    _string_list(packet["prohibited_actions"], "prohibited_actions")
    _string_list(packet["acceptance_criteria"], "acceptance_criteria", nonempty=True)
    _string(packet["expected_output"], "expected_output")
    _string_list(packet["verification_required"], "verification_required", nonempty=True)

    ownership = packet["ownership"]
    if not isinstance(ownership, dict) or set(ownership) != {"mode", "paths"}:
        raise ContractError("ownership must contain exactly mode and paths")
    if ownership["mode"] not in OWNERSHIP_MODES:
        raise ContractError("ownership.mode is unsupported")
    _string_list(ownership["paths"], "ownership.paths")
    if ownership["mode"] == "BOUNDED_WRITE" and not ownership["paths"]:
        raise ContractError("BOUNDED_WRITE ownership requires at least one path")

    if packet["content_authority"] != "DATA_ONLY":
        raise ContractError("content_authority must be DATA_ONLY")
    if packet["output_trust"] != "PROPOSAL_UNVERIFIED":
        raise ContractError("output_trust must be PROPOSAL_UNVERIFIED")

    if work_order is not None:
        validate_work_order(work_order)
        if packet["work_order_id"] != work_order["work_order_id"]:
            raise ContractError("FRIEND packet is bound to a different Work Order")
        if packet["baseline_commit_sha"].lower() != work_order["baseline"]["commit_sha"].lower():
            raise ContractError("FRIEND packet baseline differs from the Work Order baseline")
        if packet["privacy_classification"] != work_order["privacy_classification"]:
            raise ContractError("FRIEND packet privacy class differs from the Work Order")
    return packet


def observed_git_commit(repo_root):
    """Read the exact repository HEAD without invoking a shell."""
    root = Path(repo_root).resolve()
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ContractError(f"cannot observe repository baseline: {error}") from error
    return _sha(result.stdout.strip(), "observed repository commit")


def assert_work_order_fresh(work_order, observed_commit_sha):
    """Fail closed if repository state no longer matches the approved baseline."""
    validate_work_order(work_order)
    approved = work_order["baseline"]["commit_sha"].lower()
    observed = _sha(observed_commit_sha, "observed_commit_sha")
    if approved != observed:
        raise StaleWorkOrderError(
            f"Work Order {work_order['work_order_id']} is STALE: "
            f"approved baseline {approved} != observed {observed}")
    return True


def assert_executable_work_order(work_order, observed_commit_sha):
    """Require an approved, structurally valid, fresh Work Order before execution."""
    validate_work_order(work_order)
    if work_order["status"] != "APPROVED":
        raise ContractError(
            f"Work Order {work_order['work_order_id']} is not executable: "
            f"status={work_order['status']}")
    return assert_work_order_fresh(work_order, observed_commit_sha)


def assert_repository_fresh(work_order, repo_root):
    """Convenience enforcement primitive for a future dispatcher."""
    return assert_executable_work_order(work_order, observed_git_commit(repo_root))
