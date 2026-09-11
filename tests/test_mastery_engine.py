import unittest
from datetime import datetime, timedelta, timezone

from learning import Course, Evidence, MasteryEngine, seed

class MasteryEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = seed(MasteryEngine())

    def test_flagship_courses_preserved(self):
        self.assertIn("cybersecurity-dfir", self.engine.courses)
        self.assertIn("ai-systems", self.engine.courses)
        self.assertEqual(self.engine.courses["cybersecurity-dfir"].career_readiness_percent, 47.0)
        self.assertEqual(self.engine.skills["ai.transformers"].stage, "introduced")

    def test_overlap_is_supported(self):
        self.assertIn("git", self.engine.courses["cybersecurity-dfir"].skill_ids)
        self.assertIn("git", self.engine.courses["ai-systems"].skill_ids)

    def test_evidence_updates_mastery(self):
        self.engine.record_evidence(Evidence("e1", "git", "BodyFix project", "resolved a branch problem", {
            "knowledge": 3, "practical": 4, "diagnostic": 3, "communication": 2
        }))
        self.assertGreater(self.engine.skills["git"].mastery_percent, 0)
        self.assertEqual(self.engine.skills["git"].last_practiced, self.engine.evidence["e1"].created_at)

    def test_contradictory_evidence_can_reduce_mastery(self):
        high = {d: 5 for d in ("knowledge", "practical", "diagnostic", "communication")}
        low = {d: 0 for d in ("knowledge", "practical", "diagnostic", "communication")}
        self.engine.record_evidence(Evidence("high", "git", "assessment", "independent success", high))
        before = self.engine.skills["git"].mastery_percent
        self.engine.record_evidence(Evidence("low", "git", "assessment", "later reproduction failure", low))
        self.assertLess(self.engine.skills["git"].mastery_percent, before)

    def test_duplicate_evidence_is_idempotent_but_collision_rejected(self):
        item = Evidence("same", "git", "lab", "attempt", {"practical": 4})
        self.engine.record_evidence(item)
        self.engine.record_evidence(item)
        self.assertEqual(self.engine.skills["git"].evidence_ids.count("same"), 1)
        with self.assertRaises(ValueError):
            self.engine.record_evidence(Evidence("same", "git", "lab", "different", {"practical": 1}))

    def test_research_is_candidate_only(self):
        item = self.engine.propose_curriculum_update("Future topic", "field changed", ["primary-source"])
        self.assertEqual(item["status"], "candidate")
        self.assertFalse(self.engine.snapshot()["policy"]["curriculum_self_promotion"])

    def test_invalid_score_rejected(self):
        for value in (-1, 6):
            with self.assertRaises(ValueError):
                self.engine.record_evidence(Evidence(f"bad-{value}", "git", "lab", "bad score", {"practical": value}))

    def test_unknown_skill_rejected(self):
        with self.assertRaises(KeyError):
            self.engine.record_evidence(Evidence("e3", "missing", "lab", "unknown", {"practical": 2}))

    def test_future_and_naive_timestamps_rejected(self):
        future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        with self.assertRaises(ValueError):
            self.engine.record_evidence(Evidence("future", "git", "lab", "future", {"practical": 2}, created_at=future))
        with self.assertRaises(ValueError):
            self.engine.record_evidence(Evidence("naive", "git", "lab", "naive", {"practical": 2}, created_at="2026-09-11T12:00:00"))

    def test_course_rejects_unknown_skill_reference(self):
        with self.assertRaises(ValueError):
            self.engine.add_course(Course("bad", "Bad", ["not-real"]))

    def test_empty_course_is_defined(self):
        self.engine.add_course(Course("empty", "Empty", []))
        self.assertEqual(self.engine.course_mastery_percent("empty"), 0.0)
        self.assertEqual(self.engine.course_completion_percent("empty"), 0.0)

    def test_metrics_include_epistemic_context(self):
        course = self.engine.snapshot()["courses"]["ai-systems"]
        self.assertEqual(course["metric_status"], "ESTIMATED_FROM_RECORDED_EVIDENCE")
        self.assertIn("evidence_count", course)

    def test_gap_reason_is_inspectable(self):
        reason = self.engine.gap_reasons("ai-systems", 1)[0]
        self.assertIn("mastery_percent", reason)
        self.assertIn("priority", reason)
        self.assertIn("reason", reason)

    def test_completion_and_mastery_are_distinct(self):
        self.assertNotEqual(self.engine.course_completion_percent("cybersecurity-dfir"),
                            self.engine.courses["cybersecurity-dfir"].career_readiness_percent)

if __name__ == "__main__":
    unittest.main()
