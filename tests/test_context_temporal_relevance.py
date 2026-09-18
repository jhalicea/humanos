import unittest
from datetime import datetime, timedelta, timezone

from context_runtime import RuntimeContextRouter


class TemporalContextTests(unittest.TestCase):
    def setUp(self):
        self.router = object.__new__(RuntimeContextRouter)

    def _record(self, when, workstream):
        return {
            "source_tx": "internal-" + workstream,
            "workspace_id": "WS-HUMANOS",
            "workstream_id": workstream,
            "created_date": when.date().isoformat(),
            "created_at": when.isoformat(),
        }

    def test_yesterday_is_calendar_scoped(self):
        now = datetime.now(timezone.utc)
        records = [
            self._record(now, "TODAY"),
            self._record(now - timedelta(days=1), "YESTERDAY"),
            self._record(now - timedelta(days=2), "OLDER"),
        ]
        scoped, reason = self.router._apply_temporal_scope(records, "continue what we were doing yesterday")
        self.assertEqual([x["workstream_id"] for x in scoped], ["YESTERDAY"])
        self.assertIn("yesterday", reason)

    def test_today_is_calendar_scoped(self):
        now = datetime.now(timezone.utc)
        records = [self._record(now, "TODAY"), self._record(now - timedelta(days=1), "OLD")]
        scoped, reason = self.router._apply_temporal_scope(records, "resume the work from earlier today")
        self.assertEqual([x["workstream_id"] for x in scoped], ["TODAY"])
        self.assertIn("today", reason)

    def test_last_week_uses_previous_monday_to_monday_window(self):
        now = datetime.now(timezone.utc)
        this_monday = now.date() - timedelta(days=now.weekday())
        last_week_day = datetime.combine(this_monday - timedelta(days=3), datetime.min.time(), tzinfo=timezone.utc)
        current_week_day = datetime.combine(this_monday, datetime.min.time(), tzinfo=timezone.utc)
        records = [self._record(current_week_day, "CURRENT"), self._record(last_week_day, "LAST")]
        scoped, reason = self.router._apply_temporal_scope(records, "continue the work from last week")
        self.assertEqual([x["workstream_id"] for x in scoped], ["LAST"])
        self.assertIn("last week", reason)

    def test_most_recent_uses_verified_history_order(self):
        now = datetime.now(timezone.utc)
        records = [self._record(now, "NEWEST"), self._record(now - timedelta(hours=1), "OLDER")]
        scoped, reason = self.router._apply_temporal_scope(records, "continue the most recent work")
        self.assertEqual([x["workstream_id"] for x in scoped], ["NEWEST"])
        self.assertIn("most recent", reason)

    def test_no_temporal_language_preserves_candidates(self):
        now = datetime.now(timezone.utc)
        records = [self._record(now, "ONE"), self._record(now - timedelta(days=4), "TWO")]
        scoped, reason = self.router._apply_temporal_scope(records, "continue the earlier work")
        self.assertEqual(scoped, records)
        self.assertIsNone(reason)


if __name__ == "__main__":
    unittest.main()
