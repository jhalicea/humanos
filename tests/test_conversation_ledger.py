import json
import tempfile
import unittest
from pathlib import Path

from capture_current_conversation import capture_current, capture_status, resolve_source
from conversation_ledger import append_conversation_id_correction, import_messages, read_ledger, verify_ledger


class ConversationLedgerTests(unittest.TestCase):
    def test_import_is_exact_idempotent_and_reopenable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.jsonl"
            source.write_text("\n".join([
                json.dumps({"type": "session_meta", "payload": {"session_id": "thread-9"}}),
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

    def test_current_capture_resolves_session_rollout(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rollout = root / "2026" / "09" / "19" / "rollout-2026-09-19-thread-9.jsonl"
            rollout.parent.mkdir(parents=True)
            rollout.write_text("", encoding="utf-8")
            self.assertEqual(resolve_source("thread-9", root), rollout)

    def test_capture_current_uses_explicit_source_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.jsonl"
            source.write_text(json.dumps({"type": "session_meta", "payload": {"session_id": "thread-9"}}) + "\n" +
                              json.dumps({"type": "response_item", "payload": {"id": "u1", "role": "user",
                              "content": [{"type": "input_text", "text": "capture"}]}}) + "\n", encoding="utf-8")
            ledger = root / "ledger.jsonl"
            first_result = capture_current(ledger, source)
            self.assertEqual(first_result["added"], 1)
            self.assertEqual(first_result["status"], "CHECKPOINTED")
            result = capture_current(ledger, source)
            self.assertEqual(result["added"], 0)
            self.assertEqual(result["status"], "CHECKPOINTED")
            receipts = root / "capture-receipts.jsonl"
            self.assertEqual(len(receipts.read_text(encoding="utf-8").splitlines()), 2)
            self.assertEqual(capture_status(ledger)["status"], "CHECKPOINTED")
            ledger.write_text(ledger.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            self.assertEqual(capture_status(ledger)["status"], "RECOVERY REQUIRED")

    def test_verify_ledger_fails_on_digest_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.jsonl"
            ledger.write_text(json.dumps({"source": "s", "source_id": "1", "conversation_id": "c",
                "role": "HUMAN", "text": "changed", "content_digest": "wrong"}) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                verify_ledger(ledger)

    def test_invalid_batch_does_not_append_partial_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.jsonl"
            source.write_text("\n".join([
                json.dumps({"type": "session_meta", "payload": {"session_id": "thread-9"}}),
                json.dumps({"type": "response_item", "payload": {"id": "u1", "role": "user",
                            "content": [{"type": "input_text", "text": "good"}]}}),
                json.dumps({"type": "response_item", "payload": {"id": "u2", "role": "user",
                            "content": [{"type": "input_text", "text": "bad"}]}}),
            ]) + "\n", encoding="utf-8")
            ledger = root / "ledger.jsonl"
            import_messages(source, ledger)
            before = ledger.read_bytes()
            source.write_text("\n".join([
                json.dumps({"type": "response_item", "payload": {"id": "u1", "role": "user",
                            "content": [{"type": "input_text", "text": "good"}]}}),
                json.dumps({"type": "response_item", "payload": {"id": "u3", "role": "user",
                            "content": []}}),
            ]) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "source message"):
                import_messages(source, ledger)
            self.assertEqual(ledger.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
