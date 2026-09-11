"""HumanOS Adaptive Mastery Engine v1.

Local-first, human-governed learning state. Evidence is append-only inside the
engine, scores are derived from evidence, and researched curriculum remains a
candidate until an external governed human action promotes it.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

STAGES = ("unseen", "introduced", "assisted", "practiced", "demonstrated", "mastered")
DIMENSIONS = ("knowledge", "practical", "diagnostic", "communication")
WEIGHTS = {"knowledge": .25, "practical": .30, "diagnostic": .25, "communication": .20}
EVIDENCE_SCHEMA_VERSION = 1

@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    skill_id: str
    source: str
    summary: str
    scores: Dict[str, float]
    project: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    schema_version: int = EVIDENCE_SCHEMA_VERSION

@dataclass
class Skill:
    skill_id: str
    title: str
    domains: List[str]
    prerequisites: List[str] = field(default_factory=list)
    priority: float = 0.5
    stage: str = "unseen"
    scores: Dict[str, float] = field(default_factory=lambda: {d: 0.0 for d in DIMENSIONS})
    evidence_ids: List[str] = field(default_factory=list)
    last_practiced: Optional[str] = None

    @property
    def mastery_percent(self) -> float:
        return round(sum(self.scores.get(k, 0.0) * WEIGHTS[k] for k in DIMENSIONS) * 20, 1)

@dataclass
class Course:
    course_id: str
    title: str
    skill_ids: List[str]
    active: bool = True
    career_readiness_percent: Optional[float] = None

class MasteryEngine:
    def __init__(self) -> None:
        self.skills: Dict[str, Skill] = {}
        self.courses: Dict[str, Course] = {}
        self.evidence: Dict[str, Evidence] = {}
        self.curriculum_candidates: List[dict] = []

    def add_skill(self, skill: Skill) -> None:
        if skill.stage not in STAGES:
            raise ValueError(f"invalid stage: {skill.stage}")
        self.skills[skill.skill_id] = skill

    def add_course(self, course: Course) -> None:
        missing = [s for s in course.skill_ids if s not in self.skills]
        if missing:
            raise ValueError(f"course references unknown skills: {missing}")
        self.courses[course.course_id] = course

    @staticmethod
    def _validate_created_at(created_at: str) -> None:
        try:
            parsed = datetime.fromisoformat(created_at)
        except ValueError as exc:
            raise ValueError("created_at must be ISO-8601") from exc
        if parsed.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        if parsed.astimezone(timezone.utc) > datetime.now(timezone.utc):
            raise ValueError("created_at cannot be in the future")

    def _recompute_skill(self, skill_id: str) -> None:
        skill = self.skills[skill_id]
        items = [self.evidence[eid] for eid in skill.evidence_ids]
        for dimension in DIMENSIONS:
            values = [float(e.scores[dimension]) for e in items if dimension in e.scores]
            skill.scores[dimension] = sum(values) / len(values) if values else 0.0

    def record_evidence(self, item: Evidence) -> None:
        if item.skill_id not in self.skills:
            raise KeyError(f"unknown skill: {item.skill_id}")
        if not item.evidence_id:
            raise ValueError("evidence_id is required")
        if item.evidence_id in self.evidence:
            if self.evidence[item.evidence_id] == item:
                return
            raise ValueError(f"evidence_id collision: {item.evidence_id}")
        if not item.scores:
            raise ValueError("evidence must contain at least one score")
        for key, value in item.scores.items():
            if key not in DIMENSIONS or not 0 <= value <= 5:
                raise ValueError("scores must use mastery dimensions and range 0..5")
        self._validate_created_at(item.created_at)
        skill = self.skills[item.skill_id]
        self.evidence[item.evidence_id] = item
        skill.evidence_ids.append(item.evidence_id)
        skill.last_practiced = item.created_at
        self._recompute_skill(item.skill_id)

    def course_mastery_percent(self, course_id: str) -> float:
        course = self.courses[course_id]
        values = [self.skills[s].mastery_percent for s in course.skill_ids]
        return round(sum(values) / len(values), 1) if values else 0.0

    def course_completion_percent(self, course_id: str) -> float:
        course = self.courses[course_id]
        covered = sum(self.skills[s].stage != "unseen" for s in course.skill_ids)
        return round(100 * covered / len(course.skill_ids), 1) if course.skill_ids else 0.0

    def biggest_gaps(self, course_id: str, limit: int = 5) -> List[Skill]:
        course = self.courses[course_id]
        candidates = [self.skills[s] for s in course.skill_ids]
        return sorted(candidates, key=lambda s: (s.mastery_percent / 100) - s.priority)[:limit]

    def gap_reasons(self, course_id: str, limit: int = 5) -> List[dict]:
        return [{"skill_id": s.skill_id, "mastery_percent": s.mastery_percent, "priority": s.priority,
                 "reason": "high priority relative to current evidence-derived mastery"}
                for s in self.biggest_gaps(course_id, limit)]

    def encounter(self, skill_id: str) -> None:
        skill = self.skills[skill_id]
        if skill.stage == "unseen":
            skill.stage = "introduced"

    def propose_curriculum_update(self, title: str, rationale: str, sources: Iterable[str]) -> dict:
        candidate = {"title": title, "rationale": rationale, "sources": list(sources), "status": "candidate"}
        self.curriculum_candidates.append(candidate)
        return candidate

    def snapshot(self) -> dict:
        return {
            "schema": "humanos.mastery.v1",
            "skills": {k: asdict(v) | {"mastery_percent": v.mastery_percent} for k, v in self.skills.items()},
            "courses": {k: asdict(v) | {"completion_percent": self.course_completion_percent(k),
                "mastery_percent": self.course_mastery_percent(k), "metric_status": "ESTIMATED_FROM_RECORDED_EVIDENCE",
                "evidence_count": sum(len(self.skills[s].evidence_ids) for s in v.skill_ids)} for k, v in self.courses.items()},
            "evidence": {k: asdict(v) for k, v in self.evidence.items()},
            "curriculum_candidates": list(self.curriculum_candidates),
            "policy": {"curriculum_self_promotion": False, "metrics_execute_external_actions": False,
                       "cross_project_evidence_default": "not_automatically_imported"},
        }
