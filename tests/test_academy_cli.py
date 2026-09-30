import json
from pathlib import Path

import pytest

from humanos import main as humanos_main
from learning.academy_cli import main as academy_main


FIXTURE = Path(__file__).resolve().parents[1] / "examples" / "academy" / "synthetic-academy-v1.json"


def _read_json(capsys):
    return json.loads(capsys.readouterr().out)


def test_courses_lists_synthetic_public_package(tmp_path, capsys):
    academy_main(["--package", str(FIXTURE), "--db", str(tmp_path / "academy.db"), "courses"])
    result = _read_json(capsys)
    assert result["package"]["package_id"] == "synthetic-public-academy"
    assert {item["course_id"] for item in result["courses"]} == {
        "sample-security-course",
        "sample-automation-course",
    }


def test_root_humanos_command_delegates_to_academy(tmp_path, capsys):
    humanos_main([
        "academy",
        "--package", str(FIXTURE),
        "--db", str(tmp_path / "academy.db"),
        "courses",
    ])
    result = _read_json(capsys)
    assert result["package"]["title"] == "Synthetic Public Academy Fixture"


def test_start_does_not_select_until_human_explicitly_selects(tmp_path, capsys):
    db = tmp_path / "academy.db"
    base = ["--package", str(FIXTURE), "--db", str(db)]

    academy_main(base + ["start", "sample-evidence-lab", "sample-security-course",
                         "--module-id", "sample-security-foundations"])
    started = _read_json(capsys)
    assert started["state"]["current_focus"] is None
    assert "sample-evidence-lab" in started["state"]["unfinished"]

    academy_main(base + ["select", "sample-security-course",
                         "--module-id", "sample-security-foundations",
                         "--activity-id", "sample-evidence-lab"])
    selected = _read_json(capsys)
    assert selected["state"]["current_focus"]["activity_id"] == "sample-evidence-lab"

    academy_main(base + ["pause", "--reason", "human chose another topic"])
    paused = _read_json(capsys)
    assert paused["state"]["current_focus"] is None
    assert "sample-evidence-lab" in paused["state"]["unfinished"]

    academy_main(base + ["status"])
    reopened = _read_json(capsys)
    assert reopened["current_focus"] is None
    assert "activity:sample-evidence-lab" in reopened["paused_focuses"]

    academy_main(base + ["resume", "activity:sample-evidence-lab"])
    resumed = _read_json(capsys)
    assert resumed["state"]["current_focus"]["activity_id"] == "sample-evidence-lab"


def test_certification_coverage_is_not_credential_readiness(tmp_path, capsys):
    db = tmp_path / "academy.db"
    base = ["--package", str(FIXTURE), "--db", str(db)]

    academy_main(base + ["stage", "sample.security.evidence", "practiced",
                         "--reason", "synthetic test"])
    _read_json(capsys)
    academy_main(base + ["certifications", "sample-security-course"])
    result = _read_json(capsys)
    coverage = result["certifications"][0]["coverage"]
    assert coverage["coverage_percent"] == 100.0
    assert coverage["metric_status"] == "COVERAGE_NOT_CREDENTIAL_READINESS"


def test_job_pack_reuses_skill_state(tmp_path, capsys):
    db = tmp_path / "academy.db"
    base = ["--package", str(FIXTURE), "--db", str(db)]

    academy_main(base + ["evidence", "ev-automation", "sample.automation.reliability",
                         "--source", "synthetic-cli-test", "--summary", "synthetic",
                         "--score", "knowledge=4", "--score", "practical=4"])
    _read_json(capsys)
    academy_main(base + ["job-packs"])
    result = _read_json(capsys)
    pack = result["job_packs"][0]
    assert pack["job_pack_id"] == "sample-solutions-role"
    assert pack["coverage"]["covered_skill_count"] == 1
    assert pack["coverage"]["metric_status"] == "COVERAGE_NOT_CREDENTIAL_READINESS"


def test_protocol_exposed_through_cli(tmp_path, capsys):
    academy_main(["--package", str(FIXTURE), "--db", str(tmp_path / "academy.db"), "protocol"])
    result = _read_json(capsys)
    assert result["stages"][0] == "MAP"
    assert "AI_MUST_NOT_DO_TARGET_COGNITIVE_WORK" in result["invariants"]


def test_unknown_course_fails_closed(tmp_path, capsys):
    with pytest.raises(SystemExit):
        academy_main([
            "--package", str(FIXTURE),
            "--db", str(tmp_path / "academy.db"),
            "select", "missing-course",
        ])
    assert "unknown course" in capsys.readouterr().err
