"""Synthetic kill-point acceptance for manual one-turn Codex -> Life Notebook import.

Never discovers Codex sessions, needs no private owner vault, writes only to
TemporaryDirectory() and uses real independent Python subprocesses.
"""
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest

from capture_current_conversation import capture_status
from conversation_ledger import read_ledger, verify_ledger
from notebook import Notebook

REPO = Path(__file__).resolve().parents[1]
PYTHON = sys.executable
HUMAN = "synthetic crash-boundary human 🧭\n exact"
ASSISTANT = "synthetic crash-boundary assistant \n final"


def _fixture(root):
    source = root / "synthetic-source.jsonl"
    dest = root / "private"
    dest.mkdir(mode=0o700)
    ledger = dest / "evidence.jsonl"
    vault = dest / "notebook"
    rows = [
        {"type": "session_meta", "payload": {"id": "synthetic-crash-session"}},
        {"type": "response_item", "payload": {"type": "message", "id": "synthetic-human-id",
             "role": "user", "content": [{"type": "input_text", "text": HUMAN}]}},
        {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "synthetic-turn"}},
        {"type": "response_item", "payload": {"type": "message", "id": "synthetic-assistant-id",
             "role": "assistant", "content": [{"type": "output_text", "text": ASSISTANT}]}},
    ]
    source.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                      encoding="utf-8")
    source.chmod(0o600)
    args = ["import-codex", "--source", str(source), "--ledger", str(ledger),
            "--notebook", str(vault), "--confirm-observed"]
    return source, ledger, vault, args


def _run_cli(args):
    return subprocess.run([PYTHON, str(REPO / "humanos.py"), *args],
                          cwd=str(REPO), capture_output=True, text=True, timeout=30)


def _kill_at(stage, args):
    # Deliberately abrupt process exit, not an exception that could run cleanup.
    code = r'''
import os
import sys
import humanos
if sys.argv[1] == "BEFORE_PROJECTION":
    humanos.project_all_pairs = lambda *a, **kw: os._exit(71)
elif sys.argv[1] == "AFTER_CHECKPOINT":
    real = humanos.project_all_pairs
    def finish_then_die(*a, **kw):
        real(*a, **kw)
        os._exit(72)
    humanos.project_all_pairs = finish_then_die
elif sys.argv[1] == "MID_NOTEBOOK":
    import ledger_notebook_projection as projection
    def half_project(book, tx, human, assistant, *, include_final_phase=False):
        identity = book.bind("Jon", human["text"])
        book.start(identity["hcid"], tx, human["text"],
                   source_binding=projection._source_evidence_binding(human, assistant))
        os._exit(73)
    projection._project_new = half_project
else:
    raise AssertionError("unknown synthetic test stage")
humanos.main(sys.argv[2:])
'''
    return subprocess.run([PYTHON, "-c", code, stage, *args],
                          cwd=str(REPO), capture_output=True, text=True, timeout=30)


class SyntheticCodexImportInterruptionTests(unittest.TestCase):
    def _assert_checkpoint(self, vault):
        book = Notebook(vault)
        try:
            self.assertTrue(book.verify())
            transaction = book.get_transaction("CAPTURE-synthetic-assistant-id")
            self.assertEqual(transaction["status"], "CHECKPOINTED")
            state = book.task("CAPTURE-synthetic-assistant-id")
            self.assertEqual(state["conversation_id"], "synthetic-crash-session")
            self.assertEqual(state["source_id"], "codex-rollout") if "source_id" in state else None
            self.assertEqual(state["human_source_id"], "synthetic-human-id")
            self.assertEqual(state["assistant_source_id"], "synthetic-assistant-id")
            self.assertEqual(state["final"], ASSISTANT)
            records = [dict(row) for row in book.db.execute(
                "SELECT role,text FROM transcript WHERE tx=? ORDER BY ordinal",
                ("CAPTURE-synthetic-assistant-id",))]
            self.assertEqual(records, [{"role": "HUMAN", "text": HUMAN},
                                       {"role": "ASSISTANT", "text": ASSISTANT}])
            self.assertEqual(book.db.execute("SELECT COUNT(*) FROM transactions").fetchone()[0],
                             1)
        finally:
            book.close()

    def test_crash_after_manual_confirmation_reuses_one_approval_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, ledger, vault, args = _fixture(Path(tmp))
            self.assertEqual(_kill_at("MID_NOTEBOOK", args).returncode, 73)
            before = ledger.read_bytes()
            code = r'''
import os, sys
import notebook
import humanos
original = notebook.Notebook.event
def die_after_approval(self, tx, kind, payload):
    outcome = original(self, tx, kind, payload)
    if kind == "CODEX_RECONCILIATION_CONFIRMED":
        os._exit(74)
    return outcome
notebook.Notebook.event = die_after_approval
humanos.main(sys.argv[1:])
'''
            recovery = ["reconcile-codex", "--ledger", str(ledger),
                        "--notebook", str(vault), "--human-source-id",
                        "synthetic-human-id", "--assistant-source-id",
                        "synthetic-assistant-id", "--confirm-reconcile"]
            interrupted = subprocess.run([PYTHON, "-c", code, *recovery],
                                         cwd=str(REPO), capture_output=True, text=True, timeout=30)
            self.assertEqual(interrupted.returncode, 74, interrupted.stderr)
            book = Notebook(vault)
            try:
                self.assertTrue(book.verify())
                self.assertEqual(book.message_count("CAPTURE-synthetic-assistant-id"), 1)
                self.assertEqual(book.db.execute(
                    "SELECT COUNT(*) FROM events WHERE kind='CODEX_RECONCILIATION_CONFIRMED'"
                ).fetchone()[0], 1)
            finally:
                book.close()
            restarted = _run_cli(recovery)
            self.assertEqual(restarted.returncode, 0, restarted.stderr)
            self.assertEqual(json.loads(restarted.stdout)["status"], "MANUALLY_RECONCILED")
            self._assert_checkpoint(vault)
            book = Notebook(vault)
            try:
                self.assertEqual(book.db.execute(
                    "SELECT COUNT(*) FROM events WHERE kind='CODEX_RECONCILIATION_CONFIRMED'"
                ).fetchone()[0], 1)
            finally:
                book.close()
            self.assertEqual(ledger.read_bytes(), before)

    def test_crash_after_assistant_append_stays_fail_closed_and_preserves_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, ledger, vault, args = _fixture(Path(tmp))
            self.assertEqual(_kill_at("MID_NOTEBOOK", args).returncode, 73)
            prior_ledger = ledger.read_bytes()
            script = r'''
import os, sys
import notebook
import humanos
old = notebook.Notebook.append
def die_after_append(self, tx, ordinal, role, text):
    value = old(self, tx, ordinal, role, text)
    if tx == "CAPTURE-synthetic-assistant-id" and ordinal == 1:
        os._exit(75)
    return value
notebook.Notebook.append = die_after_append
humanos.main(sys.argv[1:])
'''
            recovery = ["reconcile-codex", "--ledger", str(ledger),
                        "--notebook", str(vault), "--human-source-id",
                        "synthetic-human-id", "--assistant-source-id",
                        "synthetic-assistant-id", "--confirm-reconcile"]
            interrupted = subprocess.run([PYTHON, "-c", script, *recovery],
                                         cwd=str(REPO), capture_output=True, text=True, timeout=30)
            self.assertEqual(interrupted.returncode, 75, interrupted.stderr)
            book = Notebook(vault)
            try:
                tx = "CAPTURE-synthetic-assistant-id"
                self.assertEqual(book.get_transaction(tx)["status"], "STARTED")
                rows = [r["text"] for r in book.db.execute(
                    "SELECT text FROM transcript WHERE tx=? ORDER BY ordinal", (tx,))]
                self.assertEqual(rows, [HUMAN, ASSISTANT])
            finally:
                book.close()
            retried = _run_cli(recovery)
            self.assertNotEqual(retried.returncode, 0)
            self.assertEqual(retried.stdout, "")
            self.assertEqual(ledger.read_bytes(), prior_ledger)
            book = Notebook(vault)
            try:
                self.assertEqual(book.get_transaction(
                    "CAPTURE-synthetic-assistant-id")["status"], "STARTED")
                self.assertEqual(book.message_count("CAPTURE-synthetic-assistant-id"), 2)
            finally:
                book.close()

    def test_reconcile_refuses_conflicting_or_duplicate_prior_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, ledger, vault, args = _fixture(Path(tmp))
            self.assertEqual(_kill_at("MID_NOTEBOOK", args).returncode, 73)
            prior = ledger.read_bytes()
            book = Notebook(vault)
            try:
                book.event("CAPTURE-synthetic-assistant-id",
                           "CODEX_RECONCILIATION_CONFIRMED",
                           {"source": "codex-rollout", "operator_confirmation": False})
            finally:
                book.close()
            cmd = ["reconcile-codex", "--ledger", str(ledger),
                   "--notebook", str(vault), "--human-source-id",
                   "synthetic-human-id", "--assistant-source-id",
                   "synthetic-assistant-id", "--confirm-reconcile"]
            rejected = _run_cli(cmd)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertEqual(rejected.stdout, "")
            self.assertEqual(ledger.read_bytes(), prior)
            book = Notebook(vault)
            try:
                self.assertEqual(book.message_count("CAPTURE-synthetic-assistant-id"), 1)
            finally:
                book.close()

    def test_recovery_rejects_foreign_same_id_and_same_human_text(self):
        """Matching transaction ID + HUMAN text cannot authorize foreign grafting."""
        with tempfile.TemporaryDirectory() as tmp:
            source, ledger, vault, args = _fixture(Path(tmp))
            self.assertEqual(_kill_at("BEFORE_PROJECTION", args).returncode, 71)
            from notebook import Notebook
            book = Notebook(vault)
            try:
                identity = book.bind("Jon", HUMAN)
                book.start(identity["hcid"], "CAPTURE-synthetic-assistant-id", HUMAN)
            finally:
                book.close()
            original = ledger.read_bytes()
            retry = ["reconcile-codex", "--ledger", str(ledger),
                     "--notebook", str(vault), "--human-source-id",
                     "synthetic-human-id", "--assistant-source-id",
                     "synthetic-assistant-id", "--confirm-reconcile"]
            rejected = _run_cli(retry)
            self.assertNotEqual(rejected.returncode, 0)
            self.assertEqual(rejected.stdout, "")
            self.assertEqual(ledger.read_bytes(), original)
            book = Notebook(vault)
            try:
                self.assertEqual(book.get_transaction("CAPTURE-synthetic-assistant-id")["status"],
                                 "STARTED")
                self.assertEqual(book.message_count("CAPTURE-synthetic-assistant-id"), 1)
                self.assertEqual(book.db.execute(
                    "SELECT COUNT(*) FROM events WHERE kind='CODEX_RECONCILIATION_CONFIRMED'"
                ).fetchone()[0], 0)
            finally:
                book.close()

    def test_recovery_rejects_source_conversation_identity_replacement(self):
        """A ledger with matching message IDs/text but different source session fails."""
        with tempfile.TemporaryDirectory() as tmp:
            source, ledger, vault, args = _fixture(Path(tmp))
            self.assertEqual(_kill_at("MID_NOTEBOOK", args).returncode, 73)
            from conversation_ledger import read_ledger, verify_ledger
            original = read_ledger(ledger)
            different = [dict(item, conversation_id="foreign-synthetic-session")
                         for item in original]
            ledger.write_text("\n".join(json.dumps(x) for x in different) + "\n",
                              encoding="utf-8")
            self.assertEqual(verify_ledger(ledger)["rows"], 2)
            rejected = _run_cli(["reconcile-codex", "--ledger", str(ledger),
                        "--notebook", str(vault), "--human-source-id",
                        "synthetic-human-id", "--assistant-source-id",
                        "synthetic-assistant-id", "--confirm-reconcile"])
            self.assertNotEqual(rejected.returncode, 0)
            self.assertEqual(rejected.stdout, "")
            book = Notebook(vault)
            try:
                self.assertEqual(book.get_transaction("CAPTURE-synthetic-assistant-id")["status"],
                                 "STARTED")
                self.assertEqual(book.message_count("CAPTURE-synthetic-assistant-id"), 1)
            finally:
                book.close()

    def test_crash_started_capture_has_atomic_source_evidence_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, ledger, vault, args = _fixture(Path(tmp))
            self.assertEqual(_kill_at("MID_NOTEBOOK", args).returncode, 73)
            book = Notebook(vault)
            try:
                tx = "CAPTURE-synthetic-assistant-id"
                self.assertEqual(book.get_transaction(tx)["status"], "STARTED")
                self.assertTrue(book.verify())
                proof = [json.loads(item["payload"]) for item in book.db.execute(
                    "SELECT payload FROM events WHERE tx=? AND kind='CODEX_SOURCE_EVIDENCE_BOUND'",
                    (tx,))]
                self.assertEqual(len(proof), 1)
                self.assertEqual(proof[0]["binding_version"], 1)
                self.assertEqual(proof[0]["source"], "codex-rollout")
                self.assertEqual(len(proof[0]["evidence_sha256"]), 64)
            finally:
                book.close()

    def test_explicit_operator_reconciliation_completes_exact_existing_partial(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, ledger, vault, args = _fixture(Path(tmp))
            original_source = source.read_bytes()
            crashed = _kill_at("MID_NOTEBOOK", args)
            self.assertEqual(crashed.returncode, 73, crashed.stderr)
            before = ledger.read_bytes()
            recovery = ["reconcile-codex", "--ledger", str(ledger),
                        "--notebook", str(vault), "--human-source-id",
                        "synthetic-human-id", "--assistant-source-id",
                        "synthetic-assistant-id"]
            denied = _run_cli(recovery)
            self.assertNotEqual(denied.returncode, 0)
            self.assertEqual(denied.stdout, "")
            self.assertEqual(ledger.read_bytes(), before)
            accepted = _run_cli(recovery + ["--confirm-reconcile"])
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            reported = json.loads(accepted.stdout)
            self.assertEqual(reported["status"], "MANUALLY_RECONCILED")
            self.assertEqual(reported["appended"], 1)
            self._assert_checkpoint(vault)
            self.assertEqual(ledger.read_bytes(), before)
            self.assertEqual(source.read_bytes(), original_source)
            again = _run_cli(recovery + ["--confirm-reconcile"])
            self.assertEqual(again.returncode, 0, again.stderr)
            self.assertEqual(json.loads(again.stdout)["status"], "ALREADY_RECONCILED")
            self.assertEqual(ledger.read_bytes(), before)
            self._assert_checkpoint(vault)

    def test_manual_reconcile_requires_exact_owner_selected_source_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, ledger, vault, args = _fixture(Path(tmp))
            self.assertEqual(_kill_at("MID_NOTEBOOK", args).returncode, 73)
            original_ledger = ledger.read_bytes()
            wrong = _run_cli(["reconcile-codex", "--ledger", str(ledger),
                "--notebook", str(vault), "--human-source-id", "incorrect-human",
                "--assistant-source-id", "synthetic-assistant-id",
                "--confirm-reconcile"])
            self.assertNotEqual(wrong.returncode, 0)
            self.assertEqual(wrong.stdout, "")
            self.assertNotIn(HUMAN, wrong.stderr)
            self.assertEqual(ledger.read_bytes(), original_ledger)
            book = Notebook(vault)
            try:
                self.assertEqual(book.get_transaction(
                    "CAPTURE-synthetic-assistant-id")["status"], "STARTED")
                self.assertEqual(book.message_count("CAPTURE-synthetic-assistant-id"), 1)
            finally:
                book.close()

    def test_manual_reconcile_rejects_existing_conflicting_assistant(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, ledger, vault, args = _fixture(Path(tmp))
            self.assertEqual(_kill_at("MID_NOTEBOOK", args).returncode, 73)
            original_ledger = ledger.read_bytes()
            book = Notebook(vault)
            try:
                book.append("CAPTURE-synthetic-assistant-id", 1,
                            "ASSISTANT", "conflicting assistant text")
                book.project()
                self.assertTrue(book.verify())
            finally:
                book.close()
            failed = _run_cli(["reconcile-codex", "--ledger", str(ledger),
                "--notebook", str(vault), "--human-source-id", "synthetic-human-id",
                "--assistant-source-id", "synthetic-assistant-id",
                "--confirm-reconcile"])
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual(failed.stdout, "")
            self.assertEqual(ledger.read_bytes(), original_ledger)
            book = Notebook(vault)
            try:
                tx = "CAPTURE-synthetic-assistant-id"
                self.assertEqual(book.get_transaction(tx)["status"], "STARTED")
                self.assertEqual([r["text"] for r in book.db.execute(
                    "SELECT text FROM transcript WHERE tx=? ORDER BY ordinal", (tx,)
                )], [HUMAN, "conflicting assistant text"])
            finally:
                book.close()

    def test_manual_reconcile_rejects_absent_notebook_without_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, ledger, vault, args = _fixture(Path(tmp))
            result = _run_cli(["reconcile-codex", "--ledger", str(ledger),
                "--notebook", str(vault), "--human-source-id", "synthetic-human-id",
                "--assistant-source-id", "synthetic-assistant-id",
                "--confirm-reconcile"])
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")
            self.assertFalse(ledger.exists())
            self.assertFalse(vault.exists())

    def test_abrupt_exit_after_ledger_receipt_before_projection_replays_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, ledger, vault, args = _fixture(Path(tmp))
            original_source = source.read_bytes()
            killed = _kill_at("BEFORE_PROJECTION", args)
            self.assertEqual(killed.returncode, 71, killed.stderr)
            self.assertFalse(killed.stdout)
            self.assertFalse(vault.exists())
            self.assertEqual(verify_ledger(ledger), {"rows": 2, "status": "CHECKPOINTED"})
            self.assertEqual([row["text"] for row in read_ledger(ledger)], [HUMAN, ASSISTANT])
            # Ledger-only status is not proof the Notebook was checkpointed.
            self.assertEqual(capture_status(ledger)["status"], "CHECKPOINTED")
            receipt = ledger.parent / "capture-receipts.jsonl"
            self.assertEqual(stat.S_IMODE(receipt.stat().st_mode), 0o600)
            before = ledger.read_bytes()
            resumed = _run_cli(args)
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            outcome = json.loads(resumed.stdout)
            self.assertEqual(outcome["notebook"],
                             {"status": "CHECKPOINTED", "projected": 1,
                              "skipped": 0, "pending": 0})
            self.assertEqual(ledger.read_bytes(), before)
            self.assertEqual(source.read_bytes(), original_source)
            self._assert_checkpoint(vault)
            repeated = _run_cli(args)
            self.assertEqual(repeated.returncode, 0, repeated.stderr)
            self.assertEqual(json.loads(repeated.stdout)["notebook"]["skipped"], 1)
            self.assertEqual(ledger.read_bytes(), before)
            self._assert_checkpoint(vault)

    def test_abrupt_exit_after_notebook_checkpoint_before_response_skips_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, ledger, vault, args = _fixture(Path(tmp))
            original_source = source.read_bytes()
            killed = _kill_at("AFTER_CHECKPOINT", args)
            self.assertEqual(killed.returncode, 72, killed.stderr)
            self.assertFalse(killed.stdout)
            self.assertEqual(verify_ledger(ledger)["rows"], 2)
            before = ledger.read_bytes()
            self._assert_checkpoint(vault)
            resumed = _run_cli(args)
            self.assertEqual(resumed.returncode, 0, resumed.stderr)
            state = json.loads(resumed.stdout)["notebook"]
            self.assertEqual(state, {"status": "CHECKPOINTED", "projected": 0,
                                     "skipped": 1, "pending": 0})
            self.assertEqual(ledger.read_bytes(), before)
            self.assertEqual(source.read_bytes(), original_source)
            self._assert_checkpoint(vault)

    def test_abrupt_exit_with_started_notebook_transaction_fails_closed_on_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, ledger, vault, args = _fixture(Path(tmp))
            original_source = source.read_bytes()
            killed = _kill_at("MID_NOTEBOOK", args)
            self.assertEqual(killed.returncode, 73, killed.stderr)
            self.assertEqual(verify_ledger(ledger)["rows"], 2)
            before = ledger.read_bytes()
            book = Notebook(vault)
            try:
                tx = book.get_transaction("CAPTURE-synthetic-assistant-id")
                self.assertIsNotNone(tx)
                self.assertEqual(tx["status"], "STARTED")
            finally:
                book.close()
            retried = _run_cli(args)
            self.assertNotEqual(retried.returncode, 0)
            self.assertEqual(retried.stdout, "")
            self.assertIn("failed validation or projection", retried.stderr)
            self.assertNotIn(HUMAN, retried.stderr)
            self.assertNotIn(ASSISTANT, retried.stderr)
            self.assertEqual(ledger.read_bytes(), before)
            self.assertEqual(source.read_bytes(), original_source)
            # Explicit reconciliation required; do not overwrite partial evidence.
            book = Notebook(vault)
            try:
                self.assertEqual(book.get_transaction(
                    "CAPTURE-synthetic-assistant-id")["status"], "STARTED")
            finally:
                book.close()
