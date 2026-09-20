import json
import tempfile
import unittest
from pathlib import Path

from conversation_ledger import import_messages, read_ledger, repair_conversation_ids


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

    def test_session_metadata_supplies_conversation_id_and_legacy_repair_preserves_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.jsonl"
            source.write_text("\n".join([
                json.dumps({"type": "session_meta", "payload": {"session_id": "thread-9"}}),
                json.dumps({"type": "response_item", "payload": {"id": "u1", "role": "user",
                            "content": [{"type": "input_text", "text": "hello"}]}}),
            ]) + "\n", encoding="utf-8")
            ledger = root / "ledger.jsonl"
            self.assertEqual(import_messages(source, ledger), {"added": 1, "total": 1})
            original = read_ledger(ledger)[0]
            self.assertEqual(original["conversation_id"], "thread-9")
            legacy = dict(original)
            legacy["conversation_id"] = None
            ledger.write_text(json.dumps(legacy) + "\n", encoding="utf-8")
            before = (legacy["source_id"], legacy["text"], legacy["content_digest"])
            self.assertEqual(repair_conversation_ids(ledger, "thread-9"), 1)
            repaired = read_ledger(ledger)[0]
            self.assertEqual((repaired["source_id"], repaired["text"], repaired["content_digest"]), before)
            self.assertEqual(repaired["conversation_id"], "thread-9")


if __name__ == "__main__":
    unittest.main()
