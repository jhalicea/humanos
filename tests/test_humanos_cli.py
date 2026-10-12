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
                     "mismatched_thread", "missing_message_content"):
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
                        records[1]["payload"]["content"] = [{"type": "unrecognized"}]
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


    def test_explicit_pair_selection_in_larger_rollout_preserves_original_source(self):
        from conversation_ledger import read_ledger
        from notebook import Notebook
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, ledger, vault = self.setup_paths(root)
            records = _one_turn_rollout(source)
            records.extend([
                {"type": "response_item", "payload": {"id": "human-2", "role": "user",
                    "content": [{"type": "input_text", "text": "second human 🧭"}]}},
                {"type": "response_item", "payload": {"id": "assistant-2", "role": "assistant",
                    "content": [{"type": "output_text", "text": "second assistant."}]}},
            ])
            source.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in records) + "\n",
                              encoding="utf-8")
            source_bytes = source.read_bytes()
            args = self.command(source, ledger, vault) + [
                "--human-source-id", "human-2", "--assistant-source-id", "assistant-2",
            ]
            code, out, err = self.run_cli(args)
            self.assertEqual(code, 0, err)
            self.assertEqual(json.loads(out)["notebook"]["projected"], 1)
            saved = read_ledger(ledger)
            self.assertEqual([(x["source_id"], x["text"]) for x in saved],
                             [("human-2", "second human 🧭"), ("assistant-2", "second assistant.")])
            original_ledger = ledger.read_bytes()
            code, out, err = self.run_cli(args)
            self.assertEqual(code, 0, err)
            self.assertEqual(json.loads(out)["notebook"]["skipped"], 1)
            self.assertEqual(ledger.read_bytes(), original_ledger)
            self.assertEqual(source.read_bytes(), source_bytes)
            book = Notebook(vault)
            try:
                self.assertTrue(book.verify())
                self.assertEqual(book.get_transaction("CAPTURE-assistant-2")["input"],
                                 "second human 🧭")
                self.assertIsNone(book.get_transaction("CAPTURE-assistant-1"))
            finally:
                book.close()

    def test_explicit_pair_selection_must_be_complete_and_consecutive(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, ledger, vault = self.setup_paths(root)
            records = _one_turn_rollout(source)
            records += [
                {"type": "response_item", "payload": {"id": "human-2", "role": "user",
                    "content": [{"type": "input_text", "text": "second human"}]}},
                {"type": "response_item", "payload": {"id": "assistant-2", "role": "assistant",
                    "content": [{"type": "output_text", "text": "second reply"}]}},
            ]
            source.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
            for selection in (
                [],
                ["--human-source-id", "human-1"],
                ["--human-source-id", "human-1", "--assistant-source-id", "assistant-2"],
                ["--human-source-id", "missing", "--assistant-source-id", "assistant-2"],
                ["--human-source-id", "assistant-2", "--assistant-source-id", "human-2"],
                ["--human-source-id", "human-2", "--assistant-source-id", "human-2"],
            ):
                with self.subTest(selection=selection):
                    code, out, err = self.run_cli(self.command(source, ledger, vault) + selection)
                    self.assertNotEqual(code, 0)
                    self.assertEqual(out, "")
                    self.assertIn("Selected Codex import failed", err)
                    self.assertFalse(ledger.exists())
                    self.assertFalse(vault.exists())
                    self.assertFalse((root / "capture-receipts.jsonl").exists())

    def test_codex_inspection_reports_ids_without_original_message_text(self):
        with tempfile.TemporaryDirectory() as folder:
            source, ledger, vault = self.setup_paths(Path(folder))
            records = _one_turn_rollout(source, human="PRIVATE human text",
                                        assistant="PRIVATE assistant text")
            records.extend([
                {"type": "response_item", "payload": {"id": "human-2", "role": "user",
                    "content": [{"type": "input_text", "text": "secret second human"}]}},
                {"type": "response_item", "payload": {"id": "assistant-2", "role": "assistant",
                    "content": [{"type": "output_text", "text": "secret second answer"}]}},
            ])
            source.write_text("\n".join(json.dumps(x) for x in records) + "\n", encoding="utf-8")
            code, out, err = self.run_cli(["inspect-codex", "--source", str(source)])
            self.assertEqual(code, 0, err)
            self.assertNotIn("PRIVATE", out)
            self.assertNotIn("secret second", out)
            report = json.loads(out)
            self.assertEqual(report["status"], "UNVERIFIED_METADATA_ONLY")
            self.assertEqual(report["message_count"], 4)
            self.assertEqual([(x["role"], x["source_id"]) for x in report["messages"]],
                             [("HUMAN", "human-1"), ("ASSISTANT", "assistant-1"),
                              ("HUMAN", "human-2"), ("ASSISTANT", "assistant-2")])
            self.assertFalse(ledger.exists())
            self.assertFalse(vault.exists())

    def test_realistic_idless_codex_record_selection_and_exact_provenance(self):
        """OpenAI Codex rollout fixtures omit message IDs on response_item."""
        from conversation_ledger import read_ledger
        from notebook import Notebook
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, ledger, vault = self.setup_paths(root)
            records = [
                {"type": "session_meta", "payload": {"id": "codex-idless-synthetic"}},
                {"type": "response_item", "payload": {"type": "message", "role": "user",
                    "content": [{"type": "input_text", "text": "idless human 🧭"}]}},
                {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "turn-synthetic"}},
                {"type": "response_item", "payload": {"type": "message", "role": "assistant",
                    "content": [{"type": "output_text", "text": "idless answer"}]}},
                {"type": "event_msg", "payload": {"type": "task_complete", "turn_id": "turn-synthetic"}},
            ]
            source.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
            before_source = source.read_bytes()
            code, out, err = self.run_cli(["inspect-codex", "--source", str(source)])
            self.assertEqual(code, 0, err)
            report = json.loads(out)
            self.assertEqual(report["message_count"], 2)
            self.assertNotIn("idless human", out)
            self.assertNotIn("idless answer", out)
            ids = [row["source_id"] for row in report["messages"]]
            self.assertEqual(len(set(ids)), 2)
            self.assertTrue(all(x.startswith("local-record-v1:") for x in ids))
            self.assertTrue(all(x["source_id_origin"] == "LOCAL_DERIVED_RECORD_V1"
                                for x in report["messages"]))

            args = self.command(source, ledger, vault) + [
                "--human-source-id", ids[0], "--assistant-source-id", ids[1],
            ]
            code, result_text, err = self.run_cli(args)
            self.assertEqual(code, 0, err)
            self.assertEqual(json.loads(result_text)["notebook"]["projected"], 1)
            self.assertEqual(source.read_bytes(), before_source)
            saved = read_ledger(ledger)
            self.assertEqual([row["source_id"] for row in saved], ids)
            self.assertEqual([row["source_line"] for row in saved], [2, 4])
            self.assertEqual([row["source_id_origin"] for row in saved],
                             ["LOCAL_DERIVED_RECORD_V1"] * 2)
            self.assertEqual([row["text"] for row in saved],
                             ["idless human 🧭", "idless answer"])
            first_ledger = ledger.read_bytes()
            code, result_text, err = self.run_cli(args)
            self.assertEqual(code, 0, err)
            self.assertEqual(json.loads(result_text)["notebook"]["skipped"], 1)
            self.assertEqual(ledger.read_bytes(), first_ledger)
            book = Notebook(vault)
            try:
                self.assertTrue(book.verify())
                tx = "CAPTURE-" + ids[1]
                self.assertEqual(book.get_transaction(tx)["input"], "idless human 🧭")
                self.assertEqual(book.task(tx)["assistant_source_id"], ids[1])
            finally:
                book.close()

    def test_local_record_reference_invalidated_by_source_edit(self):
        with tempfile.TemporaryDirectory() as folder:
            source, ledger, vault = self.setup_paths(Path(folder))
            records = [
                {"type": "session_meta", "payload": {"id": "synthetic-session"}},
                {"type": "response_item", "payload": {"type": "message", "role": "user",
                    "content": [{"type": "input_text", "text": "original"}]}},
                {"type": "response_item", "payload": {"type": "message", "role": "assistant",
                    "content": [{"type": "output_text", "text": "answer"}]}},
            ]
            source.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
            code, out, err = self.run_cli(["inspect-codex", "--source", str(source)])
            self.assertEqual(code, 0, err)
            ids = [row["source_id"] for row in json.loads(out)["messages"]]
            records[1]["payload"]["content"][0]["text"] = "changed"
            source.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
            code, out, err = self.run_cli(self.command(source, ledger, vault) + [
                "--human-source-id", ids[0], "--assistant-source-id", ids[1],
            ])
            self.assertNotEqual(code, 0)
            self.assertEqual(out, "")
            self.assertFalse(ledger.exists())
            self.assertFalse(vault.exists())

    def test_codex_inspection_denies_implicit_source_discovery(self):
        with tempfile.TemporaryDirectory() as folder:
            source, ledger, vault = self.setup_paths(Path(folder))
            _one_turn_rollout(source)
            code, stdout, stderr = self.run_cli(["inspect-codex"])
            self.assertNotEqual(code, 0)
            self.assertEqual(stdout, "")
            self.assertFalse(ledger.exists())
            self.assertFalse(vault.exists())

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
