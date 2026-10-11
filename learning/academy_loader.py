"""Load and validate portable HumanOS Academy JSON packages."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Sequence, Tuple

from .academy_models import (
    AcademyPackage,
    Assessment,
    CertificationObjective,
    CertificationOverlay,
    Concept,
    CourseDefinition,
    Exercise,
    JobPack,
    JobRequirement,
    LabDefinition,
    ModuleDefinition,
    Resource,
    SkillDefinition,
)

PACKAGE_SCHEMA = "humanos.academy.package.v1"


def _require_mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object")
    return value


def _require_sequence(value: Any, name: str) -> Sequence[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{name} must be a list")
    return value


def _require_str(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()


def _optional_str(value: Any, name: str, default: str = "") -> str:
    if value is None:
        return default
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string")
    return value


def _string_tuple(value: Any, name: str) -> Tuple[str, ...]:
    items = _require_sequence(value, name)
    result = tuple(_require_str(item, f"{name}[]") for item in items)
    if len(result) != len(set(result)):
        raise ValueError(f"{name} must not contain duplicate identifiers")
    return result


def _unique_id(target: Dict[str, Any], key: str, kind: str) -> None:
    if key in target:
        raise ValueError(f"duplicate {kind} id: {key}")


def _parse_concepts(items: Iterable[Any], prefix: str) -> Tuple[Concept, ...]:
    result = []
    seen = set()
    for index, raw in enumerate(items):
        item = _require_mapping(raw, f"{prefix}.concepts[{index}]")
        cid = _require_str(item.get("concept_id"), f"{prefix}.concepts[{index}].concept_id")
        if cid in seen:
            raise ValueError(f"duplicate concept id: {cid}")
        seen.add(cid)
        result.append(Concept(
            concept_id=cid,
            title=_require_str(item.get("title"), f"{prefix}.concepts[{index}].title"),
            description=_optional_str(item.get("description"), f"{prefix}.concepts[{index}].description"),
        ))
    return tuple(result)


def _parse_exercises(items: Iterable[Any], prefix: str) -> Tuple[Exercise, ...]:
    result = []
    seen = set()
    for index, raw in enumerate(items):
        item = _require_mapping(raw, f"{prefix}.exercises[{index}]")
        eid = _require_str(item.get("exercise_id"), f"{prefix}.exercises[{index}].exercise_id")
        if eid in seen:
            raise ValueError(f"duplicate exercise id: {eid}")
        seen.add(eid)
        result.append(Exercise(
            exercise_id=eid,
            title=_require_str(item.get("title"), f"{prefix}.exercises[{index}].title"),
            kind=_optional_str(item.get("kind"), f"{prefix}.exercises[{index}].kind", "practice"),
            description=_optional_str(item.get("description"), f"{prefix}.exercises[{index}].description"),
        ))
    return tuple(result)


def _parse_assessments(items: Iterable[Any], prefix: str) -> Tuple[Assessment, ...]:
    result = []
    seen = set()
    for index, raw in enumerate(items):
        item = _require_mapping(raw, f"{prefix}.assessments[{index}]")
        aid = _require_str(item.get("assessment_id"), f"{prefix}.assessments[{index}].assessment_id")
        if aid in seen:
            raise ValueError(f"duplicate assessment id: {aid}")
        seen.add(aid)
        result.append(Assessment(
            assessment_id=aid,
            title=_require_str(item.get("title"), f"{prefix}.assessments[{index}].title"),
            kind=_optional_str(item.get("kind"), f"{prefix}.assessments[{index}].kind", "assessment"),
            description=_optional_str(item.get("description"), f"{prefix}.assessments[{index}].description"),
        ))
    return tuple(result)


def parse_package(data: Mapping[str, Any]) -> AcademyPackage:
    data = _require_mapping(data, "package")
    schema = _require_str(data.get("schema"), "schema")
    if schema != PACKAGE_SCHEMA:
        raise ValueError(f"unsupported Academy package schema: {schema}")

    skills: Dict[str, SkillDefinition] = {}
    for index, raw in enumerate(_require_sequence(data.get("skills", []), "skills")):
        item = _require_mapping(raw, f"skills[{index}]")
        skill_id = _require_str(item.get("skill_id"), f"skills[{index}].skill_id")
        _unique_id(skills, skill_id, "skill")
        skills[skill_id] = SkillDefinition(
            skill_id=skill_id,
            title=_require_str(item.get("title"), f"skills[{index}].title"),
            description=_optional_str(item.get("description"), f"skills[{index}].description"),
            domains=_string_tuple(item.get("domains", []), f"skills[{index}].domains"),
            prerequisites=_string_tuple(item.get("prerequisites", []), f"skills[{index}].prerequisites"),
            concepts=_parse_concepts(item.get("concepts", []), f"skills[{index}]"),
            exercises=_parse_exercises(item.get("exercises", []), f"skills[{index}]"),
            assessments=_parse_assessments(item.get("assessments", []), f"skills[{index}]"),
        )

    for skill in skills.values():
        missing = [skill_id for skill_id in skill.prerequisites if skill_id not in skills]
        if missing:
            raise ValueError(f"skill {skill.skill_id} references unknown prerequisites: {missing}")

    courses: Dict[str, CourseDefinition] = {}
    for c_index, raw in enumerate(_require_sequence(data.get("courses", []), "courses")):
        item = _require_mapping(raw, f"courses[{c_index}]")
        course_id = _require_str(item.get("course_id"), f"courses[{c_index}].course_id")
        _unique_id(courses, course_id, "course")

        modules = []
        module_ids = set()
        for m_index, raw_module in enumerate(_require_sequence(item.get("modules", []), f"courses[{c_index}].modules")):
            module = _require_mapping(raw_module, f"courses[{c_index}].modules[{m_index}]")
            module_id = _require_str(module.get("module_id"), f"courses[{c_index}].modules[{m_index}].module_id")
            if module_id in module_ids:
                raise ValueError(f"duplicate module id in {course_id}: {module_id}")
            module_ids.add(module_id)
            module_skill_ids = _string_tuple(module.get("skill_ids", []), f"courses[{c_index}].modules[{m_index}].skill_ids")
            missing = [skill_id for skill_id in module_skill_ids if skill_id not in skills]
            if missing:
                raise ValueError(f"module {module_id} references unknown skills: {missing}")
            modules.append(ModuleDefinition(
                module_id=module_id,
                title=_require_str(module.get("title"), f"courses[{c_index}].modules[{m_index}].title"),
                skill_ids=module_skill_ids,
                description=_optional_str(module.get("description"), f"courses[{c_index}].modules[{m_index}].description"),
            ))

        labs = []
        lab_ids = set()
        course_skill_ids = {skill_id for module in modules for skill_id in module.skill_ids}
        for l_index, raw_lab in enumerate(_require_sequence(item.get("labs", []), f"courses[{c_index}].labs")):
            lab = _require_mapping(raw_lab, f"courses[{c_index}].labs[{l_index}]")
            lab_id = _require_str(lab.get("lab_id"), f"courses[{c_index}].labs[{l_index}].lab_id")
            if lab_id in lab_ids:
                raise ValueError(f"duplicate lab id in {course_id}: {lab_id}")
            lab_ids.add(lab_id)
            lab_skill_ids = _string_tuple(lab.get("skill_ids", []), f"courses[{c_index}].labs[{l_index}].skill_ids")
            outside = [skill_id for skill_id in lab_skill_ids if skill_id not in course_skill_ids]
            if outside:
                raise ValueError(f"lab {lab_id} references skills outside parent course: {outside}")
            minutes = lab.get("estimated_minutes")
            if minutes is not None and (not isinstance(minutes, int) or minutes <= 0):
                raise ValueError(f"lab {lab_id} estimated_minutes must be a positive integer")
            labs.append(LabDefinition(
                lab_id=lab_id,
                title=_require_str(lab.get("title"), f"courses[{c_index}].labs[{l_index}].title"),
                skill_ids=lab_skill_ids,
                description=_optional_str(lab.get("description"), f"courses[{c_index}].labs[{l_index}].description"),
                estimated_minutes=minutes,
            ))

        certifications = []
        certification_ids = set()
        for o_index, raw_overlay in enumerate(_require_sequence(item.get("certifications", []), f"courses[{c_index}].certifications")):
            overlay = _require_mapping(raw_overlay, f"courses[{c_index}].certifications[{o_index}]")
            cert_id = _require_str(overlay.get("certification_id"), f"courses[{c_index}].certifications[{o_index}].certification_id")
            if cert_id in certification_ids:
                raise ValueError(f"duplicate certification overlay in {course_id}: {cert_id}")
            certification_ids.add(cert_id)
            objectives = []
            objective_ids = set()
            for obj_index, raw_objective in enumerate(_require_sequence(overlay.get("objectives", []), f"courses[{c_index}].certifications[{o_index}].objectives")):
                objective = _require_mapping(raw_objective, f"courses[{c_index}].certifications[{o_index}].objectives[{obj_index}]")
                objective_id = _require_str(objective.get("objective_id"), f"courses[{c_index}].certifications[{o_index}].objectives[{obj_index}].objective_id")
                if objective_id in objective_ids:
                    raise ValueError(f"duplicate certification objective id: {objective_id}")
                objective_ids.add(objective_id)
                objective_skill_ids = _string_tuple(objective.get("skill_ids", []), f"courses[{c_index}].certifications[{o_index}].objectives[{obj_index}].skill_ids")
                outside = [skill_id for skill_id in objective_skill_ids if skill_id not in course_skill_ids]
                if outside:
                    raise ValueError(f"certification {cert_id} objective {objective_id} references skills outside parent course: {outside}")
                objectives.append(CertificationObjective(
                    objective_id=objective_id,
                    title=_require_str(objective.get("title"), f"courses[{c_index}].certifications[{o_index}].objectives[{obj_index}].title"),
                    skill_ids=objective_skill_ids,
                ))
            certifications.append(CertificationOverlay(
                certification_id=cert_id,
                title=_require_str(overlay.get("title"), f"courses[{c_index}].certifications[{o_index}].title"),
                objectives=tuple(objectives),
                branch=_optional_str(overlay.get("branch"), f"courses[{c_index}].certifications[{o_index}].branch", "core"),
                notes=_optional_str(overlay.get("notes"), f"courses[{c_index}].certifications[{o_index}].notes"),
            ))

        courses[course_id] = CourseDefinition(
            course_id=course_id,
            title=_require_str(item.get("title"), f"courses[{c_index}].title"),
            modules=tuple(modules),
            description=_optional_str(item.get("description"), f"courses[{c_index}].description"),
            labs=tuple(labs),
            certifications=tuple(certifications),
        )

    job_packs: Dict[str, JobPack] = {}
    for j_index, raw in enumerate(_require_sequence(data.get("job_packs", []), "job_packs")):
        item = _require_mapping(raw, f"job_packs[{j_index}]")
        job_pack_id = _require_str(item.get("job_pack_id"), f"job_packs[{j_index}].job_pack_id")
        _unique_id(job_packs, job_pack_id, "job pack")
        requirements = []
        requirement_ids = set()
        for r_index, raw_requirement in enumerate(_require_sequence(item.get("requirements", []), f"job_packs[{j_index}].requirements")):
            requirement = _require_mapping(raw_requirement, f"job_packs[{j_index}].requirements[{r_index}]")
            requirement_id = _require_str(requirement.get("requirement_id"), f"job_packs[{j_index}].requirements[{r_index}].requirement_id")
            if requirement_id in requirement_ids:
                raise ValueError(f"duplicate job requirement id: {requirement_id}")
            requirement_ids.add(requirement_id)
            requirement_skill_ids = _string_tuple(requirement.get("skill_ids", []), f"job_packs[{j_index}].requirements[{r_index}].skill_ids")
            missing = [skill_id for skill_id in requirement_skill_ids if skill_id not in skills]
            if missing:
                raise ValueError(f"job pack {job_pack_id} references unknown skills: {missing}")
            employer_specific = requirement.get("employer_specific", False)
            if not isinstance(employer_specific, bool):
                raise ValueError(f"job pack {job_pack_id} employer_specific must be boolean")
            requirements.append(JobRequirement(
                requirement_id=requirement_id,
                title=_require_str(requirement.get("title"), f"job_packs[{j_index}].requirements[{r_index}].title"),
                skill_ids=requirement_skill_ids,
                employer_specific=employer_specific,
            ))
        job_packs[job_pack_id] = JobPack(
            job_pack_id=job_pack_id,
            title=_require_str(item.get("title"), f"job_packs[{j_index}].title"),
            requirements=tuple(requirements),
            notes=_optional_str(item.get("notes"), f"job_packs[{j_index}].notes"),
        )

    resources: Dict[str, Resource] = {}
    for r_index, raw in enumerate(_require_sequence(data.get("resources", []), "resources")):
        item = _require_mapping(raw, f"resources[{r_index}]")
        resource_id = _require_str(item.get("resource_id"), f"resources[{r_index}].resource_id")
        _unique_id(resources, resource_id, "resource")
        resources[resource_id] = Resource(
            resource_id=resource_id,
            title=_require_str(item.get("title"), f"resources[{r_index}].title"),
            resource_type=_require_str(item.get("resource_type"), f"resources[{r_index}].resource_type"),
            locator=_optional_str(item.get("locator"), f"resources[{r_index}].locator"),
        )

    metadata = data.get("metadata", {})
    metadata = dict(_require_mapping(metadata, "metadata"))

    return AcademyPackage(
        schema=schema,
        package_id=_require_str(data.get("package_id"), "package_id"),
        title=_require_str(data.get("title"), "title"),
        version=_require_str(data.get("version"), "version"),
        skills=skills,
        courses=courses,
        job_packs=job_packs,
        resources=resources,
        metadata=metadata,
    )


def load_package(path: Path | str) -> AcademyPackage:
    source = Path(path)
    with source.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return parse_package(data)
