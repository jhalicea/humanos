"""Local dry-run entry point for the HumanOS model router.

This command classifies a task, emits a Mirror routing recommendation, optionally
persists it to the append-only routing ledger, verifies the ledger, and exits.
It never dispatches a model or grants execution authority.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from mirror_router_adapter import RoutingEventLedger, route_for_mirror
from model_router import TaskProfile

DEFAULT_LEDGER = Path("var/model-routing/routing-events.jsonl")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="HumanOS model-router dry run")
    parser.add_argument("--task-id", default="DRY-RUN-001")
    parser.add_argument("--well-defined", action="store_true")
    parser.add_argument("--operational-state", action="store_true")
    parser.add_argument("--security", action="store_true")
    parser.add_argument("--canonical-state", action="store_true")
    parser.add_argument("--external-action", action="store_true")
    parser.add_argument("--irreversible", action="store_true")
    parser.add_argument("--high-consequence", action="store_true")
    parser.add_argument("--broad-parallel", action="store_true")
    parser.add_argument("--cross-system", action="store_true")
    parser.add_argument("--expensive-to-miss", action="store_true")
    parser.add_argument("--important-artifact", action="store_true")
    parser.add_argument("--owner-override", choices=("luna", "terra", "sol", "astra"))
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--no-persist", action="store_true")
    return parser


def task_from_args(args: argparse.Namespace) -> TaskProfile:
    return TaskProfile(
        task_id=args.task_id,
        well_defined=args.well_defined,
        operational_state_dominant=args.operational_state,
        security_privacy_authority=args.security,
        canonical_state=args.canonical_state,
        money_or_external_action=args.external_action,
        irreversible=args.irreversible,
        high_consequence=args.high_consequence,
        broad_parallel_work=args.broad_parallel,
        cross_system=args.cross_system,
        expensive_to_miss_failures=args.expensive_to_miss,
        important_artifact=args.important_artifact,
        owner_override=args.owner_override,
    )


def run_dry_run(args: argparse.Namespace) -> dict:
    task = task_from_args(args)
    ledger = None if args.no_persist else RoutingEventLedger(args.ledger)
    result = route_for_mirror(task, ledger=ledger)

    ledger_verified = None
    if ledger is not None:
        ledger_verified = ledger.verify()

    return {
        "routing_event": result["routing_event"],
        "ledger_recorded": result["ledger_record"] is not None,
        "ledger_path": str(args.ledger) if ledger is not None else None,
        "ledger_verified": ledger_verified,
        "model_dispatched": result["model_dispatched"],
        "authority_granted": result["authority_granted"],
    }


def main() -> int:
    args = build_parser().parse_args()
    output = run_dry_run(args)
    print(json.dumps(output, indent=2, sort_keys=True))

    if output["model_dispatched"] or output["authority_granted"]:
        return 2
    if output["ledger_recorded"] and not output["ledger_verified"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
