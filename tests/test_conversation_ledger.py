import json
import tempfile
import unittest
from pathlib import Path

from conversation_ledger import append_conversation_id_correction, import_messages, read_ledger


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

    def test_session_metadata_supplies_conversation_id_and_correction_is_appended(self):
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
            before = ledger.read_bytes()
            correction = append_conversation_id_correction(ledger, "u1", "thread-9")
            self.assertEqual(correction["event_type"], "METADATA_CORRECTION")
            self.assertTrue(ledger.read_bytes().startswith(before))
            self.assertEqual(read_ledger(ledger)[0], original)

    def test_incremental_import_appends_only_new_observed_turn(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.jsonl"
            meta = {"type": "session_meta", "payload": {"session_id": "thread-9"}}
            first = {"type": "response_item", "payload": {"id": "u1", "role": "user",
                    "content": [{"type": "input_text", "text": "first"}]}}
            second = {"type": "response_item", "payload": {"id": "a1", "role": "assistant",
                    "content": [{"type": "output_text", "text": "second"}]}}
            source.write_text("\n".join(json.dumps(row) for row in (meta, first, second)) + "\n", encoding="utf-8")
            ledger = root / "ledger.jsonl"
            self.assertEqual(import_messages(source, ledger), {"added": 2, "total": 2})
            before = ledger.read_bytes()
            third = {"type": "response_item", "payload": {"id": "u2", "role": "user",
                    "content": [{"type": "input_text", "text": "new turn"}]}}
            with source.open("a", encoding="utf-8") as stream:
                stream.write(json.dumps(third) + "\n")
            self.assertEqual(import_messages(source, ledger), {"added": 1, "total": 3})
            self.assertTrue(ledger.read_bytes().startswith(before))
            self.assertEqual(import_messages(source, ledger), {"added": 0, "total": 3})


if __name__ == "__main__":
    unittest.main()
