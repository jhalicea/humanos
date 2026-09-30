"""Provider-neutral data model for the HumanOS Academy.

This module contains reusable curriculum structure only. Real learner curricula and
state belong in an authorized private Academy store.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Concept:
    concept_id: str
    title: str
    description: str = ""


@dataclass(frozen=True)
class Exercise:
    exercise_id: str
    title: str
    kind: str = "practice"
    description: str = ""


@dataclass(frozen=True)
class Assessment:
    assessment_id: str
    title: str
    kind: str = "assessment"
    description: str = ""


@dataclass(frozen=True)
class Resource:
    resource_id: str
    title: str
    resource_type: str
    locator: str = ""


@dataclass(frozen=True)
class SkillDefinition:
    skill_id: str
    title: str
    description: str = ""
    domains: Tuple[str, ...] = ()
    prerequisites: Tuple[str, ...] = ()
    concepts: Tuple[Concept, ...] = ()
    exercises: Tuple[Exercise, ...] = ()
    assessments: Tuple[Assessment, ...] = ()


@dataclass(frozen=True)
class ModuleDefinition:
    module_id: str
    title: str
    skill_ids: Tuple[str, ...]
    description: str = ""


@dataclass(frozen=True)
class LabDefinition:
    lab_id: str
    title: str
    skill_ids: Tuple[str, ...]
    description: str = ""
    estimated_minutes: Optional[int] = None


@dataclass(frozen=True)
class CertificationObjective:
    objective_id: str
    title: str
    skill_ids: Tuple[str, ...]


@dataclass(frozen=True)
class CertificationOverlay:
    certification_id: str
    title: str
    objectives: Tuple[CertificationObjective, ...]
    branch: str = "core"
    notes: str = ""

    @property
    def skill_ids(self) -> Tuple[str, ...]:
        seen: List[str] = []
        for objective in self.objectives:
            for skill_id in objective.skill_ids:
                if skill_id not in seen:
                    seen.append(skill_id)
        return tuple(seen)


@dataclass(frozen=True)
class CourseDefinition:
    course_id: str
    title: str
    modules: Tuple[ModuleDefinition, ...]
    description: str = ""
    labs: Tuple[LabDefinition, ...] = ()
    certifications: Tuple[CertificationOverlay, ...] = ()

    @property
    def skill_ids(self) -> Tuple[str, ...]:
        seen: List[str] = []
        for module in self.modules:
            for skill_id in module.skill_ids:
                if skill_id not in seen:
                    seen.append(skill_id)
        return tuple(seen)


@dataclass(frozen=True)
class JobRequirement:
    requirement_id: str
    title: str
    skill_ids: Tuple[str, ...]
    employer_specific: bool = False


@dataclass(frozen=True)
class JobPack:
    job_pack_id: str
    title: str
    requirements: Tuple[JobRequirement, ...]
    notes: str = ""

    @property
    def skill_ids(self) -> Tuple[str, ...]:
        seen: List[str] = []
        for requirement in self.requirements:
            for skill_id in requirement.skill_ids:
                if skill_id not in seen:
                    seen.append(skill_id)
        return tuple(seen)


@dataclass(frozen=True)
class AcademyPackage:
    schema: str
    package_id: str
    title: str
    version: str
    skills: Dict[str, SkillDefinition]
    courses: Dict[str, CourseDefinition]
    job_packs: Dict[str, JobPack] = field(default_factory=dict)
    resources: Dict[str, Resource] = field(default_factory=dict)
    metadata: Dict[str, object] = field(default_factory=dict)

    def get_course(self, course_id: str) -> Optional[CourseDefinition]:
        return self.courses.get(course_id)

    def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
        return self.skills.get(skill_id)
