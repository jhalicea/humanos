import tempfile
import unittest
from pathlib import Path

from ledger_capture_adapter import capture_observed_turn
from conversation_ledger import read_ledger


class LedgerCaptureAdapterTests(unittest.TestCase):
    def test_observed_turn_is_exact_and_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.jsonl"
            first = capture_observed_turn(ledger, "chatgpt", "conversation-1", "turn-1", "hello", "world")
            second = capture_observed_turn(ledger, "chatgpt", "conversation-1", "turn-1", "hello", "world")
            self.assertEqual(first["added"], 2)
            self.assertEqual(second["added"], 0)
            self.assertEqual([row["role"] for row in read_ledger(ledger)], ["HUMAN", "ASSISTANT"])
            self.assertEqual(first["status"], "CHECKPOINTED")


if __name__ == "__main__":
    unittest.main()
