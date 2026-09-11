"""Portable HumanOS learning goal profiles.

Goal profiles provide a finite finish line without claiming total domain mastery.
They consume normalized skill state and are independent of the LLM/provider used
to teach, discuss, or assess candidate evidence.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class GoalRequirement:
    skill_id: str
    target_mastery_percent: float
    minimum_stage: str = "demonstrated"
    required: bool = True
    rationale: str = ""

    def __post_init__(self) -> None:
        if not 0 <= self.target_mastery_percent <= 100:
            raise ValueError("target_mastery_percent must be in 0..100")


@dataclass
class GoalProfile:
    goal_id: str
    title: str
    requirements: List[GoalRequirement]
    description: str = ""
    source: str = "human_defined"
    version: str = "1"
    status: str = "candidate"
    metadata: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class GoalSkillResult:
    skill_id: str
    current_mastery_percent: float
    target_mastery_percent: float
    confidence_level: str
    evidence_count: int
    gap_percent: float
    meets_target: bool


class GoalPathEngine:
    """Derive a transparent path from current evidence to a bounded goal."""

    def __init__(self, mastery_engine) -> None:
        self.mastery = mastery_engine
        self.goals: Dict[str, GoalProfile] = {}

    def add_goal(self, goal: GoalProfile) -> None:
        missing = [r.skill_id for r in goal.requirements if r.skill_id not in self.mastery.skills]
        if missing:
            raise ValueError(f"goal references unknown skills: {missing}")
        if goal.status not in ("candidate", "active", "completed", "archived"):
            raise ValueError(f"invalid goal status: {goal.status}")
        self.goals[goal.goal_id] = goal

    def evaluate(self, goal_id: str) -> List[GoalSkillResult]:
        goal = self.goals[goal_id]
        results = []
        for requirement in goal.requirements:
            skill = self.mastery.skills[requirement.skill_id]
            current = skill.mastery_percent
            gap = max(0.0, round(requirement.target_mastery_percent - current, 1))
            confidence = skill.confidence
            results.append(GoalSkillResult(
                skill_id=skill.skill_id,
                current_mastery_percent=current,
                target_mastery_percent=requirement.target_mastery_percent,
                confidence_level=confidence["level"],
                evidence_count=confidence["evidence_count"],
                gap_percent=gap,
                meets_target=current >= requirement.target_mastery_percent and confidence["level"] in ("medium", "high"),
            ))
        return results

    def completion_percent(self, goal_id: str) -> float:
        results = self.evaluate(goal_id)
        if not results:
            return 0.0
        ratios = [min(1.0, r.current_mastery_percent / r.target_mastery_percent) if r.target_mastery_percent else 1.0 for r in results]
        return round(100 * sum(ratios) / len(ratios), 1)

    def next_path(self, goal_id: str, limit: int = 5) -> List[GoalSkillResult]:
        """Largest remaining normalized gaps first; deterministic and inspectable."""
        return sorted(
            [r for r in self.evaluate(goal_id) if not r.meets_target],
            key=lambda r: (-(r.gap_percent / r.target_mastery_percent if r.target_mastery_percent else 0), r.skill_id),
        )[:limit]

    def snapshot(self, goal_id: str) -> dict:
        goal = self.goals[goal_id]
        return {
            "schema": "humanos.learning_goal.v1",
            "goal": asdict(goal),
            "completion_percent": self.completion_percent(goal_id),
            "skill_results": [asdict(r) for r in self.evaluate(goal_id)],
            "next_path": [asdict(r) for r in self.next_path(goal_id)],
            "meaning": "Completion measures progress toward this bounded goal; it does not claim total domain mastery.",
            "policy": {
                "provider_neutral": True,
                "llm_can_change_grade_directly": False,
                "human_goal_authority": True,
                "market_reconciliation_is_evidence_not_authority": True,
            },
        }
