"""Bridge completed local Notebook transactions into the conversation ledger."""
import os
import json
from datetime import datetime, timezone
from pathlib import Path
from conversation_ledger import append_observed_turn, verify_ledger
from ledger_notebook_projection import project_all_pairs

def record_completed_transaction(book, tx, hcid, human_text, assistant_text):
    configured = os.environ.get("HUMANOS_LEDGER_PATH")
    path = Path(configured) if configured else Path(book.root).parent / "runtime" / "current-conversation.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    result = append_observed_turn(path, "humanos-local", hcid, tx, human_text, assistant_text)
    result["verification"] = verify_ledger(path)
    result["projection"] = project_all_pairs(path, book=book)
    receipt = path.parent / "runtime-capture-receipts.jsonl"
    with receipt.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({"captured_at": datetime.now(timezone.utc).isoformat(), "conversation_id": hcid, "transaction": tx, "status": "CHECKPOINTED", "ledger_rows": result["verification"]["rows"]}, sort_keys=True) + "\n")
    result["status"] = "CHECKPOINTED"
    return result
