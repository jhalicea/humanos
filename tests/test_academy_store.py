import sqlite3
import unittest

from learning.academy_store import AcademyStore


class AcademyStoreTests(unittest.TestCase):
    def test_unfinished_activity_is_not_current_without_explicit_selection(self) -> None:
        with self.subTest("start does not imply current focus"):
            from tempfile import TemporaryDirectory
            from pathlib import Path
            with TemporaryDirectory() as tmp:
                db = Path(tmp) / "academy.sqlite3"
                with AcademyStore(db) as store:
                    store.start_activity("lab-1", "course-1", module_id="module-1", title="Lab One")
                    state = store.rebuild_state()
                    self.assertIsNone(state["current_focus"])
                    self.assertIn("lab-1", state["unfinished"])
                    self.assertFalse(state["policy"]["unfinished_is_current"])

    def test_select_pause_reopen_and_resume_preserve_explicit_focus(self) -> None:
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "academy.sqlite3"
            with AcademyStore(db) as store:
                store.start_activity("lab-1", "course-1", module_id="module-1", title="Lab One")
                store.select_focus("course-1", module_id="module-1", activity_id="lab-1", title="Lab One")
                selected = store.rebuild_state()
                self.assertEqual(selected["current_focus"]["activity_id"], "lab-1")
                store.pause_focus("switching topics")
                paused = store.rebuild_state()
                self.assertIsNone(paused["current_focus"])
                self.assertIn("lab-1", paused["unfinished"])
                self.assertIn("activity:lab-1", paused["paused_focuses"])

            with AcademyStore(db) as reopened:
                state = reopened.rebuild_state()
                self.assertIsNone(state["current_focus"])
                self.assertIn("lab-1", state["unfinished"])
                reopened.resume_focus("activity:lab-1")
                resumed = reopened.rebuild_state()
                self.assertEqual(resumed["current_focus"]["activity_id"], "lab-1")

    def test_completion_clears_matching_current_focus_and_unfinished_activity(self) -> None:
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "academy.sqlite3"
            with AcademyStore(db) as store:
                store.start_activity("lab-1", "course-1")
                store.select_focus("course-1", activity_id="lab-1")
                store.complete_activity("lab-1", summary="done")
                state = store.rebuild_state()
                self.assertIsNone(state["current_focus"])
                self.assertNotIn("lab-1", state["unfinished"])

    def test_completion_of_unknown_activity_fails_closed(self) -> None:
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "academy.sqlite3"
            with AcademyStore(db) as store:
                with self.assertRaisesRegex(KeyError, "not unfinished"):
                    store.complete_activity("missing")

    def test_evidence_rebuilds_scores_without_auto_promoting_stage(self) -> None:
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "academy.sqlite3"
            with AcademyStore(db) as store:
                store.record_evidence(
                    "ev-1",
                    "skill-1",
                    {"knowledge": 4, "practical": 4, "diagnostic": 4, "communication": 4},
                    source="synthetic-test",
                    summary="synthetic evidence",
                    created_at="2000-01-01T00:00:00+00:00",
                )
                state = store.rebuild_state()
                self.assertEqual(state["skills"]["skill-1"]["mastery_percent"], 80.0)
                self.assertEqual(state["skills"]["skill-1"]["stage"], "unseen")
                self.assertEqual(state["skills"]["skill-1"]["evidence_count"], 1)

    def test_explicit_stage_event_survives_rebuild(self) -> None:
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "academy.sqlite3"
            with AcademyStore(db) as store:
                store.set_skill_stage("skill-1", "practiced", reason="verified synthetic exercise")
                self.assertEqual(store.rebuild_state()["skills"]["skill-1"]["stage"], "practiced")

    def test_event_rows_are_append_only_at_database_boundary(self) -> None:
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "academy.sqlite3"
            with AcademyStore(db) as store:
                store.checkpoint("one")
                with self.assertRaises(sqlite3.DatabaseError):
                    store.connection.execute("UPDATE academy_events SET event_type='FOCUS_SELECTED'")
                with self.assertRaises(sqlite3.DatabaseError):
                    store.connection.execute("DELETE FROM academy_events")

    def test_evidence_id_is_idempotent_when_same_event_is_retried(self) -> None:
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "academy.sqlite3"
            with AcademyStore(db) as store:
                kwargs = dict(
                    evidence_id="ev-1",
                    skill_id="skill-1",
                    scores={"knowledge": 3},
                    source="synthetic-test",
                    summary="same",
                    created_at="2000-01-01T00:00:00+00:00",
                )
                first = store.record_evidence(**kwargs)
                second = store.record_evidence(**kwargs)
                self.assertEqual(first, second)
                self.assertEqual(store.rebuild_state()["event_count"], 1)

    def test_evidence_retry_without_repeated_timestamp_is_idempotent(self) -> None:
        from tempfile import TemporaryDirectory
        from pathlib import Path
        with TemporaryDirectory() as tmp:
            db = Path(tmp) / "academy.sqlite3"
            with AcademyStore(db) as store:
                kwargs = dict(
                    evidence_id="ev-no-time",
                    skill_id="skill-1",
                    scores={"diagnostic": 4},
                    source="synthetic-test",
                    summary="same semantic retry",
                )
                first = store.record_evidence(**kwargs)
                second = store.record_evidence(**kwargs)
                self.assertEqual(first, second)
                self.assertEqual(store.rebuild_state()["event_count"], 1)


if __name__ == "__main__":
    unittest.main()
