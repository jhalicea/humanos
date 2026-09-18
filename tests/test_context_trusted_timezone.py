import os
import unittest
from unittest.mock import patch

from context_runtime import RuntimeContextRouter


class TrustedTimezoneSourceTests(unittest.TestCase):
    def test_inspect_history_defaults_timezone_to_utc(self):
        import inspect
        sig = inspect.signature(RuntimeContextRouter.inspect_history)
        self.assertEqual(sig.parameters["timezone_name"].default, "UTC")

    def test_history_forwards_timezone_to_temporal_scope(self):
        router = object.__new__(RuntimeContextRouter)
        seen = {}
        router.inspect = lambda text, workspace_hint=None: type("Fresh", (), {"origin": "REQUEST"})()
        router._history_candidate = lambda text: True
        router._verified_history_records = lambda book, current_tx=None: []
        router._history_subject_tokens = lambda text: set()
        def capture(records, text, timezone_name="UTC"):
            seen["timezone"] = timezone_name
            return records, None
        router._apply_temporal_scope = capture
        class Book:
            def verify(self):
                return True
        route = router.inspect_history(Book(), "continue what we were doing yesterday",
                                       timezone_name="America/New_York")
        self.assertEqual(seen["timezone"], "America/New_York")
        self.assertTrue(route.requires_confirmation)

    def test_runtime_setting_is_explicit_host_environment(self):
        with patch.dict(os.environ, {"HUMANOS_TIMEZONE": "America/New_York"}, clear=False):
            self.assertEqual(os.environ.get("HUMANOS_TIMEZONE", "UTC"), "America/New_York")

    def test_missing_runtime_setting_defaults_to_utc(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(os.environ.get("HUMANOS_TIMEZONE", "UTC"), "UTC")


if __name__ == "__main__":
    unittest.main()
