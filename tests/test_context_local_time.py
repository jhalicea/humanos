import unittest
from datetime import datetime, timezone

from context_runtime import RuntimeContextRouter


class LocalTemporalContextTests(unittest.TestCase):
    def setUp(self):
        self.router = object.__new__(RuntimeContextRouter)

    def test_record_date_changes_at_timezone_boundary(self):
        item = {
            "created_at": "2026-09-18T02:30:00+00:00",
            "created_date": "2026-09-18",
        }
        self.assertEqual(self.router._record_local_date(item, timezone.utc), "2026-09-18")
        from zoneinfo import ZoneInfo
        self.assertEqual(self.router._record_local_date(item, ZoneInfo("America/New_York")), "2026-09-17")

    def test_invalid_timezone_fails_safely_to_utc(self):
        records = [{
            "source_tx": "host-only",
            "workspace_id": "WS-HUMANOS",
            "workstream_id": "HOS-CTX-005",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_date": datetime.now(timezone.utc).date().isoformat(),
        }]
        scoped, reason = self.router._apply_temporal_scope(records, "continue earlier today", "Not/A_Real_Zone")
        self.assertEqual(scoped, records)
        self.assertIn("UTC", reason)
        self.assertNotIn("Not/A_Real_Zone", reason)

    def test_default_remains_utc_for_backward_compatibility(self):
        records = [{
            "source_tx": "host-only",
            "workspace_id": "WS-HUMANOS",
            "workstream_id": "HOS-CTX-005",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_date": datetime.now(timezone.utc).date().isoformat(),
        }]
        scoped, _ = self.router._apply_temporal_scope(records, "continue earlier today")
        self.assertEqual(scoped, records)


if __name__ == "__main__":
    unittest.main()
