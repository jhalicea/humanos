import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from conversation_capture import UniversalConversationCapture
from experiments.ln0_migration_spike import (
    MigrationConflict,
    migrate_runtime_fixture,
    verify_candidate_chain,
)
from notebook import Notebook


class LN0MigrationSpikeTests(unittest.TestCase):
    """V-01 uses only synthetic temporary Notebook data."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.vault = self.root / "vault"
        self.target = self.root / "candidate-kernel.sqlite3"
        self.book = Notebook(self.vault)
        self.book.recover()
        self.binding = self.book.bind("Synthetic Owner", "synthetic opening")

        self.same_text = "  exact duplicate text 🧭\r\nline two  "
        capture = UniversalConversationCapture(self.book, "chatgpt-test")
        self.captured_tx = capture.capture_turn(
            self.binding["hcid"],
            "synthetic-conversation",
            "synthetic-turn",
            self.same_text,
            self.same_text,
        )

        self.pending_tx = "synthetic-recovery-tx"
        self.pending_text = "  recovery input remains unresolved 🧭\n"
        self.book.start(self.binding["hcid"], self.pending_tx, self.pending_text)
        created = "2026-09-25T12:34:56+00:00"
        with self.book.db:
            self.book.db.execute(
                "UPDATE transactions SET status='RECOVERY_REQUIRED' WHERE tx=?",
                (self.pending_tx,),
            )
            self.book.db.execute(
                "INSERT INTO recovery(tx,error,closed,created,scope) VALUES(?,?,?,?,?)",
                (self.pending_tx, "synthetic injected recovery", 0, created, "NOTEBOOK"),
            )
            self.book.db.execute(
                "INSERT INTO privacy_operations(op_id,tx,ordinal,operation,actor,created) "
                "VALUES(?,?,?,?,?,?)",
                ("privacy-op-1", self.captured_tx, 0, "HIDE", "OWNER", created),
            )
            self.book.db.execute(
                "INSERT INTO privacy_state(tx,ordinal,state,updated) VALUES(?,?,?,?)",
                (self.captured_tx, 0, "HIDDEN", created),
            )
            self.book.db.execute(
                "INSERT INTO privacy_receipts(receipt_id,op_id,operation,actor,created) "
                "VALUES(?,?,?,?,?)",
                ("privacy-receipt-1", "privacy-op-1", "HIDE", "OWNER", created),
            )

        # Make the fixture include the same projection classes Runtime 0.1 uses.
        self.book.project()
        self.runtime_root = self.book.root
        self.book.close()
        self.book = None

    def tearDown(self):
        if self.book is not None:
            self.book.close()
        self.tmp.cleanup()

    def _target_db(self):
        db = sqlite3.connect(self.target)
        db.row_factory = sqlite3.Row
        return db

    def test_v01_exact_evidence_coverage_and_idempotency(self):
        first = migrate_runtime_fixture(self.runtime_root, self.target)
        self.assertEqual(first["source_records"], first["mapped_records"])
        self.assertGreater(first["migrated_evidence"], 0)
        self.assertGreater(first["retained_records"], 0)
        self.assertEqual(first["kernel_events"], first["payload_objects"])
        self.assertTrue(verify_candidate_chain(self.target))

        db = self._target_db()
        try:
            # Transcript payloads preserve exact UTF-8 text, including whitespace,
            # CR/LF and Unicode. The identical HUMAN/ASSISTANT messages are still
            # independent payload objects rather than deduplicated storage identity.
            captured = list(
                db.execute(
                    "SELECT k.legacy_source_key,p.payload_id,p.content_hash,p.payload "
                    "FROM kernel_events k JOIN payload_objects p ON p.payload_id=k.payload_id "
                    "WHERE k.legacy_source_name='transcript' ORDER BY k.seq"
                )
            )
            duplicate_rows = [row for row in captured if row["payload"] == self.same_text.encode("utf-8")]
            self.assertEqual(len(duplicate_rows), 2)
            self.assertNotEqual(duplicate_rows[0]["payload_id"], duplicate_rows[1]["payload_id"])
            self.assertEqual(duplicate_rows[0]["content_hash"], duplicate_rows[1]["content_hash"])

            pending = [row for row in captured if row["payload"] == self.pending_text.encode("utf-8")]
            self.assertEqual(len(pending), 1)

            # Stable source identities remain explicitly mapped even when they are
            # operational metadata rather than promoted kernel history.
            identity = db.execute(
                "SELECT status,target_ref FROM legacy_records WHERE source_name='identities' LIMIT 1"
            ).fetchone()
            self.assertIsNotNone(identity)
            self.assertEqual(identity["status"], "RETAINED_OPERATIONAL")
            self.assertTrue(identity["target_ref"].startswith("legacy:DB_ROW:identities:"))

            # Recovery failure is migrated as failure evidence, not rewritten into
            # a successful/checkpointed event.
            recovery_payload = db.execute(
                "SELECT p.payload FROM kernel_events k JOIN payload_objects p ON p.payload_id=k.payload_id "
                "WHERE k.legacy_source_name='recovery' ORDER BY k.seq DESC LIMIT 1"
            ).fetchone()
            self.assertIsNotNone(recovery_payload)
            recovery = json.loads(bytes(recovery_payload["payload"]).decode("utf-8"))
            self.assertEqual(recovery["closed"], 0)
            self.assertEqual(recovery["tx"], self.pending_tx)

            # Privacy action and receipt remain distinct auditable records.
            self.assertEqual(
                db.execute(
                    "SELECT COUNT(*) FROM legacy_records WHERE source_name IN ('privacy_operations','privacy_receipts') "
                    "AND status='MIGRATED_EVIDENCE'"
                ).fetchone()[0],
                2,
            )

            # Current per-record integrity/digest fields are preserved inside the
            # legacy row envelope even though the candidate event has a new hash chain.
            transcript_legacy = db.execute(
                "SELECT preserved FROM legacy_records WHERE source_name='transcript' ORDER BY source_key LIMIT 1"
            ).fetchone()
            preserved = json.loads(bytes(transcript_legacy["preserved"]).decode("utf-8"))
            self.assertIn("sha256", preserved)
            self.assertIn("record_integrity", preserved)
            self.assertIn("record_integrity_version", preserved)

            # Page/index/binding materializations are retained as projections, not
            # silently promoted to source evidence.
            self.assertGreater(
                db.execute(
                    "SELECT COUNT(*) FROM legacy_records WHERE source_kind='FILE' AND status='RETAINED_PROJECTION'"
                ).fetchone()[0],
                0,
            )
        finally:
            db.close()

        second = migrate_runtime_fixture(self.runtime_root, self.target)
        self.assertTrue(second["idempotent_replay"])
        self.assertEqual(first["source_fingerprint"], second["source_fingerprint"])
        self.assertEqual(first["mapped_records"], second["mapped_records"])
        self.assertEqual(first["kernel_events"], second["kernel_events"])
        self.assertTrue(verify_candidate_chain(self.target))

    def test_v01_changed_source_fails_closed(self):
        migrate_runtime_fixture(self.runtime_root, self.target)
        source_db = sqlite3.connect(self.runtime_root / "notebook.sqlite3")
        try:
            with source_db:
                source_db.execute(
                    "UPDATE transactions SET input=? WHERE tx=?",
                    ("tampered after migration", self.pending_tx),
                )
        finally:
            source_db.close()

        with self.assertRaises(MigrationConflict):
            migrate_runtime_fixture(self.runtime_root, self.target)


if __name__ == "__main__":
    unittest.main()
