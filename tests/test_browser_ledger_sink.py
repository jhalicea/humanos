import json

from browser_ledger_sink import accept_browser_event
from conversation_ledger import read_ledger


def test_historical_browser_events_append_idempotently(tmp_path):
    ledger = tmp_path / "ledger.jsonl"
    event = {"source": "chatgpt", "conversation_id": "/c/demo",
             "turn_id": "msg-1", "role": "human", "text": "hello"}
    first = accept_browser_event(event, ledger)
    second = accept_browser_event(event, ledger)
    assert first["added"] == 1
    assert second["added"] == 0
    assert second["status"] == "CHECKPOINTED"
    assert read_ledger(ledger)[0]["role"] == "HUMAN"
    assert len(ledger.read_text(encoding="utf-8").splitlines()) == 1
