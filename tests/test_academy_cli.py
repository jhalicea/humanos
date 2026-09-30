import io
import json
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory

from humanos import main as humanos_main
from learning.academy_cli import main as academy_main


FIXTURE = Path(__file__).resolve().parents[1] / "examples" / "academy" / "synthetic-academy-v1.json"


class AcademyCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "academy.db"
        self.base = ["--package", str(FIXTURE), "--db", str(self.db)]

    def run_cli(self, args, *, root=False):
        output = io.StringIO()
        runner = humanos_main if root else academy_main
        call_args = (["academy"] + args) if root else args
        with redirect_stdout(output):
            runner(call_args)
        return json.loads(output.getvalue())

    def test_courses_lists_synthetic_public_package(self) -> None:
        result = self.run_cli(self.base + ["courses"])
        self.assertEqual(result["package"]["package_id"], "synthetic-public-academy")
        self.assertEqual(
            {item["course_id"] for item in result["courses"]},
            {"sample-security-course", "sample-automation-course"},
        )

    def test_root_humanos_command_delegates_to_academy(self) -> None:
        result = self.run_cli(self.base + ["courses"], root=True)
        self.assertEqual(result["package"]["title"], "Synthetic Public Academy Fixture")

    def test_start_does_not_select_until_human_explicitly_selects(self) -> None:
        started = self.run_cli(self.base + [
            "start", "sample-evidence-lab", "sample-security-course",
            "--module-id", "sample-security-foundations",
        ])
        self.assertIsNone(started["state"]["current_focus"])
        self.assertIn("sample-evidence-lab", started["state"]["unfinished"])

        selected = self.run_cli(self.base + [
            "select", "sample-security-course",
            "--module-id", "sample-security-foundations",
            "--activity-id", "sample-evidence-lab",
        ])
        self.assertEqual(selected["state"]["current_focus"]["activity_id"], "sample-evidence-lab")

        paused = self.run_cli(self.base + ["pause", "--reason", "human chose another topic"])
        self.assertIsNone(paused["state"]["current_focus"])
        self.assertIn("sample-evidence-lab", paused["state"]["unfinished"])

        reopened = self.run_cli(self.base + ["status"])
        self.assertIsNone(reopened["current_focus"])
        self.assertIn("activity:sample-evidence-lab", reopened["paused_focuses"])

        resumed = self.run_cli(self.base + ["resume", "activity:sample-evidence-lab"])
        self.assertEqual(resumed["state"]["current_focus"]["activity_id"], "sample-evidence-lab")

    def test_certification_coverage_is_not_credential_readiness(self) -> None:
        self.run_cli(self.base + [
            "stage", "sample.security.evidence", "practiced", "--reason", "synthetic test",
        ])
        result = self.run_cli(self.base + ["certifications", "sample-security-course"])
        coverage = result["certifications"][0]["coverage"]
        self.assertEqual(coverage["coverage_percent"], 100.0)
        self.assertEqual(coverage["metric_status"], "COVERAGE_NOT_CREDENTIAL_READINESS")

    def test_job_pack_reuses_skill_state(self) -> None:
        self.run_cli(self.base + [
            "evidence", "ev-automation", "sample.automation.reliability",
            "--source", "synthetic-cli-test", "--summary", "synthetic",
            "--score", "knowledge=4", "--score", "practical=4",
        ])
        result = self.run_cli(self.base + ["job-packs"])
        pack = result["job_packs"][0]
        self.assertEqual(pack["job_pack_id"], "sample-solutions-role")
        self.assertEqual(pack["coverage"]["covered_skill_count"], 1)
        self.assertEqual(pack["coverage"]["metric_status"], "COVERAGE_NOT_CREDENTIAL_READINESS")

    def test_protocol_exposed_through_cli(self) -> None:
        result = self.run_cli(self.base + ["protocol"])
        self.assertEqual(result["stages"][0], "MAP")
        self.assertIn("AI_MUST_NOT_DO_TARGET_COGNITIVE_WORK", result["invariants"])

    def test_unknown_course_fails_closed(self) -> None:
        error = io.StringIO()
        with redirect_stderr(error):
            with self.assertRaises(SystemExit):
                academy_main(self.base + ["select", "missing-course"])
        self.assertIn("unknown course", error.getvalue())


if __name__ == "__main__":
    unittest.main()
