"""Generic public catalog API with synthetic demonstration entries only."""

from __future__ import annotations

from copy import deepcopy
from typing import Optional

from .mastery_engine import Course, MasteryEngine, Skill


SKILLS = [
    Skill(
        "sample-skill-foundations",
        "Foundational workflow",
        ["learning"],
        priority=0.5,
    ),
    Skill(
        "sample-skill-threat-modeling",
        "Threat modeling",
        ["security"],
        prerequisites=["sample-skill-foundations"],
        priority=0.6,
    ),
    Skill(
        "sample-skill-automation",
        "Automation workflow",
        ["automation"],
        prerequisites=["sample-skill-foundations"],
        priority=0.55,
    ),
]

CYBER = Course(
    course_id="sample-security-lab",
    title="Sample Security Lab",
    skill_ids=["sample-skill-foundations", "sample-skill-threat-modeling"],
)

AI = Course(
    course_id="sample-automation-workflow",
    title="Sample Automation Workflow",
    skill_ids=["sample-skill-foundations", "sample-skill-automation"],
)

COURSES = (CYBER, AI)


def seed(engine: MasteryEngine) -> MasteryEngine:
    """Add the synthetic demonstration catalog to ``engine`` and return it.

    Fresh copies prevent evidence or progression in one engine instance from
    changing the module-level demonstration fixtures or another instance.
    """
    for skill in SKILLS:
        engine.add_skill(deepcopy(skill))
    for course in COURSES:
        engine.add_course(deepcopy(course))
    return engine


def load_catalog(engine: Optional[MasteryEngine] = None) -> MasteryEngine:
    """Load the synthetic catalog into a supplied or newly created engine."""
    return seed(engine if engine is not None else MasteryEngine())


def get_course(engine: MasteryEngine, course_id: str) -> Optional[Course]:
    """Return a catalog course, or ``None`` when the identifier is unknown."""
    return engine.courses.get(course_id)
