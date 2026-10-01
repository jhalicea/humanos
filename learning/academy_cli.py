"""CLI vertical slice for the HumanOS Academy runtime."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Iterable, Optional

from .academy_loader import load_package
from .academy_store import AcademyStore
from .teaching_protocol import load_default_teaching_protocol

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = Path(
    os.environ.get(
        "HUMANOS_ACADEMY_DB",
        Path.home() / ".humanos" / "private" / "academy" / "academy.sqlite3",
    )
)
DEFAULT_PACKAGE = Path(
    os.environ.get(
        "HUMANOS_ACADEMY_PACKAGE",
        REPO_ROOT / "examples" / "academy" / "synthetic-academy-v1.json",
    )
)


def _emit(payload: object, pretty: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2 if pretty else None))


def _coverage(skill_ids: Iterable[str], state: Dict[str, object]) -> Dict[str, object]:
    ids = list(dict.fromkeys(skill_ids))
    skills = state.get("skills", {})
    covered = 0
    details = []
    for skill_id in ids:
        skill_state = skills.get(skill_id, {}) if isinstance(skills, dict) else {}
        stage = skill_state.get("stage", "unseen")
        mastery = float(skill_state.get("mastery_percent", 0.0))
        has_evidence = int(skill_state.get("evidence_count", 0)) > 0
        is_covered = stage != "unseen" or has_evidence
        covered += int(is_covered)
        details.append({
            "skill_id": skill_id,
            "stage": stage,
            "mastery_percent": mastery,
            "has_evidence": has_evidence,
            "covered": is_covered,
        })
    percent = round(100 * covered / len(ids), 1) if ids else 0.0
    return {
        "skill_count": len(ids),
        "covered_skill_count": covered,
        "coverage_percent": percent,
        "metric_status": "COVERAGE_NOT_CREDENTIAL_READINESS",
        "skills": details,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="humanos academy")
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--pretty", action="store_true")
    sub = parser.add_subparsers(dest="action", required=True)

    sub.add_parser("courses")

    show_course = sub.add_parser("course")
    show_course.add_argument("course_id")

    sub.add_parser("status")
    sub.add_parser("protocol")
    sub.add_parser("job-packs")

    certs = sub.add_parser("certifications")
    certs.add_argument("course_id")

    select = sub.add_parser("select")
    select.add_argument("course_id")
    select.add_argument("--module-id")
    select.add_argument("--activity-id")
    select.add_argument("--title")

    start = sub.add_parser("start")
    start.add_argument("activity_id")
    start.add_argument("course_id")
    start.add_argument("--module-id")
    start.add_argument("--title")
    start.add_argument("--select", action="store_true", dest="select_focus")

    pause = sub.add_parser("pause")
    pause.add_argument("--reason", default="")

    resume = sub.add_parser("resume")
    resume.add_argument("focus_key")

    complete = sub.add_parser("complete")
    complete.add_argument("activity_id")
    complete.add_argument("--summary", default="")

    stage = sub.add_parser("stage")
    stage.add_argument("skill_id")
    stage.add_argument("stage")
    stage.add_argument("--reason", default="")

    evidence = sub.add_parser("evidence")
    evidence.add_argument("evidence_id")
    evidence.add_argument("skill_id")
    evidence.add_argument("--source", required=True)
    evidence.add_argument("--summary", required=True)
    evidence.add_argument("--course-id")
    evidence.add_argument("--activity-id")
    evidence.add_argument(
        "--score",
        action="append",
        default=[],
        help="dimension=value; repeat for knowledge/practical/diagnostic/communication",
    )

    checkpoint = sub.add_parser("checkpoint")
    checkpoint.add_argument("label")
    checkpoint.add_argument("--note", default="")
    return parser


def _parse_scores(values: Iterable[str]) -> Dict[str, float]:
    scores: Dict[str, float] = {}
    for item in values:
        if "=" not in item:
            raise ValueError("score must use dimension=value")
        key, value = item.split("=", 1)
        key = key.strip()
        if key in scores:
            raise ValueError(f"duplicate score dimension: {key}")
        scores[key] = float(value)
    return scores


def _validate_focus(package, course_id: str, module_id: Optional[str]) -> None:
    course = package.get_course(course_id)
    if course is None:
        raise KeyError(f"unknown course: {course_id}")
    if module_id is not None and module_id not in {module.module_id for module in course.modules}:
        raise KeyError(f"unknown module in {course_id}: {module_id}")


def _validate_skill(package, skill_id: str, course_id: Optional[str] = None) -> None:
    if package.get_skill(skill_id) is None:
        raise KeyError(f"unknown skill: {skill_id}")
    if course_id is None:
        return
    course = package.get_course(course_id)
    if course is None:
        raise KeyError(f"unknown course: {course_id}")
    if skill_id not in course.skill_ids:
        raise ValueError(f"skill {skill_id} is not part of course {course_id}")


def main(argv=None) -> None:
    parser = _parser()
    args = parser.parse_args(argv)
    package = None
    package_actions = {
        "courses", "course", "certifications", "job-packs", "select", "start", "stage", "evidence"
    }
    if args.action in package_actions:
        package = load_package(args.package)

    try:
        if args.action == "courses":
            result = {
                "package": {"package_id": package.package_id, "title": package.title, "version": package.version},
                "courses": [
                    {
                        "course_id": course.course_id,
                        "title": course.title,
                        "module_count": len(course.modules),
                        "skill_count": len(course.skill_ids),
                        "lab_count": len(course.labs),
                        "certification_overlay_count": len(course.certifications),
                    }
                    for course in package.courses.values()
                ],
            }
        elif args.action == "course":
            course = package.get_course(args.course_id)
            if course is None:
                raise KeyError(f"unknown course: {args.course_id}")
            result = {
                "course_id": course.course_id,
                "title": course.title,
                "description": course.description,
                "modules": [
                    {"module_id": module.module_id, "title": module.title, "skill_ids": list(module.skill_ids)}
                    for module in course.modules
                ],
                "labs": [
                    {
                        "lab_id": lab.lab_id,
                        "title": lab.title,
                        "skill_ids": list(lab.skill_ids),
                        "estimated_minutes": lab.estimated_minutes,
                    }
                    for lab in course.labs
                ],
                "certifications": [
                    {
                        "certification_id": cert.certification_id,
                        "title": cert.title,
                        "branch": cert.branch,
                        "skill_ids": list(cert.skill_ids),
                    }
                    for cert in course.certifications
                ],
            }
        elif args.action == "protocol":
            protocol = load_default_teaching_protocol()
            result = {
                "protocol_id": protocol.protocol_id,
                "title": protocol.title,
                "stages": list(protocol.stages),
                "invariants": list(protocol.invariants),
                "roles": list(protocol.roles),
                "grading": protocol.grading,
            }
        else:
            with AcademyStore(args.db) as store:
                if args.action == "status":
                    result = store.rebuild_state()
                elif args.action == "select":
                    _validate_focus(package, args.course_id, args.module_id)
                    event_id = store.select_focus(
                        args.course_id,
                        module_id=args.module_id,
                        activity_id=args.activity_id,
                        title=args.title,
                    )
                    result = {"event_id": event_id, "state": store.rebuild_state()}
                elif args.action == "start":
                    _validate_focus(package, args.course_id, args.module_id)
                    event_id = store.start_activity(
                        args.activity_id,
                        args.course_id,
                        module_id=args.module_id,
                        title=args.title,
                    )
                    selected_event_id = None
                    if args.select_focus:
                        selected_event_id = store.select_focus(
                            args.course_id,
                            module_id=args.module_id,
                            activity_id=args.activity_id,
                            title=args.title,
                        )
                    result = {
                        "event_id": event_id,
                        "selected_event_id": selected_event_id,
                        "state": store.rebuild_state(),
                    }
                elif args.action == "pause":
                    event_id = store.pause_focus(args.reason)
                    result = {"event_id": event_id, "state": store.rebuild_state()}
                elif args.action == "resume":
                    event_id = store.resume_focus(args.focus_key)
                    result = {"event_id": event_id, "state": store.rebuild_state()}
                elif args.action == "complete":
                    event_id = store.complete_activity(args.activity_id, summary=args.summary)
                    result = {"event_id": event_id, "state": store.rebuild_state()}
                elif args.action == "stage":
                    _validate_skill(package, args.skill_id)
                    event_id = store.set_skill_stage(args.skill_id, args.stage, reason=args.reason)
                    result = {"event_id": event_id, "state": store.rebuild_state()}
                elif args.action == "evidence":
                    _validate_skill(package, args.skill_id, args.course_id)
                    event_id = store.record_evidence(
                        args.evidence_id,
                        args.skill_id,
                        _parse_scores(args.score),
                        source=args.source,
                        summary=args.summary,
                        course_id=args.course_id,
                        activity_id=args.activity_id,
                    )
                    result = {"event_id": event_id, "state": store.rebuild_state()}
                elif args.action == "checkpoint":
                    event_id = store.checkpoint(args.label, note=args.note)
                    result = {"event_id": event_id, "state": store.rebuild_state()}
                elif args.action == "certifications":
                    course = package.get_course(args.course_id)
                    if course is None:
                        raise KeyError(f"unknown course: {args.course_id}")
                    state = store.rebuild_state()
                    result = {
                        "course_id": course.course_id,
                        "certifications": [
                            {
                                "certification_id": cert.certification_id,
                                "title": cert.title,
                                "branch": cert.branch,
                                "coverage": _coverage(cert.skill_ids, state),
                                "objectives": [
                                    {
                                        "objective_id": objective.objective_id,
                                        "title": objective.title,
                                        "skill_ids": list(objective.skill_ids),
                                    }
                                    for objective in cert.objectives
                                ],
                            }
                            for cert in course.certifications
                        ],
                    }
                elif args.action == "job-packs":
                    state = store.rebuild_state()
                    result = {
                        "job_packs": [
                            {
                                "job_pack_id": job_pack.job_pack_id,
                                "title": job_pack.title,
                                "coverage": _coverage(job_pack.skill_ids, state),
                                "requirements": [
                                    {
                                        "requirement_id": requirement.requirement_id,
                                        "title": requirement.title,
                                        "skill_ids": list(requirement.skill_ids),
                                        "employer_specific": requirement.employer_specific,
                                    }
                                    for requirement in job_pack.requirements
                                ],
                            }
                            for job_pack in package.job_packs.values()
                        ]
                    }
                else:
                    parser.error(f"unsupported Academy action: {args.action}")
    except (KeyError, ValueError) as exc:
        parser.error(str(exc))
        return
    _emit(result, args.pretty)


if __name__ == "__main__":
    main()
