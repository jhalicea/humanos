"""Synthetic end-to-end custody of one selected turn; no owner/session discovery."""
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock

try:
    import cryptography  # noqa: F401
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from capture_current_conversation import capture_current
from conversation_ledger import read_ledger, verify_ledger
from ledger_notebook_projection import project_all_pairs
from notebook import Notebook
from vault_encryption import EncryptedBackupError, create_encrypted_backup
from conversation_custody import (
    CustodyError, create_custody_backup, verify_custody_backup,
    restore_custody_backup,
)


@unittest.skipUnless(HAS_CRYPTO, "optional cryptography dependency unavailable")
class SelectedConversationCustodyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "selected.jsonl"
        self.ledger = self.root / "evidence.jsonl"
        self.receipts = self.root / "capture-receipts.jsonl"
        self.vault = self.root / "notebook"
        self.encrypted = self.root / "complete-evidence.hosenc"
        self.passphrase = "synthetic owner private custody passphrase"
        self.human = "SYNTHETIC-PRIVATE-HUMAN-8127\nline two"
        self.assistant = "SYNTHETIC-PRIVATE-ASSISTANT-9394"
        records = [
            {"type": "session_meta", "payload": {"id": "synthetic-custody"}},
            {"type": "response_item", "payload": {"id": "h1", "role": "user",
                "content": [{"type": "input_text", "text": self.human}]}},
            {"type": "response_item", "payload": {"id": "a1", "role": "assistant",
                "content": [{"type": "output_text", "text": self.assistant}]}},
        ]
        self.source.write_text("\n".join(json.dumps(row) for row in records) + "\n",
                               encoding="utf-8")
        self.source.chmod(0o600)
        capture_current(self.ledger, self.source)
        projected = project_all_pairs(self.ledger, self.vault)
        self.assertEqual(projected["projected"], 1)

    def tearDown(self):
        self.temp.cleanup()

    def backup(self):
        return create_custody_backup(self.source, self.ledger, self.receipts,
                                     self.vault, self.encrypted, self.passphrase)

    def test_encrypted_custody_roundtrip_preserves_all_four_evidence_parts(self):
        original = {n: p.read_bytes() for n, p in (
            ("source", self.source), ("ledger", self.ledger),
            ("receipts", self.receipts))}
        result = self.backup()
        self.assertTrue(result["verified"])
        self.assertTrue(result["staged_restore"])
        content = self.encrypted.read_bytes()
        self.assertNotIn(self.human.encode("utf-8"), content)
        self.assertNotIn(self.assistant.encode("utf-8"), content)
        self.assertNotIn(b"SQLite format 3", content)
        self.assertEqual(stat.S_IMODE(self.encrypted.stat().st_mode), 0o600)
        self.assertTrue(verify_custody_backup(self.encrypted, self.passphrase)["verified"])
        target = self.root / "restored"
        restored = restore_custody_backup(self.encrypted, target, self.passphrase)
        self.assertTrue(restored["restored"])
        for n, target_name in [("source", "source.jsonl"),
                               ("ledger", "ledger.jsonl"),
                               ("receipts", "capture-receipts.jsonl")]:
            self.assertEqual(original[n], (target / "evidence" / target_name).read_bytes())
        self.assertEqual(verify_ledger(target / "evidence/ledger.jsonl")["rows"], 2)
        restored_vault = Notebook(target / "vault")
        try:
            self.assertTrue(restored_vault.verify())
            self.assertEqual(restored_vault.get_transaction("CAPTURE-a1")["status"],
                             "CHECKPOINTED")
        finally:
            restored_vault.close()

    def test_interrupted_encryption_never_publishes_partial_output(self):
        def simulated_crash(tar_path, output, passphrase, *, payload):
            Path(output).write_bytes(b"SYNTHETIC-UNTRUSTED-PARTIAL")
            raise OSError("synthetic encryption interruption")
        with mock.patch("conversation_custody._encrypt_tar",
                        side_effect=simulated_crash):
            with self.assertRaises(OSError):
                self.backup()
        self.assertFalse(self.encrypted.exists())

    def test_staged_restore_failure_never_publishes_output(self):
        with mock.patch("conversation_custody._decrypt_and_check",
                        side_effect=CustodyError("synthetic staged restore mismatch")):
            with self.assertRaises(CustodyError):
                self.backup()
        self.assertFalse(self.encrypted.exists())

    def test_custody_output_inside_vault_is_denied(self):
        with self.assertRaises(CustodyError):
            create_custody_backup(
                self.source, self.ledger, self.receipts, self.vault,
                self.vault / "untrusted.hosenc", self.passphrase)
        self.assertFalse((self.vault / "untrusted.hosenc").exists())

    def test_extra_unselected_source_message_is_not_archived(self):
        # Extra evidence remains in the explicitly named source file.
        # It must never hitchhike into a "one selected turn" backup.
        rows = [json.loads(x) for x in self.source.read_text(encoding="utf-8").splitlines()]
        rows.append({"type": "response_item", "payload": {
            "id": "unrelated-user", "role": "user",
            "content": [{"type": "input_text", "text": "SYNTHETIC OTHER SECRET"}]}})
        self.source.write_text("\n".join(json.dumps(row) for row in rows) + "\n",
                               encoding="utf-8")
        self.source.chmod(0o600)
        with self.assertRaisesRegex(CustodyError, "other messages"):
            self.backup()
        self.assertFalse(self.encrypted.exists())

    def test_old_unselected_receipt_is_not_archived(self):
        previous = {"captured_at": "2026-01-01T00:00:00Z",
                    "source": "codex-rollout", "conversation_id": "other-chat",
                    "status": "CHECKPOINTED", "ledger_digest": "f" * 64,
                    "added": 2, "total": 2}
        history = self.receipts.read_bytes()
        self.receipts.write_bytes((json.dumps(previous) + "\n").encode("utf-8") + history)
        self.receipts.chmod(0o600)
        with self.assertRaisesRegex(CustodyError, "other capture receipts"):
            self.backup()
        self.assertFalse(self.encrypted.exists())

    def test_unrelated_notebook_turn_is_not_archived(self):
        book = Notebook(self.vault)
        try:
            identity = book.bind("Jon", "SYNTHETIC UNRELATED HUMAN")
            book.start(identity["hcid"], "other-turn", "SYNTHETIC UNRELATED HUMAN")
            book.append("other-turn", 1, "ASSISTANT", "SYNTHETIC UNRELATED ASSISTANT")
            book.save_task("other-turn", {"phase": "COMPLETE",
                "final": "SYNTHETIC UNRELATED ASSISTANT", "final_ordinal": 1})
            book.checkpoint("other-turn")
            self.assertTrue(book.verify())
        finally:
            book.close()
        with self.assertRaisesRegex(CustodyError, "unrelated Notebook"):
            self.backup()
        self.assertFalse(self.encrypted.exists())

    def test_missing_receipts_denies_create_without_partial_artifact(self):
        self.receipts.unlink()
        with self.assertRaises((FileNotFoundError, CustodyError)):
            self.backup()
        self.assertFalse(self.encrypted.exists())

    def test_changed_source_denies_capture_custody(self):
        records = [json.loads(line) for line in self.source.read_text(encoding="utf-8").splitlines()]
        records[1]["payload"]["content"][0]["text"] = "DIFFERENT HUMAN"
        self.source.write_text("\n".join(json.dumps(row) for row in records) + "\n",
                               encoding="utf-8")
        self.source.chmod(0o600)
        with self.assertRaises(CustodyError):
            self.backup()
        self.assertFalse(self.encrypted.exists())

    def test_tampered_capture_receipt_denies_custody(self):
        records = [json.loads(line) for line in self.receipts.read_text().splitlines()]
        records[-1]["ledger_digest"] = "0" * 64
        self.receipts.write_text("\n".join(json.dumps(row) for row in records) + "\n",
                                 encoding="utf-8")
        self.receipts.chmod(0o600)
        with self.assertRaises(CustodyError):
            self.backup()
        self.assertFalse(self.encrypted.exists())

    def test_existing_vault_encryption_payload_is_not_interchangeable(self):
        old = self.root / "vault-only.hosenc"
        create_encrypted_backup(self.vault, old, self.passphrase)
        with self.assertRaisesRegex(EncryptedBackupError, "payload type"):
            verify_custody_backup(old, self.passphrase)

    def test_wrong_passphrase_and_tamper_do_not_restore(self):
        self.backup()
        target = self.root / "must-stay-absent"
        with self.assertRaises(EncryptedBackupError):
            restore_custody_backup(self.encrypted, target, "wrong passphrase")
        self.assertFalse(target.exists())
        tampered = bytearray(self.encrypted.read_bytes())
        tampered[-1] ^= 1
        self.encrypted.write_bytes(tampered)
        self.encrypted.chmod(0o600)
        with self.assertRaises(EncryptedBackupError):
            restore_custody_backup(self.encrypted, target, self.passphrase)
        self.assertFalse(target.exists())

    def test_nonempty_or_existing_destination_not_overwritten(self):
        self.backup()
        dest = self.root / "already"
        dest.mkdir()
        (dest / "important").write_text("PRESERVE", encoding="utf-8")
        with self.assertRaises(CustodyError):
            restore_custody_backup(self.encrypted, dest, self.passphrase)
        self.assertEqual((dest / "important").read_text(encoding="utf-8"), "PRESERVE")

    def test_torn_ledger_cannot_be_custody_backed(self):
        with self.ledger.open("ab") as f:
            f.write(b'{"incomplete":')
        with self.assertRaises(ValueError):
            self.backup()
        self.assertFalse(self.encrypted.exists())
