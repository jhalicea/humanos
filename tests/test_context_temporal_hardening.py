import unittest
from types import SimpleNamespace
from datetime import timezone
from zoneinfo import ZoneInfo

from context_runtime import RuntimeContextRouter


class TemporalResolutionHardeningTests(unittest.TestCase):
    def setUp(self):
        self.router = object.__new__(RuntimeContextRouter)

    def test_temporal_phrases_are_historical_candidates(self):
        for text in (
            "continue the work today",
            "continue the most recent work",
            "resume the latest work",
        ):
            with self.subTest(text=text):
                self.assertTrue(self.router._history_candidate(text))

    def test_terminal_newest_record_does_not_hide_newest_eligible_record(self):
        self.router.registry = SimpleNamespace(workstreams={
            "ARCHIVED": SimpleNamespace(workspace_id="WS-HUMANOS", status="ARCHIVED"),
            "ELIGIBLE": SimpleNamespace(workspace_id="WS-HUMANOS", status="PAUSED"),
        })
        records = [
            {
                "source_tx": "tx-archived",
                "workspace_id": "WS-HUMANOS",
                "workstream_id": "ARCHIVED",
                "created_at": "2026-09-18T02:00:00+00:00",
                "created_date": "2026-09-18",
            },
            {
                "source_tx": "tx-eligible",
                "workspace_id": "WS-HUMANOS",
                "workstream_id": "ELIGIBLE",
                "created_at": "2026-09-18T01:00:00+00:00",
                "created_date": "2026-09-18",
            },
        ]
        eligible = self.router._eligible_history_records(records)
        scoped, _ = self.router._apply_temporal_scope(
            eligible, "continue the most recent work", "UTC")
        self.assertEqual([item["workstream_id"] for item in scoped], ["ELIGIBLE"])

    def test_naive_timestamp_falls_back_to_canonical_date(self):
        item = {
            "created_at": "2026-09-18T02:30:00",
            "created_date": "2026-09-18",
        }
        self.assertEqual(
            self.router._record_local_date(item, ZoneInfo("America/New_York")),
            "2026-09-18",
        )
        self.assertEqual(
            self.router._record_local_date(item, timezone.utc),
            "2026-09-18",
        )


if __name__ == "__main__":
    unittest.main()
