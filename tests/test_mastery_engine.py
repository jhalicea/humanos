"""Behavioral tests using synthetic public learning fixtures only."""

import unittest
from datetime import datetime, timedelta, timezone

from learning import Course, Evidence, MasteryEngine, Skill, seed
from learning.catalog import get_course, load_catalog


FOUNDATION = "sample-skill-foundations"
THREAT_MODELING = "sample-skill-threat-modeling"
SECURITY_LAB = "sample-security-lab"


def evidence(evidence_id: str, skill_id: str, score: float, *, created_at: str) -> Evidence:
    return Evidence(
        evidence_id=evidence_id,
        skill_id=skill_id,
        source="synthetic-test-fixture",
        summary="Synthetic behavioral test evidence",
        scores={
            "knowledge": score,
            "practical": score,
            "diagnostic": score,
            "communication": score,
        },
        created_at=created_at,
    )


class MasteryEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = load_catalog()
        self.now = "2000-01-01T00:00:00+00:00"

    def test_seed_preserves_synthetic_catalog_api(self) -> None:
        self.assertEqual(
            set(self.engine.courses),
            {"sample-security-lab", "sample-automation-workflow"},
        )
        self.assertEqual(set(self.engine.skills), {
            "sample-skill-foundations",
            "sample-skill-threat-modeling",
            "sample-skill-automation",
        })
        self.assertIn(FOUNDATION, self.engine.courses[SECURITY_LAB].skill_ids)
        self.assertIs(self.engine, seed(self.engine))

    def test_catalog_instances_do_not_share_mutable_learner_state(self) -> None:
        second = load_catalog()
        self.engine.encounter(FOUNDATION)
        self.assertEqual(self.engine.skills[FOUNDATION].stage, "introduced")
        self.assertEqual(second.skills[FOUNDATION].stage, "unseen")

    def test_course_lookup_returns_none_for_unknown_identifier(self) -> None:
        self.assertEqual(get_course(self.engine, SECURITY_LAB).course_id, SECURITY_LAB)
        self.assertIsNone(get_course(self.engine, "private-course-unavailable"))

    def test_overlapping_courses_are_supported(self) -> None:
        self.assertIn(FOUNDATION, self.engine.courses["sample-security-lab"].skill_ids)
        self.assertIn(FOUNDATION, self.engine.courses["sample-automation-workflow"].skill_ids)

    def test_evidence_updates_derived_mastery(self) -> None:
        before = self.engine.skills[FOUNDATION].mastery_percent
        self.engine.record_evidence(evidence("synthetic-evidence-1", FOUNDATION, 4, created_at=self.now))
        self.assertGreater(self.engine.skills[FOUNDATION].mastery_percent, before)
        self.assertEqual(self.engine.skills[FOUNDATION].mastery_percent, 80.0)

    def test_new_contradictory_evidence_can_reduce_derived_mastery(self) -> None:
        self.engine.record_evidence(evidence("synthetic-evidence-1", FOUNDATION, 5, created_at=self.now))
        high = self.engine.skills[FOUNDATION].mastery_percent
        self.engine.record_evidence(evidence("synthetic-evidence-2", FOUNDATION, 1, created_at=self.now))
        self.assertLess(self.engine.skills[FOUNDATION].mastery_percent, high)

    def test_duplicate_evidence_is_idempotent_and_conflicting_id_is_rejected(self) -> None:
        item = evidence("synthetic-evidence-1", FOUNDATION, 4, created_at=self.now)
        self.engine.record_evidence(item)
        self.engine.record_evidence(item)
        self.assertEqual(len(self.engine.skills[FOUNDATION].evidence_ids), 1)
        conflict = evidence("synthetic-evidence-1", FOUNDATION, 2, created_at=self.now)
        with self.assertRaises(ValueError):
            self.engine.record_evidence(conflict)

    def test_curriculum_research_remains_a_candidate(self) -> None:
        candidate = self.engine.propose_curriculum_update(
            "Synthetic proposal", "Synthetic rationale", ["synthetic-source"]
        )
        self.assertEqual(candidate["status"], "candidate")
        self.assertEqual(len(self.engine.curriculum_candidates), 1)

    def test_invalid_score_is_rejected(self) -> None:
        item = Evidence("synthetic-evidence", FOUNDATION, "fixture", "fixture", {"knowledge": 6})
        with self.assertRaises(ValueError):
            self.engine.record_evidence(item)

    def test_unknown_skill_is_rejected(self) -> None:
        item = evidence("synthetic-evidence", "sample-skill-unavailable", 3, created_at=self.now)
        with self.assertRaises(KeyError):
            self.engine.record_evidence(item)

    def test_naive_and_future_timestamps_are_rejected(self) -> None:
        naive = evidence("synthetic-naive", FOUNDATION, 3, created_at="2000-01-01T00:00:00")
        future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        future_item = evidence("synthetic-future", FOUNDATION, 3, created_at=future)
        with self.assertRaises(ValueError):
            self.engine.record_evidence(naive)
        with self.assertRaises(ValueError):
            self.engine.record_evidence(future_item)

    def test_course_rejects_unknown_skill_reference(self) -> None:
        with self.assertRaises(ValueError):
            self.engine.add_course(Course("sample-invalid-course", "Synthetic", ["sample-skill-unavailable"]))

    def test_empty_course_metrics_are_defined(self) -> None:
        self.engine.add_course(Course("sample-empty-course", "Synthetic Empty Course", []))
        self.assertEqual(self.engine.course_mastery_percent("sample-empty-course"), 0.0)
        self.assertEqual(self.engine.course_completion_percent("sample-empty-course"), 0.0)

    def test_snapshot_marks_metrics_as_evidence_estimates(self) -> None:
        course = self.engine.snapshot()["courses"][SECURITY_LAB]
        self.assertEqual(course["metric_status"], "ESTIMATED_FROM_RECORDED_EVIDENCE")
        self.assertEqual(course["evidence_count"], 0)

    def test_gap_reasons_are_inspectable(self) -> None:
        reasons = self.engine.gap_reasons(SECURITY_LAB)
        self.assertTrue(reasons)
        self.assertEqual(reasons[0]["skill_id"], THREAT_MODELING)
        self.assertIn("priority relative to current evidence-derived mastery", reasons[0]["reason"])

    def test_completion_and_mastery_are_distinct(self) -> None:
        self.engine.encounter(FOUNDATION)
        self.assertEqual(self.engine.course_completion_percent(SECURITY_LAB), 50.0)
        self.assertNotEqual(
            self.engine.course_completion_percent(SECURITY_LAB),
            self.engine.course_mastery_percent(SECURITY_LAB),
        )

    def test_course_defaults_contain_no_owner_specific_readiness(self) -> None:
        self.assertIsNone(self.engine.courses[SECURITY_LAB].career_readiness_percent)


if __name__ == "__main__":
    unittest.main()
