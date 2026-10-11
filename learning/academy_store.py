"""Local-first append-only runtime state for the HumanOS Academy."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from .mastery_engine import DIMENSIONS, STAGES, WEIGHTS

EVENT_TYPES = {
    "FOCUS_SELECTED",
    "FOCUS_PAUSED",
    "ACTIVITY_STARTED",
    "ACTIVITY_COMPLETED",
    "SKILL_STAGE_SET",
    "EVIDENCE_RECORDED",
    "CHECKPOINT_RECORDED",
}


class AcademyStore:
    """SQLite event ledger whose derived state can be rebuilt at any time.

    Real learner state belongs in a private local database. The repository contains
    only this reusable storage implementation and synthetic tests.
    """

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.path))
        self.connection.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.connection.executescript(
            """
            PRAGMA journal_mode=WAL;
            PRAGMA foreign_keys=ON;
            CREATE TABLE IF NOT EXISTS academy_events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                event_type TEXT NOT NULL,
                course_id TEXT,
                module_id TEXT,
                skill_id TEXT,
                activity_id TEXT,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_academy_events_type
                ON academy_events(event_type, seq);
            CREATE INDEX IF NOT EXISTS idx_academy_events_activity
                ON academy_events(activity_id, seq);
            CREATE INDEX IF NOT EXISTS idx_academy_events_skill
                ON academy_events(skill_id, seq);
            CREATE TRIGGER IF NOT EXISTS academy_events_no_update
            BEFORE UPDATE ON academy_events
            BEGIN
                SELECT RAISE(ABORT, 'academy events are append-only');
            END;
            CREATE TRIGGER IF NOT EXISTS academy_events_no_delete
            BEFORE DELETE ON academy_events
            BEGIN
                SELECT RAISE(ABORT, 'academy events are append-only');
            END;
            """
        )
        self.connection.commit()

    @staticmethod
    def _timestamp(value: Optional[str] = None) -> str:
        if value is None:
            return datetime.now(timezone.utc).isoformat()
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("created_at must be ISO-8601") from exc
        if parsed.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if parsed.astimezone(timezone.utc) > datetime.now(timezone.utc):
            raise ValueError("created_at cannot be in the future")
        return value

    @staticmethod
    def _focus_key(focus: Dict[str, Any]) -> str:
        activity_id = focus.get("activity_id")
        if activity_id:
            return f"activity:{activity_id}"
        course_id = focus.get("course_id") or ""
        module_id = focus.get("module_id") or ""
        return f"focus:{course_id}:{module_id}"

    def append_event(
        self,
        event_type: str,
        payload: Dict[str, Any],
        *,
        course_id: Optional[str] = None,
        module_id: Optional[str] = None,
        skill_id: Optional[str] = None,
        activity_id: Optional[str] = None,
        event_id: Optional[str] = None,
        created_at: Optional[str] = None,
    ) -> str:
        if event_type not in EVENT_TYPES:
            raise ValueError(f"unsupported Academy event type: {event_type}")
        if not isinstance(payload, dict):
            raise ValueError("event payload must be an object")
        event_id = event_id or str(uuid.uuid4())
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

        # Check before generating a new timestamp so a network/process retry using the
        # same deterministic event_id remains idempotent even when created_at was not
        # repeated by the caller.
        existing = self.connection.execute(
            "SELECT event_type, course_id, module_id, skill_id, activity_id, payload_json, created_at "
            "FROM academy_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        if existing is not None:
            semantic = (event_type, course_id, module_id, skill_id, activity_id, encoded)
            if tuple(existing)[:6] == semantic:
                if created_at is not None and existing["created_at"] != self._timestamp(created_at):
                    raise ValueError(f"Academy event_id collision: {event_id}")
                return event_id
            raise ValueError(f"Academy event_id collision: {event_id}")

        timestamp = self._timestamp(created_at)
        try:
            self.connection.execute(
                """
                INSERT INTO academy_events
                    (event_id, event_type, course_id, module_id, skill_id, activity_id, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (event_id, event_type, course_id, module_id, skill_id, activity_id, encoded, timestamp),
            )
            self.connection.commit()
        except sqlite3.IntegrityError as exc:
            # Concurrent writers can race the pre-check. Re-read and accept only an
            # exact semantic retry; anything else is a collision and fails closed.
            row = self.connection.execute(
                "SELECT event_type, course_id, module_id, skill_id, activity_id, payload_json, created_at "
                "FROM academy_events WHERE event_id = ?",
                (event_id,),
            ).fetchone()
            semantic = (event_type, course_id, module_id, skill_id, activity_id, encoded)
            if row is not None and tuple(row)[:6] == semantic:
                if created_at is not None and row["created_at"] != timestamp:
                    raise ValueError(f"Academy event_id collision: {event_id}") from exc
                return event_id
            raise ValueError(f"Academy event_id collision: {event_id}") from exc
        return event_id

    def select_focus(
        self,
        course_id: str,
        *,
        module_id: Optional[str] = None,
        activity_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> str:
        if not course_id:
            raise ValueError("course_id is required")
        focus = {
            "course_id": course_id,
            "module_id": module_id,
            "activity_id": activity_id,
            "title": title,
        }
        focus["focus_key"] = self._focus_key(focus)
        return self.append_event(
            "FOCUS_SELECTED",
            {"focus": focus},
            course_id=course_id,
            module_id=module_id,
            activity_id=activity_id,
        )

    def pause_focus(self, reason: str = "") -> Optional[str]:
        state = self.rebuild_state()
        focus = state["current_focus"]
        if focus is None:
            return None
        return self.append_event(
            "FOCUS_PAUSED",
            {"focus": focus, "reason": reason},
            course_id=focus.get("course_id"),
            module_id=focus.get("module_id"),
            activity_id=focus.get("activity_id"),
        )

    def resume_focus(self, focus_key: str) -> str:
        state = self.rebuild_state()
        focus = state["paused_focuses"].get(focus_key)
        if focus is None:
            activity = state["unfinished"].get(focus_key.removeprefix("activity:"))
            if activity is not None:
                focus = {
                    "course_id": activity.get("course_id"),
                    "module_id": activity.get("module_id"),
                    "activity_id": activity.get("activity_id"),
                    "title": activity.get("title"),
                }
        if focus is None:
            raise KeyError(f"unknown paused/unfinished focus: {focus_key}")
        return self.select_focus(
            focus["course_id"],
            module_id=focus.get("module_id"),
            activity_id=focus.get("activity_id"),
            title=focus.get("title"),
        )

    def start_activity(
        self,
        activity_id: str,
        course_id: str,
        *,
        module_id: Optional[str] = None,
        title: Optional[str] = None,
    ) -> str:
        if not activity_id or not course_id:
            raise ValueError("activity_id and course_id are required")
        state = self.rebuild_state()
        if activity_id in state["unfinished"]:
            existing = state["unfinished"][activity_id]
            requested = {"course_id": course_id, "module_id": module_id, "title": title}
            current = {key: existing.get(key) for key in requested}
            if current == requested:
                raise ValueError(f"activity already in progress: {activity_id}")
            raise ValueError(f"activity_id already belongs to another unfinished activity: {activity_id}")
        return self.append_event(
            "ACTIVITY_STARTED",
            {
                "activity_id": activity_id,
                "course_id": course_id,
                "module_id": module_id,
                "title": title,
            },
            course_id=course_id,
            module_id=module_id,
            activity_id=activity_id,
        )

    def complete_activity(self, activity_id: str, *, summary: str = "") -> str:
        if not activity_id:
            raise ValueError("activity_id is required")
        state = self.rebuild_state()
        if activity_id not in state["unfinished"]:
            raise KeyError(f"activity is not unfinished: {activity_id}")
        activity = state["unfinished"][activity_id]
        return self.append_event(
            "ACTIVITY_COMPLETED",
            {"activity_id": activity_id, "summary": summary},
            course_id=activity.get("course_id"),
            module_id=activity.get("module_id"),
            activity_id=activity_id,
        )

    def set_skill_stage(self, skill_id: str, stage: str, *, reason: str = "") -> str:
        if stage not in STAGES:
            raise ValueError(f"invalid stage: {stage}")
        return self.append_event(
            "SKILL_STAGE_SET",
            {"stage": stage, "reason": reason},
            skill_id=skill_id,
        )

    def record_evidence(
        self,
        evidence_id: str,
        skill_id: str,
        scores: Dict[str, float],
        *,
        source: str,
        summary: str,
        course_id: Optional[str] = None,
        activity_id: Optional[str] = None,
        created_at: Optional[str] = None,
    ) -> str:
        if not evidence_id or not skill_id:
            raise ValueError("evidence_id and skill_id are required")
        if not scores:
            raise ValueError("evidence must contain at least one score")
        normalized: Dict[str, float] = {}
        for dimension, value in scores.items():
            if dimension not in DIMENSIONS or not isinstance(value, (int, float)) or not 0 <= float(value) <= 5:
                raise ValueError("scores must use mastery dimensions and range 0..5")
            normalized[dimension] = float(value)
        return self.append_event(
            "EVIDENCE_RECORDED",
            {
                "evidence_id": evidence_id,
                "scores": normalized,
                "source": source,
                "summary": summary,
            },
            course_id=course_id,
            skill_id=skill_id,
            activity_id=activity_id,
            event_id=f"evidence:{evidence_id}",
            created_at=created_at,
        )

    def checkpoint(self, label: str, *, note: str = "") -> str:
        if not label:
            raise ValueError("checkpoint label is required")
        return self.append_event("CHECKPOINT_RECORDED", {"label": label, "note": note})

    def iter_events(self) -> Iterable[sqlite3.Row]:
        return self.connection.execute("SELECT * FROM academy_events ORDER BY seq")

    def rebuild_state(self) -> Dict[str, Any]:
        current_focus: Optional[Dict[str, Any]] = None
        paused_focuses: Dict[str, Dict[str, Any]] = {}
        unfinished: Dict[str, Dict[str, Any]] = {}
        stages: Dict[str, str] = {}
        evidence: Dict[str, list[Dict[str, float]]] = {}
        checkpoints = []
        event_count = 0

        for row in self.iter_events():
            event_count += 1
            payload = json.loads(row["payload_json"])
            event_type = row["event_type"]
            if event_type == "FOCUS_SELECTED":
                current_focus = dict(payload["focus"])
                paused_focuses.pop(current_focus["focus_key"], None)
            elif event_type == "FOCUS_PAUSED":
                focus = dict(payload["focus"])
                paused_focuses[focus["focus_key"]] = focus
                if current_focus and current_focus.get("focus_key") == focus.get("focus_key"):
                    current_focus = None
            elif event_type == "ACTIVITY_STARTED":
                activity = dict(payload)
                activity["status"] = "IN_PROGRESS"
                unfinished[activity["activity_id"]] = activity
            elif event_type == "ACTIVITY_COMPLETED":
                activity_id = payload["activity_id"]
                unfinished.pop(activity_id, None)
                paused_focuses.pop(f"activity:{activity_id}", None)
                if current_focus and current_focus.get("activity_id") == activity_id:
                    current_focus = None
            elif event_type == "SKILL_STAGE_SET":
                stages[row["skill_id"]] = payload["stage"]
            elif event_type == "EVIDENCE_RECORDED":
                evidence.setdefault(row["skill_id"], []).append(payload["scores"])
            elif event_type == "CHECKPOINT_RECORDED":
                checkpoints.append({"seq": row["seq"], **payload, "created_at": row["created_at"]})

        skill_state: Dict[str, Dict[str, Any]] = {}
        all_skill_ids = set(stages) | set(evidence)
        for skill_id in sorted(all_skill_ids):
            items = evidence.get(skill_id, [])
            averages: Dict[str, float] = {}
            for dimension in DIMENSIONS:
                values = [float(item[dimension]) for item in items if dimension in item]
                averages[dimension] = sum(values) / len(values) if values else 0.0
            mastery = round(sum(averages[dimension] * WEIGHTS[dimension] for dimension in DIMENSIONS) * 20, 1)
            skill_state[skill_id] = {
                "stage": stages.get(skill_id, "unseen"),
                "scores": averages,
                "mastery_percent": mastery,
                "evidence_count": len(items),
                "metric_status": "ESTIMATED_FROM_RECORDED_EVIDENCE",
            }

        return {
            "schema": "humanos.academy.state.v1",
            "current_focus": current_focus,
            "paused_focuses": paused_focuses,
            "unfinished": unfinished,
            "skills": skill_state,
            "checkpoints": checkpoints,
            "event_count": event_count,
            "policy": {
                "unfinished_is_current": False,
                "current_focus_requires_explicit_selection": True,
                "event_ledger_append_only": True,
            },
        }

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "AcademyStore":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
