"""Capture one already-observed provider turn into Notebook and JSONL evidence."""

from pathlib import Path

from conversation_capture import UniversalConversationCapture
from conversation_ledger import append_observed_turn, verify_ledger


def capture_host_turn(book, ledger, hcid, source, conversation_id, turn_id,
                      human_text, assistant_text):
    """Write the same exact turn to both durable provenance surfaces."""
    tx = UniversalConversationCapture(book, source).capture_turn(
        hcid, conversation_id, turn_id, human_text, assistant_text
    )
    result = append_observed_turn(
        Path(ledger), source, conversation_id, turn_id, human_text, assistant_text
    )
    result["verification"] = verify_ledger(ledger)
    result["notebook_transaction"] = tx
    result["status"] = "CHECKPOINTED"
    return result
