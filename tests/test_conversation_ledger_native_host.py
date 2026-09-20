import json
import struct
import subprocess
import sys

from conversation_ledger import read_ledger


def frame(value):
    payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
    return struct.pack("<I", len(payload)) + payload


def test_native_host_writes_browser_event_to_ledger(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    event = {"source": "chatgpt", "conversation_id": "/c/demo",
             "turn_id": "msg-1", "role": "assistant", "text": "done"}
    proc = subprocess.run([sys.executable, "conversation_ledger_native_host.py",
                           "--ledger", str(ledger)], input=frame(event), capture_output=True)
    assert proc.returncode == 0
    response_size = struct.unpack("<I", proc.stdout[:4])[0]
    response = json.loads(proc.stdout[4:4 + response_size])
    assert response["status"] == "CHECKPOINTED"
    assert read_ledger(ledger)[0]["text"] == "done"
