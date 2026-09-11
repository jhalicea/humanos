import tempfile
import unittest
from pathlib import Path

from capture_ledger import CaptureConflict, CaptureLedger


def record(**changes):
    value = {
        "message_id": "message-1",
        "chat_id": "chat-1",
        "chat_title": "Design",
        "role": "USER",
        "text": "exact visible text",
        "observed_at": "2026-09-11T14:00:00.000Z",
        "source_url": "https://chatgpt.com/c/chat-1",
    }
    value.update(changes)
    return value


class CaptureLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.ledger = CaptureLedger(Path(self.temp.name) / "pending.sqlite3")

    def tearDown(self):
        self.ledger.close()
        self.temp.cleanup()

    def test_captures_cross_chat_turns_in_one_pending_ledger(self):
        self.assertEqual(self.ledger.capture(record())["status"], "CAPTURED")
        self.ledger.capture(record(message_id="message-2", chat_id="chat-2",
                                   role="ASSISTANT", text="reply"))
        rows = list(self.ledger.db.execute(
            "SELECT chat_id,role,text,state FROM pending_turns ORDER BY rowid"))
        self.assertEqual([tuple(row) for row in rows], [
            ("chat-1", "USER", "exact visible text", "PENDING"),
            ("chat-2", "ASSISTANT", "reply", "PENDING")])

    def test_identical_redelivery_is_idempotent(self):
        self.ledger.capture(record())
        self.assertEqual(self.ledger.capture(record())["status"], "ALREADY_PENDING")
        self.assertEqual(self.ledger.db.execute(
            "SELECT COUNT(*) FROM pending_turns").fetchone()[0], 1)

    def test_same_id_different_evidence_is_audited_and_rejected(self):
        self.ledger.capture(record())
        with self.assertRaises(CaptureConflict):
            self.ledger.capture(record(text="altered"))
        self.assertEqual(self.ledger.db.execute(
            "SELECT COUNT(*) FROM capture_conflicts").fetchone()[0], 1)
        self.assertEqual(self.ledger.db.execute(
            "SELECT text FROM pending_turns").fetchone()[0], "exact visible text")

    def test_non_chatgpt_source_is_rejected(self):
        with self.assertRaises(PermissionError):
            self.ledger.capture(record(source_url="https://example.com/c/chat-1"))

    def test_pending_evidence_cannot_be_deleted_or_updated(self):
        self.ledger.capture(record())
        with self.assertRaises(Exception):
            with self.ledger.db:
                self.ledger.db.execute("DELETE FROM pending_turns")


if __name__ == "__main__":
    unittest.main()
