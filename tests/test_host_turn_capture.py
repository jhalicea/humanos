import tempfile
import unittest
from pathlib import Path

from host_turn_capture import capture_host_turn
from notebook import Notebook
from conversation_ledger import read_ledger


class HostTurnCaptureTests(unittest.TestCase):
    def test_both_surfaces_are_exact_and_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            book = Notebook(root / "vault")
            book.recover()
            binding = book.bind("owner", "test")
            try:
                first = capture_host_turn(book, root / "turns.jsonl", binding["hcid"],
                                          "chatgpt", "c1", "t1", " hello ", " world ")
                second = capture_host_turn(book, root / "turns.jsonl", binding["hcid"],
                                           "chatgpt", "c1", "t1", " hello ", " world ")
                self.assertEqual(first["verification"]["status"], "CHECKPOINTED")
                self.assertEqual(second["added"], 0)
                self.assertEqual([r["text"] for r in read_ledger(root / "turns.jsonl")],
                                 [" hello ", " world "])
                self.assertTrue(book.verify())
            finally:
                book.close()


if __name__ == "__main__":
    unittest.main()
