import unittest

from runtime_info import intent, request_for


class IntentRoutingRegressionTests(unittest.TestCase):
    def test_long_task_mentioning_notebook_is_not_hijacked(self):
        text = (
            "HUMANOS JOB HOS-R1-LOCAL-001-A3. This is a clean benchmark turn. "
            "Do not use read_notebook or prior conversation history. "
            "Audit current local HumanOS features and report evidence."
        )
        self.assertIsNone(intent(text))
        self.assertIsNone(request_for(text, []))


if __name__ == "__main__":
    unittest.main()
