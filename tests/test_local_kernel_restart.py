import subprocess
import sys


def test_completed_turn_replay_after_process_restart_is_byte_stable(tmp_path):
    ledger = tmp_path / "conversation.jsonl"
    command = [sys.executable, "humanos.py", "turn", "--ledger", str(ledger),
               "--conversation-id", "restart-c", "--turn-id", "restart-t",
               "--human", "hello", "--assistant", "hi"]
    first = subprocess.run(command, check=True, capture_output=True, text=True)
    before = ledger.read_bytes()
    second = subprocess.run(command, check=True, capture_output=True, text=True)
    assert '"added": 2' in first.stdout
    assert '"added": 0' in second.stdout
    assert ledger.read_bytes() == before
