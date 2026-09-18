import os
import unittest
from unittest.mock import patch

from context_runtime import RuntimeContextRouter


class TrustedTimezoneSourceTests(unittest.TestCase):
    def test_inspect_history_defaults_timezone_to_utc(self):
        import inspect
        sig = inspect.signature(RuntimeContextRouter.inspect_history)
        self.assertEqual(sig.parameters["timezone_name"].default, "UTC")

    def test_runtime_setting_is_explicit_host_environment(self):
        with patch.dict(os.environ, {"HUMANOS_TIMEZONE": "America/New_York"}, clear=False):
            self.assertEqual(os.environ.get("HUMANOS_TIMEZONE", "UTC"), "America/New_York")

    def test_missing_runtime_setting_defaults_to_utc(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(os.environ.get("HUMANOS_TIMEZONE", "UTC"), "UTC")


if __name__ == "__main__":
    unittest.main()
