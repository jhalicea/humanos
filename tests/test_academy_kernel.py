import copy
import json
import unittest
from pathlib import Path

from learning.academy_loader import load_package, parse_package
from learning.teaching_protocol import REQUIRED_INVARIANT, load_default_teaching_protocol


FIXTURE = Path(__file__).resolve().parents[1] / "examples" / "academy" / "synthetic-academy-v1.json"


class AcademyKernelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.package = load_package(FIXTURE)
        self.raw = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_loads_shared_skill_graph_and_courses(self) -> None:
        self.assertEqual(self.package.schema, "humanos.academy.package.v1")
        self.assertIn("sample.foundation", self.package.skills)
        self.assertEqual(len(self.package.courses), 2)
        self.assertIn("sample.foundation", self.package.courses["sample-security-course"].skill_ids)
        self.assertIn("sample.foundation", self.package.courses["sample-automation-course"].skill_ids)

    def test_certification_is_overlay_inside_parent_course(self) -> None:
        course = self.package.courses["sample-security-course"]
        self.assertEqual(len(course.certifications), 1)
        overlay = course.certifications[0]
        self.assertEqual(overlay.certification_id, "sample-security-cert")
        self.assertNotIn(overlay.certification_id, self.package.courses)
        self.assertEqual(overlay.skill_ids, ("sample.security.evidence",))

    def test_labs_live_inside_parent_course_and_reference_course_skills(self) -> None:
        course = self.package.courses["sample-security-course"]
        self.assertEqual(course.labs[0].lab_id, "sample-evidence-lab")
        self.assertTrue(set(course.labs[0].skill_ids).issubset(set(course.skill_ids)))

    def test_job_pack_maps_requirements_to_existing_skills(self) -> None:
        pack = self.package.job_packs["sample-solutions-role"]
        self.assertIn("sample.automation.reliability", pack.skill_ids)
        self.assertTrue(any(item.employer_specific for item in pack.requirements))

    def test_rejects_unknown_skill_reference(self) -> None:
        raw = copy.deepcopy(self.raw)
        raw["courses"][0]["modules"][0]["skill_ids"].append("missing.skill")
        with self.assertRaisesRegex(ValueError, "unknown skills"):
            parse_package(raw)

    def test_rejects_lab_skill_outside_parent_course(self) -> None:
        raw = copy.deepcopy(self.raw)
        raw["courses"][0]["labs"][0]["skill_ids"].append("sample.automation.reliability")
        with self.assertRaisesRegex(ValueError, "outside parent course"):
            parse_package(raw)

    def test_rejects_certification_skill_outside_parent_course(self) -> None:
        raw = copy.deepcopy(self.raw)
        raw["courses"][0]["certifications"][0]["objectives"][0]["skill_ids"].append(
            "sample.automation.reliability"
        )
        with self.assertRaisesRegex(ValueError, "outside parent course"):
            parse_package(raw)

    def test_rejects_unknown_schema(self) -> None:
        raw = copy.deepcopy(self.raw)
        raw["schema"] = "humanos.academy.package.v999"
        with self.assertRaisesRegex(ValueError, "unsupported Academy package schema"):
            parse_package(raw)

    def test_teaching_protocol_preserves_cognitive_work_invariant_and_weights(self) -> None:
        protocol = load_default_teaching_protocol()
        self.assertIn(REQUIRED_INVARIANT, protocol.invariants)
        self.assertLess(protocol.stage_index("ASK_FIRST"), protocol.stage_index("TEACH_SMALLEST_USEFUL_CONCEPT"))
        self.assertLess(protocol.stage_index("BREAK"), protocol.stage_index("DIAGNOSE"))
        self.assertAlmostEqual(sum(protocol.grading.values()), 1.0)
        self.assertEqual(protocol.grading["knowledge"], 0.25)
        self.assertEqual(protocol.grading["practical"], 0.30)
        self.assertEqual(protocol.grading["diagnostic"], 0.25)
        self.assertEqual(protocol.grading["communication"], 0.20)


if __name__ == "__main__":
    unittest.main()
