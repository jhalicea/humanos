"""Thin Mirror-facing adapter for the HumanOS model router.

Learning mode only. This module emits and can persist routing recommendations.
It never dispatches a model, grants authority, or promotes experimental workflows
into policy.
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from audit import AuditEvent, canonical_json, hash_event, verify_chain
from model_router import TaskProfile, route_task

ROUTING_EVENT_SCHEMA = "routing-event-v0"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_mirror_routing_event(
    task: TaskProfile,
    *,
    event_id: Optional[str] = None,
    created_at: Optional[str] = None,
) -> dict:
    """Return a Mirror-consumable recommendation with zero execution authority."""
    recommendation = route_task(task)
    return {
        "schema_version": ROUTING_EVENT_SCHEMA,
        "event_id": event_id or f"route-{uuid.uuid4()}",
        "created_at": created_at or _utc_now(),
        "event_type": "MODEL_ROUTING_RECOMMENDATION",
        "status": "PROPOSED",
        "task_id": task.task_id,
        "task_profile": asdict(task),
        "recommendation": recommendation,
        "dispatch_allowed": False,
        "automatic_execution": False,
        "authority_granted": False,
        "policy_promotion": False,
    }


class RoutingEventLedger:
    """Small append-only JSONL ledger with the existing HumanOS audit hash chain."""

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def read_all(self) -> list[AuditEvent]:
        if not self.path.exists():
            return []
        events: list[AuditEvent] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                raw = json.loads(line)
                events.append(AuditEvent(**raw))
        return events

    def append(self, *, action_id: str, body: dict) -> AuditEvent:
        events = self.read_all()
        if events and not verify_chain(events):
            raise ValueError("routing event ledger failed hash-chain verification")

        seq = len(events) + 1
        previous_hash = events[-1].event_hash if events else "GENESIS"
        event_type = "MODEL_ROUTING_RECOMMENDATION"
        event_hash = hash_event(seq, event_type, action_id, body, previous_hash)
        event = AuditEvent(
            seq=seq,
            event_type=event_type,
            action_id=action_id,
            body=body,
            previous_hash=previous_hash,
            event_hash=event_hash,
        )

        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(canonical_json(asdict(event)) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return event

    def verify(self) -> bool:
        return verify_chain(self.read_all())


def route_for_mirror(
    task: TaskProfile,
    *,
    ledger: Optional[RoutingEventLedger] = None,
    event_id: Optional[str] = None,
    created_at: Optional[str] = None,
) -> dict:
    """Emit a recommendation and optionally record it; never execute the route."""
    event = build_mirror_routing_event(
        task,
        event_id=event_id,
        created_at=created_at,
    )
    ledger_record = None
    if ledger is not None:
        ledger_record = ledger.append(action_id=event["event_id"], body=event)

    return {
        "routing_event": event,
        "ledger_record": asdict(ledger_record) if ledger_record else None,
        "model_dispatched": False,
        "authority_granted": False,
    }
