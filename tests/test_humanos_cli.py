import json

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from humanos import main


def test_status_command_reads_kernel_state(tmp_path, capsys):
    ledger = tmp_path / "ledger.jsonl"
    main(["status", "--ledger", str(ledger)])
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "PENDING"


def test_turn_command_is_idempotent(tmp_path, capsys):
    ledger = tmp_path / "ledger.jsonl"
    args = ["turn", "--ledger", str(ledger), "--conversation-id", "c",
            "--turn-id", "t", "--human", "hello", "--assistant", "hi"]
    main(args)
    first = json.loads(capsys.readouterr().out)
    main(args)
    second = json.loads(capsys.readouterr().out)
    assert first["added"] == 2
    assert second["added"] == 0


def test_project_command_is_idempotent(tmp_path, capsys):
    ledger = tmp_path / "ledger.jsonl"
    notebook = tmp_path / "notebook"
    args = ["turn", "--ledger", str(ledger), "--conversation-id", "c",
            "--turn-id", "t", "--human", "hello", "--assistant", "hi"]
    main(args)
    capsys.readouterr()
    main(["project", "--ledger", str(ledger), "--notebook", str(notebook)])
    first = json.loads(capsys.readouterr().out)
    main(["project", "--ledger", str(ledger), "--notebook", str(notebook)])
    second = json.loads(capsys.readouterr().out)
    assert first["projected"] == 1
    assert second["skipped"] == 1


def test_verify_command_reports_ledger_and_capture(tmp_path, capsys):
    ledger = tmp_path / "ledger.jsonl"
    main(["turn", "--ledger", str(ledger), "--conversation-id", "c",
          "--turn-id", "t", "--human", "hello", "--assistant", "hi"])
    capsys.readouterr()
    main(["verify", "--ledger", str(ledger)])
    result = json.loads(capsys.readouterr().out)
    assert result["ledger"]["status"] == "CHECKPOINTED"


def _one_turn_rollout(source, *, conversation="synthetic-session", human="  hello 🧭  ", assistant="exact answer\\n"):
    records = [
        {"type": "session_meta", "payload": {"session_id": conversation}},
        {"type": "response_item", "payload": {"type": "message", "id": "human-1", "role": "user",
            "content": [{"type": "input_text", "text": human}]}},
        {"type": "response_item", "payload": {"type": "message", "id": "assistant-1", "role": "assistant",
            "content": [{"type": "output_text", "text": assistant}]}},
    ]
    source.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in records) + "\n", encoding="utf-8")
    return records


class CodexImportCliTests(unittest.TestCase):
    @staticmethod
    def run_cli(args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                main(args)
                code = 0
            except SystemExit as error:
                code = error.code
        return code, out.getvalue(), err.getvalue()

    @staticmethod
    def setup_paths(root):
        return (root / "selected-rollout.jsonl", root / "ledger.jsonl", root / "notebook")

    @staticmethod
    def command(source, ledger, vault, *, confirm=True):
        args = ["import-codex", "--source", str(source), "--ledger", str(ledger),
                "--notebook", str(vault)]
        if confirm:
            args.append("--confirm-observed")
        return args

    def test_selected_codex_turn_import_idempotent_restart_readback(self):
        from conversation_ledger import read_ledger, verify_ledger
        from notebook import Notebook

        with tempfile.TemporaryDirectory() as folder:
            source, ledger, vault = self.setup_paths(Path(folder))
            human, assistant = "  observed human 🧭\\nline two  ", "original answer\\n"
            _one_turn_rollout(source, human=human, assistant=assistant)
            args = self.command(source, ledger, vault)
            code, stdout, stderr = self.run_cli(args)
            self.assertEqual(code, 0, stderr)
            result = json.loads(stdout)
            self.assertEqual(result["status"], "CHECKPOINTED")
            self.assertEqual(result["source"], "codex-rollout")
            self.assertEqual(result["turns"], 1)
            self.assertEqual(result["ledger"], {"rows": 2, "status": "CHECKPOINTED"})
            self.assertEqual(result["notebook"]["projected"], 1)
            first = ledger.read_bytes()
            self.assertEqual([(r["role"], r["text"]) for r in read_ledger(ledger)],
                             [("HUMAN", human), ("ASSISTANT", assistant)])
            self.assertEqual(verify_ledger(ledger)["status"], "CHECKPOINTED")

            code, stdout, stderr = self.run_cli(args)
            self.assertEqual(code, 0, stderr)
            repeated = json.loads(stdout)
            self.assertEqual(repeated["status"], "CHECKPOINTED")
            self.assertEqual(repeated["notebook"]["skipped"], 1)
            self.assertEqual(repeated["notebook"]["projected"], 0)
            self.assertEqual(ledger.read_bytes(), first)

            book = Notebook(vault)
            try:
                self.assertTrue(book.verify())
                tx = "CAPTURE-assistant-1"
                self.assertEqual(book.get_transaction(tx)["status"], "CHECKPOINTED")
                state = book.task(tx)
                self.assertEqual(state["source"], "codex-rollout")
                self.assertEqual(state["conversation_id"], "synthetic-session")
                actual = [(r["role"], r["text"]) for r in book.db.execute(
                    "SELECT role,text FROM transcript WHERE tx=? ORDER BY ordinal", (tx,))]
                self.assertEqual(actual, [("HUMAN", human), ("ASSISTANT", assistant)])
            finally:
                book.close()

    def test_selection_and_owner_confirmation_required_before_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            source, ledger, vault = self.setup_paths(Path(folder))
            _one_turn_rollout(source)
            for args in (
                self.command(source, ledger, vault, confirm=False),
                ["import-codex", "--confirm-observed", "--ledger", str(ledger),
                 "--notebook", str(vault)],
                self.command(source, ledger.relative_to(Path(folder)), vault),
            ):
                with self.subTest(args=args):
                    code, stdout, _ = self.run_cli(args)
                    self.assertNotEqual(code, 0)
                    self.assertEqual(stdout, "")
                    self.assertFalse(ledger.exists())
                    self.assertFalse(vault.exists())

    def test_ambiguous_rollout_rejected_without_vault_or_ledger(self):
        for case in ("two_turns", "second_session", "orphan_assistant",
                     "mismatched_thread", "missing_message_id"):
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory() as folder:
                    root = Path(folder)
                    source, ledger, vault = self.setup_paths(root)
                    records = _one_turn_rollout(source)
                    if case == "two_turns":
                        records.extend([
                            dict(records[1], payload=dict(records[1]["payload"], id="human-2")),
                            dict(records[2], payload=dict(records[2]["payload"], id="assistant-2")),
                        ])
                    elif case == "second_session":
                        records.append({"type": "session_meta", "payload": {"session_id": "another"}})
                    elif case == "orphan_assistant":
                        records.pop(1)
                    elif case == "mismatched_thread":
                        records[2]["payload"]["thread_id"] = "different"
                    else:
                        records[1]["payload"].pop("id")
                    source.write_text("\n".join(json.dumps(row) for row in records) + "\n",
                                      encoding="utf-8")
                    code, stdout, stderr = self.run_cli(self.command(source, ledger, vault))
                    self.assertNotEqual(code, 0)
                    self.assertEqual(stdout, "")
                    self.assertIn("Selected Codex import failed", stderr)
                    self.assertNotIn("hello 🧭", stderr)
                    self.assertFalse(ledger.exists())
                    self.assertFalse(vault.exists())
                    self.assertFalse((root / "capture-receipts.jsonl").exists())

    def test_public_destination_denied_before_capture(self):
        import os
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "selected-rollout.jsonl"
            _one_turn_rollout(source)
            shared = root / "shared"
            shared.mkdir()
            os.chmod(shared, 0o755)
            ledger, vault = shared / "ledger.jsonl", shared / "notebook"
            code, stdout, stderr = self.run_cli(self.command(source, ledger, vault))
            self.assertNotEqual(code, 0)
            self.assertEqual(stdout, "")
            self.assertIn("Selected Codex import failed", stderr)
            self.assertFalse(ledger.exists())
            self.assertFalse(vault.exists())
            self.assertFalse((shared / "capture-receipts.jsonl").exists())

    def test_foreign_ledger_rejected_without_mutation(self):
        from ledger_capture_adapter import capture_observed_turn

        with tempfile.TemporaryDirectory() as folder:
            source, ledger, vault = self.setup_paths(Path(folder))
            _one_turn_rollout(source)
            capture_observed_turn(ledger, "provider-a", "foreign", "t1",
                                  "foreign human", "foreign assistant")
            initial = ledger.read_bytes()
            code, stdout, _ = self.run_cli(self.command(source, ledger, vault))
            self.assertNotEqual(code, 0)
            self.assertEqual(stdout, "")
            self.assertEqual(ledger.read_bytes(), initial)
            self.assertFalse(vault.exists())
