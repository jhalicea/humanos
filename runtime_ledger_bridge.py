"""Bridge completed local Notebook transactions into the conversation ledger."""
import os
from pathlib import Path
from conversation_ledger import append_observed_turn, verify_ledger

def record_completed_transaction(book, tx, hcid, human_text, assistant_text):
    path = Path(os.environ.get("HUMANOS_LEDGER_PATH", "var/current-conversation.jsonl"))
    result = append_observed_turn(path, "humanos-local", hcid, tx, human_text, assistant_text)
    result["verification"] = verify_ledger(path)
    result["status"] = "CHECKPOINTED"
    return result
