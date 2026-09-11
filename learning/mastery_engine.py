"""HumanOS Adaptive Mastery Engine v1.

Local-first, human-governed learning state.  The engine records evidence and
recommends priorities; it never silently promotes researched curriculum.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional

STAGES = ("unseen", "introduced", "assisted", "practiced", "demonstrated", "mastered")
DIMENSIONS = ("knowledge", "practical", "diagnostic", "communication")
WEIGHTS = {"knowledge": .25, "practical": .30, "diagnostic": .25, "communication": .20}

@dataclass
class Evidence:
    evidence_id: str
    skill_id: str
    source: str
    summary: str
    scores: Dict[str, float]
    project: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

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
        self.courses[course.course_id] = course

    def record_evidence(self, item: Evidence) -> None:
        skill = self.skills[item.skill_id]
        for key, value in item.scores.items():
            if key not in DIMENSIONS or not 0 <= value <= 5:
                raise ValueError("scores must use mastery dimensions and range 0..5")
            skill.scores[key] = max(skill.scores[key], float(value))
        skill.evidence_ids.append(item.evidence_id)
        skill.last_practiced = item.created_at
        self.evidence[item.evidence_id] = item

    def course_mastery_percent(self, course_id: str) -> float:
        course = self.courses[course_id]
        values = [self.skills[s].mastery_percent for s in course.skill_ids if s in self.skills]
        return round(sum(values) / len(values), 1) if values else 0.0

    def course_completion_percent(self, course_id: str) -> float:
        course = self.courses[course_id]
        covered = sum(self.skills[s].stage != "unseen" for s in course.skill_ids if s in self.skills)
        return round(100 * covered / len(course.skill_ids), 1) if course.skill_ids else 0.0

    def biggest_gaps(self, course_id: str, limit: int = 5) -> List[Skill]:
        course = self.courses[course_id]
        candidates = [self.skills[s] for s in course.skill_ids if s in self.skills]
        return sorted(candidates, key=lambda s: (s.mastery_percent / 100) - s.priority)[:limit]

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
            "skills": {k: asdict(v) | {"mastery_percent": v.mastery_percent} for k, v in self.skills.items()},
            "courses": {k: asdict(v) | {"completion_percent": self.course_completion_percent(k), "mastery_percent": self.course_mastery_percent(k)} for k, v in self.courses.items()},
            "evidence": {k: asdict(v) for k, v in self.evidence.items()},
            "curriculum_candidates": list(self.curriculum_candidates),
        }
