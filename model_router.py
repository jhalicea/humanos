"""Deterministic HumanOS model router.

This module does not execute models or grant authority. It only emits a routing
recommendation that can be audited before any model/tool execution occurs.
"""
from dataclasses import dataclass
from typing import Optional

VALID_ROUTES = {"BUILD", "ENGINEER", "DECIDE", "ESCALATE"}
VALID_LANES = {"GREEN", "AMBER", "RED"}
VALID_MODELS = {"luna", "terra", "sol", "astra"}


@dataclass(frozen=True)
class TaskProfile:
    task_id: str
    well_defined: bool
    operational_state_dominant: bool = False
    security_privacy_authority: bool = False
    canonical_state: bool = False
    money_or_external_action: bool = False
    irreversible: bool = False
    high_consequence: bool = False
    broad_parallel_work: bool = False
    cross_system: bool = False
    expensive_to_miss_failures: bool = False
    important_artifact: bool = False
    owner_override: Optional[str] = None


def _risk_lane(task: TaskProfile) -> str:
    if (
        task.security_privacy_authority
        or task.irreversible
        or task.high_consequence
        or task.expensive_to_miss_failures
        or (task.canonical_state and task.cross_system)
    ):
        return "RED"
    if (
        task.canonical_state
        or task.money_or_external_action
        or task.cross_system
        or task.important_artifact
        or not task.well_defined
    ):
        return "AMBER"
    return "GREEN"


def _automatic_route(task: TaskProfile, risk_lane: str) -> tuple[str, str, Optional[str], Optional[str], str]:
    """Return route, primary, worker, reviewer, behavior overlay."""
    if risk_lane == "RED":
        if task.broad_parallel_work or task.expensive_to_miss_failures or task.cross_system:
            return "ESCALATE", "astra", None, "sol", "SENIOR_CHALLENGER"
        return "DECIDE", "sol", None, "astra", "COLLABORATIVE_REFRAMER"

    if task.well_defined:
        if task.operational_state_dominant:
            reviewer = "sol" if risk_lane == "AMBER" else None
            return "ENGINEER", "terra", None, reviewer, "METHODICAL_ENGINEER"
        reviewer = "sol" if risk_lane == "AMBER" else None
        return "BUILD", "luna", None, reviewer, "LEAN_EXECUTOR"

    # Judgment is still needed: default to Sol, not Astra.
    return "DECIDE", "sol", None, None, "COLLABORATIVE_REFRAMER"


def route_task(task: TaskProfile) -> dict:
    """Create an auditable routing recommendation with no execution authority."""
    lane = _risk_lane(task)
    route, primary, worker, reviewer, overlay = _automatic_route(task, lane)
    route_source = "automatic"
    reason_codes = []

    if not task.well_defined:
        reason_codes.append("JUDGMENT_REQUIRED")
    if task.operational_state_dominant:
        reason_codes.append("METHODICAL_STATE_WORK")
    if lane == "RED":
        reason_codes.append("HIGH_RISK")
    elif lane == "AMBER":
        reason_codes.append("MODERATE_RISK")
    if task.broad_parallel_work:
        reason_codes.append("PARALLEL_BREADTH")
    if task.cross_system:
        reason_codes.append("CROSS_SYSTEM")
    if task.important_artifact:
        reason_codes.append("IMPORTANT_ARTIFACT")

    if task.owner_override is not None:
        override = task.owner_override.strip().lower()
        if override not in VALID_MODELS:
            raise ValueError("owner_override must be one of: luna, terra, sol, astra")
        primary = override
        route_source = "owner_override"
        reason_codes.append("OWNER_OVERRIDE")
        # Override changes the selected model, not the risk lane. Preserve RED review.
        if lane == "RED" and primary != "astra" and reviewer is None:
            reviewer = "astra"

    return {
        "task_id": task.task_id,
        "task_class": route,
        "risk_lane": lane,
        "primary_model": primary,
        "worker_model": worker,
        "reviewer_model": reviewer,
        "behavior_overlay": overlay,
        "route_source": route_source,
        "reason_codes": reason_codes,
        "authority_granted": False,
    }
