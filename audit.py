from __future__ import annotations
import hashlib, json
from dataclasses import dataclass
from typing import Any, Iterable

@dataclass(frozen=True)
class AuditEvent:
    seq: int
    event_type: str
    action_id: str
    body: dict[str, Any]
    previous_hash: str
    event_hash: str


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def hash_event(seq: int, event_type: str, action_id: str, body: dict[str, Any], previous_hash: str) -> str:
    raw = canonical_json({"seq": seq, "event_type": event_type, "action_id": action_id, "body": body, "previous_hash": previous_hash})
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def verify_chain(events: Iterable[AuditEvent]) -> bool:
    previous = "GENESIS"
    expected_seq = 1
    for event in events:
        if event.seq != expected_seq or event.previous_hash != previous:
            return False
        if hash_event(event.seq, event.event_type, event.action_id, event.body, previous) != event.event_hash:
            return False
        previous = event.event_hash
        expected_seq += 1
    return True
