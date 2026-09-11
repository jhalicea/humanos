import unittest

from learning import Evidence, MasteryEngine, seed

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

    def test_evidence_updates_mastery_without_averaging_away_demonstrated_skill(self):
        self.engine.record_evidence(Evidence("e1", "git", "BodyFix project", "resolved a branch problem", {
            "knowledge": 3, "practical": 4, "diagnostic": 3, "communication": 2
        }))
        self.assertGreater(self.engine.skills["git"].mastery_percent, 0)
        self.assertEqual(self.engine.skills["git"].last_practiced, self.engine.evidence["e1"].created_at)

    def test_research_is_candidate_only(self):
        item = self.engine.propose_curriculum_update("Future topic", "field changed", ["primary-source"])
        self.assertEqual(item["status"], "candidate")

    def test_invalid_score_rejected(self):
        with self.assertRaises(ValueError):
            self.engine.record_evidence(Evidence("e2", "git", "lab", "bad score", {"practical": 6}))

    def test_completion_and_mastery_are_distinct(self):
        self.assertNotEqual(self.engine.course_completion_percent("cybersecurity-dfir"),
                            self.engine.courses["cybersecurity-dfir"].career_readiness_percent)

if __name__ == "__main__":
    unittest.main()
