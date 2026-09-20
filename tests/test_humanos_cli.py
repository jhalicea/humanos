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
