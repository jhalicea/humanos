import json

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
