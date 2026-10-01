"""Machine-readable HumanOS Academy teaching protocol."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

PROTOCOL_SCHEMA = "humanos.academy.teaching-protocol.v1"
DEFAULT_PROTOCOL_PATH = Path(__file__).resolve().parent / "protocols" / "humanos-teaching-v1.json"
REQUIRED_INVARIANT = "AI_MUST_NOT_DO_TARGET_COGNITIVE_WORK"


@dataclass(frozen=True)
class TeachingProtocol:
    schema: str
    protocol_id: str
    title: str
    stages: Tuple[str, ...]
    invariants: Tuple[str, ...]
    roles: Tuple[str, ...]
    grading: Dict[str, float]

    def stage_index(self, stage: str) -> int:
        return self.stages.index(stage)


def load_teaching_protocol(path: Path | str = DEFAULT_PROTOCOL_PATH) -> TeachingProtocol:
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    if raw.get("schema") != PROTOCOL_SCHEMA:
        raise ValueError("unsupported teaching protocol schema")
    for key in ("protocol_id", "title"):
        if not isinstance(raw.get(key), str) or not raw[key].strip():
            raise ValueError(f"{key} must be a non-empty string")
    stages = tuple(raw.get("stages", ()))
    invariants = tuple(raw.get("invariants", ()))
    roles = tuple(raw.get("roles", ()))
    if not stages or any(not isinstance(item, str) or not item for item in stages):
        raise ValueError("teaching protocol stages must be non-empty strings")
    if len(stages) != len(set(stages)):
        raise ValueError("teaching protocol stages must be unique")
    if REQUIRED_INVARIANT not in invariants:
        raise ValueError("teaching protocol must preserve the cognitive-work invariant")
    grading = raw.get("grading", {})
    expected = {"knowledge", "practical", "diagnostic", "communication"}
    if set(grading) != expected:
        raise ValueError("teaching protocol grading dimensions are incomplete")
    if any(not isinstance(value, (int, float)) or value < 0 for value in grading.values()):
        raise ValueError("grading weights must be non-negative numbers")
    if abs(sum(float(value) for value in grading.values()) - 1.0) > 1e-9:
        raise ValueError("grading weights must sum to 1.0")
    return TeachingProtocol(
        schema=raw["schema"],
        protocol_id=raw["protocol_id"],
        title=raw["title"],
        stages=stages,
        invariants=invariants,
        roles=roles,
        grading={key: float(value) for key, value in grading.items()},
    )


def load_default_teaching_protocol() -> TeachingProtocol:
    return load_teaching_protocol(DEFAULT_PROTOCOL_PATH)
