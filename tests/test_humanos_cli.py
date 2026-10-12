import json

import pytest

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


def test_opt_in_codex_one_turn_import_and_restart_readback(tmp_path, capsys):
    from conversation_ledger import read_ledger, verify_ledger
    from notebook import Notebook

    source, ledger, vault = (tmp_path / "selected-rollout.jsonl",
                             tmp_path / "ledger.jsonl", tmp_path / "notebook")
    human, assistant = "  observed human 🧭\nline two  ", "original answer\n"
    _one_turn_rollout(source, human=human, assistant=assistant)
    args = ["import-codex", "--source", str(source), "--ledger", str(ledger),
            "--notebook", str(vault), "--confirm-observed"]
    main(args)
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "CHECKPOINTED"
    assert result["source"] == "codex-rollout"
    assert result["turns"] == 1
    assert result["ledger"] == {"rows": 2, "status": "CHECKPOINTED"}
    assert result["notebook"]["projected"] == 1
    first = ledger.read_bytes()
    assert [(r["role"], r["text"]) for r in read_ledger(ledger)] == [
        ("HUMAN", human), ("ASSISTANT", assistant)]
    assert verify_ledger(ledger)["status"] == "CHECKPOINTED"

    main(args)
    repeated = json.loads(capsys.readouterr().out)
    assert repeated["status"] == "CHECKPOINTED"
    assert repeated["notebook"]["skipped"] == 1
    assert repeated["notebook"]["projected"] == 0
    assert ledger.read_bytes() == first

    book = Notebook(vault)
    try:
        assert book.verify()
        tx = "CAPTURE-assistant-1"
        assert book.get_transaction(tx)["status"] == "CHECKPOINTED"
        task = book.task(tx)
        assert task["source"] == "codex-rollout"
        assert task["conversation_id"] == "synthetic-session"
        actual = [(r["role"], r["text"]) for r in book.db.execute(
            "SELECT role,text FROM transcript WHERE tx=? ORDER BY ordinal", (tx,))]
        assert actual == [("HUMAN", human), ("ASSISTANT", assistant)]
    finally:
        book.close()


def test_codex_import_requires_explicit_confirmation_and_destinations(tmp_path, capsys):
    source, ledger, vault = (tmp_path / "selected-rollout.jsonl",
                             tmp_path / "ledger.jsonl", tmp_path / "notebook")
    _one_turn_rollout(source)
    argv = ["import-codex", "--source", str(source), "--ledger", str(ledger),
            "--notebook", str(vault)]
    with pytest.raises(SystemExit):
        main(argv)
    assert capsys.readouterr().out == ""
    assert not ledger.exists() and not vault.exists()

    with pytest.raises(SystemExit):
        main(["import-codex", "--confirm-observed", "--ledger", str(ledger),
              "--notebook", str(vault)])
    assert capsys.readouterr().out == ""
    assert not ledger.exists() and not vault.exists()


@pytest.mark.parametrize("case", [
    "two_turns", "second_session", "orphan_assistant", "mismatched_thread",
    "missing_message_id",
])
def test_codex_import_rejects_ambiguous_source_without_side_effects(tmp_path, capsys, case):
    source, ledger, vault = (tmp_path / "selected-rollout.jsonl",
                             tmp_path / "ledger.jsonl", tmp_path / "notebook")
    records = _one_turn_rollout(source)
    if case == "two_turns":
        records.extend([dict(records[1], payload=dict(records[1]["payload"], id="human-2")),
                        dict(records[2], payload=dict(records[2]["payload"], id="assistant-2"))])
    elif case == "second_session":
        records.append({"type": "session_meta", "payload": {"session_id": "another-session"}})
    elif case == "orphan_assistant":
        records.pop(1)
    elif case == "mismatched_thread":
        records[2]["payload"]["thread_id"] = "different-conversation"
    else:
        records[1]["payload"].pop("id")
    source.write_text("\n".join(json.dumps(row) for row in records) + "\n", encoding="utf-8")

    with pytest.raises(SystemExit):
        main(["import-codex", "--source", str(source), "--ledger", str(ledger),
              "--notebook", str(vault), "--confirm-observed"])
    output = capsys.readouterr()
    assert output.out == ""
    assert "Selected Codex import failed" in output.err
    assert "hello 🧭" not in output.err
    assert not ledger.exists() and not vault.exists()
    assert not (tmp_path / "capture-receipts.jsonl").exists()


def test_codex_import_rejects_foreign_ledger_without_mutation(tmp_path, capsys):
    from ledger_capture_adapter import capture_observed_turn

    source, ledger, vault = (tmp_path / "selected-rollout.jsonl",
                             tmp_path / "ledger.jsonl", tmp_path / "notebook")
    _one_turn_rollout(source)
    capture_observed_turn(ledger, "provider-a", "foreign", "t1", "foreign human", "foreign assistant")
    original = ledger.read_bytes()
    with pytest.raises(SystemExit):
        main(["import-codex", "--source", str(source), "--ledger", str(ledger),
              "--notebook", str(vault), "--confirm-observed"])
    assert capsys.readouterr().out == ""
    assert ledger.read_bytes() == original
    assert not vault.exists()
