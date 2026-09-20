import json
import tempfile
import unittest
from pathlib import Path

from conversation_ledger import import_messages, read_ledger


class ConversationLedgerTests(unittest.TestCase):
    def test_import_is_exact_idempotent_and_reopenable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.jsonl"
            source.write_text("\n".join([
                json.dumps({"timestamp": "2026-09-19T00:00:00Z", "type": "response_item",
                            "payload": {"type": "message", "id": "u1", "role": "user",
                                        "content": [{"type": "input_text", "text": "  hello 🧭  "}]}}),
                json.dumps({"timestamp": "2026-09-19T00:00:01Z", "type": "response_item",
                            "payload": {"type": "message", "id": "a1", "role": "assistant",
                                        "content": [{"type": "output_text", "text": "world"}]}}),
            ]) + "\n", encoding="utf-8")
            ledger = root / "ledger.jsonl"
            self.assertEqual(import_messages(source, ledger), {"added": 2, "total": 2})
            before = ledger.read_bytes()
            self.assertEqual(import_messages(source, ledger), {"added": 0, "total": 2})
            self.assertEqual(ledger.read_bytes(), before)
            reopened = read_ledger(ledger)
            self.assertEqual([row["text"] for row in reopened], ["  hello 🧭  ", "world"])
            self.assertEqual([row["role"] for row in reopened], ["HUMAN", "ASSISTANT"])


if __name__ == "__main__":
    unittest.main()
