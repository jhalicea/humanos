from local_kernel_capture import capture_turn
from conversation_ledger import read_ledger, verify_ledger


def test_local_kernel_turn_is_restart_safe(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    first = capture_turn(ledger, "local-1", "turn-1", "hello", "hi")
    before = ledger.read_bytes()
    second = capture_turn(ledger, "local-1", "turn-1", "hello", "hi")
    assert first["added"] == 2
    assert second["added"] == 0
    assert ledger.read_bytes() == before
    assert verify_ledger(ledger)["status"] == "CHECKPOINTED"
    assert [row["role"] for row in read_ledger(ledger)] == ["HUMAN", "ASSISTANT"]
