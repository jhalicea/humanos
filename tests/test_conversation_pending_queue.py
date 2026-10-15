import hashlib
import os
import sqlite3
import stat
import tempfile
import unittest
from pathlib import Path

from conversation_pending_queue import (
    ConversationPendingQueue,
    EventConflictError,
    ObservedConversationEvent,
    PendingQueueError,
)


def event(**overrides):
    values = {
        "event_id": "evt-1",
        "conversation_id": "conversation-1",
        "source": "synthetic-provider",
        "role": "human",
        "content": "  exact UTF-8 🧭\r\nline two: e\u0301  ",
        "observed_timestamp": "2026-09-16T12:00:00+00:00",
        "ordering_evidence": "source-sequence:7",
        "capture_method": "synthetic-observer-fixture",
        "privacy_policy_version": "foundation-v1",
    }
    values.update(overrides)
    return ObservedConversationEvent(**values)


class ConversationPendingQueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "pending.sqlite3"

    def tearDown(self):
        self.tmp.cleanup()

    def test_exact_round_trip_and_durable_sqlite_settings(self):
        queue = ConversationPendingQueue(self.path)
        result = queue.enqueue(event())
        self.assertEqual(result["content"], event().content)
        self.assertEqual(
            result["content_hash"], hashlib.sha256(event().content.encode("utf-8")).hexdigest()
        )
        self.assertEqual(result["destinations"], {
            "relay": "PENDING", "notebook": "PENDING", "recovery_export": "PENDING",
        })
        self.assertEqual(queue.db.execute("PRAGMA journal_mode").fetchone()[0], "wal")
        self.assertEqual(queue.db.execute("PRAGMA synchronous").fetchone()[0], 2)
        queue.close()

    def test_restart_preserves_exact_event_and_pending_destinations(self):
        with ConversationPendingQueue(self.path) as queue:
            queue.enqueue(event(role="assistant", content="assistant\n exact 🧪"))
        with ConversationPendingQueue(self.path) as restarted:
            result = restarted.get("evt-1")
            self.assertEqual(result["content"], "assistant\n exact 🧪")
            self.assertEqual(len(result["destinations"]), 3)
            self.assertTrue(result["committed"])

    def test_identical_retry_is_idempotent(self):
        with ConversationPendingQueue(self.path) as queue:
            first = queue.enqueue(event())
            second = queue.enqueue(event())
            self.assertFalse(first["idempotent"])
            self.assertTrue(second["idempotent"])
            self.assertEqual(first["event_id"], second["event_id"])
            self.assertEqual(queue.db.execute("SELECT COUNT(*) FROM conversation_events").fetchone()[0], 1)
            self.assertEqual(queue.db.execute("SELECT COUNT(*) FROM pending_destinations").fetchone()[0], 3)

    def test_conflicting_duplicate_fails_closed(self):
        with ConversationPendingQueue(self.path) as queue:
            queue.enqueue(event())
            conflicts = (
                {"content": "different exact evidence"},
                {"conversation_id": "conversation-2"},
                {"source": "different-provider"},
                {"role": "assistant"},
                {"observed_timestamp": "2026-09-16T12:00:01+00:00"},
                {"source_timestamp": "2026-09-16T11:59:59+00:00"},
                {"ordering_evidence": "source-sequence:8"},
                {"capture_method": "different-fixture"},
                {"parent_event_id": "evt-parent"},
                {"revision_id": "revision-2"},
                {"supersedes_event_id": "evt-old"},
                {"privacy_policy_version": "foundation-v2"},
            )
            for override in conflicts:
                with self.subTest(override=override):
                    with self.assertRaises(EventConflictError):
                        queue.enqueue(event(**override))
            self.assertEqual(queue.get("evt-1")["content"], event().content)
            self.assertEqual(queue.db.execute("SELECT COUNT(*) FROM conversation_events").fetchone()[0], 1)

    def test_invalid_role_rejected_without_event(self):
        with ConversationPendingQueue(self.path) as queue:
            with self.assertRaises(ValueError):
                queue.enqueue(event(role="system"))
            self.assertIsNone(queue.get("evt-1"))

    def test_failed_atomic_transaction_leaves_no_event_or_acknowledgement(self):
        with ConversationPendingQueue(self.path) as queue:
            queue.db.execute(
                """CREATE TRIGGER fail_notebook_destination
                   BEFORE INSERT ON pending_destinations
                   WHEN NEW.destination='notebook'
                   BEGIN SELECT RAISE(ABORT, 'synthetic destination failure'); END"""
            )
            queue.db.commit()
            with self.assertRaises(sqlite3.IntegrityError):
                queue.enqueue(event())
            self.assertIsNone(queue.get("evt-1"))
            self.assertEqual(queue.pending_destinations("evt-1"), {})
            self.assertEqual(queue.db.execute("SELECT COUNT(*) FROM conversation_events").fetchone()[0], 0)
            self.assertEqual(queue.db.execute("SELECT COUNT(*) FROM pending_destinations").fetchone()[0], 0)

    def test_shared_parent_is_rejected_without_permission_mutation(self):
        shared_parent = Path(self.tmp.name) / "shared"
        shared_parent.mkdir(mode=0o755)
        os.chmod(shared_parent, 0o755)
        original_mode = stat.S_IMODE(shared_parent.stat().st_mode)

        with self.assertRaises(PendingQueueError):
            ConversationPendingQueue(shared_parent / "pending.sqlite3")

        self.assertEqual(stat.S_IMODE(shared_parent.stat().st_mode), original_mode)
        self.assertFalse((shared_parent / "pending.sqlite3").exists())


if __name__ == "__main__":
    unittest.main()
