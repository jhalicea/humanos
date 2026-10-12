import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from capture_current_conversation import DEFAULT_LEDGER, capture_audit, capture_current, capture_status, resolve_source
from conversation_ledger import append_conversation_id_correction, import_messages, read_ledger, verify_ledger


class ConversationLedgerTests(unittest.TestCase):

    def test_simultaneous_processes_only_append_each_selected_message_once(self):
        """Both writers queue on the same lock, then dedup against committed rows."""
        from conversation_ledger import _ledger_writer
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, ledger = root / "source.jsonl", root / "ledger.jsonl"
            records = [
                {"type": "session_meta", "payload": {"session_id": "synthetic-concurrent"}},
                {"type": "response_item", "payload": {"id": "u1", "role": "user",
                    "content": [{"type": "input_text", "text": "human"}]}},
                {"type": "response_item", "payload": {"id": "a1", "role": "assistant",
                    "content": [{"type": "output_text", "text": "answer"}]}},
            ]
            source.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
            script = (
                "import json,pathlib,sys; from conversation_ledger import import_messages; "
                "pathlib.Path(sys.argv[3]).write_text('ready'); "
                "print(json.dumps(import_messages(sys.argv[1],sys.argv[2])))"
            )
            processes = []
            try:
                # Force both workers to arrive before either may read the ledger.
                with _ledger_writer(ledger):
                    for i in range(2):
                        ready = root / ("ready-" + str(i))
                        processes.append(subprocess.Popen(
                            [sys.executable, "-c", script, str(source), str(ledger), str(ready)],
                            cwd=str(Path(__file__).resolve().parents[1]),
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True))
                    deadline = time.monotonic() + 10
                    while (not all((root / ("ready-" + str(i))).exists() for i in range(2))
                           and time.monotonic() < deadline):
                        time.sleep(0.02)
                    self.assertTrue(all((root / ("ready-" + str(i))).exists()
                                        for i in range(2)), "children did not reach lock")
                    self.assertFalse(ledger.exists(), "ledger was written while locked")
                results = []
                for proc in processes:
                    stdout, stderr = proc.communicate(timeout=15)
                    self.assertEqual(proc.returncode, 0, stderr)
                    results.append(json.loads(stdout))
                self.assertEqual(sorted(result["added"] for result in results), [0, 2])
                self.assertEqual([row["source_id"] for row in read_ledger(ledger)],
                                 ["u1", "a1"])
                self.assertEqual(verify_ledger(ledger),
                                 {"rows": 2, "status": "CHECKPOINTED"})
            finally:
                for proc in processes:
                    if proc.poll() is None:
                        proc.kill()
                    proc.communicate()

    def test_ledger_and_persistent_lock_are_owner_only_even_under_open_umask(self):
        import stat
        from conversation_ledger import append_observed_turn
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ledger = root / "ledger.jsonl"
            former = os.umask(0)
            try:
                append_observed_turn(ledger, "synthetic", "c", "t1", "human", "assistant")
            finally:
                os.umask(former)
            self.assertEqual(stat.S_IMODE(ledger.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE((root / "ledger.jsonl.writer.lock").stat().st_mode),
                             0o600)
            self.assertEqual(verify_ledger(ledger)["rows"], 2)

    def test_existing_group_readable_ledger_fails_closed_without_mutation(self):
        from conversation_ledger import append_observed_turn
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "ledger.jsonl"
            append_observed_turn(ledger, "synthetic", "c", "t1", "human", "assistant")
            expected = ledger.read_bytes()
            ledger.chmod(0o644)
            with self.assertRaises(PermissionError):
                append_observed_turn(ledger, "synthetic", "c", "t2", "human2", "assistant2")
            self.assertEqual(ledger.read_bytes(), expected)
            self.assertEqual(verify_ledger(ledger)["rows"], 2)


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

    def test_default_ledger_is_runtime_owned(self):
        self.assertTrue(str(DEFAULT_LEDGER).endswith("/var/current-conversation.jsonl"))

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

    def test_capture_audit_reports_receipts_and_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.jsonl"
            source.write_text(json.dumps({"type": "session_meta", "payload": {"session_id": "thread-9"}}) + "\n" +
                              json.dumps({"type": "response_item", "payload": {"id": "u1", "role": "user",
                              "content": [{"type": "input_text", "text": "audit"}]}}) + "\n", encoding="utf-8")
            ledger = root / "ledger.jsonl"
            capture_current(ledger, source)
            audit = capture_audit(ledger)
            self.assertEqual(audit["status"], "CHECKPOINTED")
            self.assertEqual(audit["rows"], 1)
            self.assertEqual(audit["receipts"], 1)

    def test_verify_ledger_fails_on_digest_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.jsonl"
            ledger.write_text(json.dumps({"source": "s", "source_id": "1", "conversation_id": "c",
                "role": "HUMAN", "text": "changed", "content_digest": "wrong"}) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                verify_ledger(ledger)

    def test_failed_capture_writes_recovery_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.jsonl"
            source.write_text(json.dumps({"type": "response_item", "payload": {"id": "u1", "role": "user",
                "content": [{"type": "input_text", "text": "no metadata"}]}}) + "\n", encoding="utf-8")
            ledger = root / "ledger.jsonl"
            with self.assertRaisesRegex(ValueError, "conversation ID"):
                capture_current(ledger, source)
            receipt = (root / "capture-receipts.jsonl").read_text(encoding="utf-8")
            self.assertIn("RECOVERY REQUIRED", receipt)
            self.assertFalse(ledger.exists())

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
