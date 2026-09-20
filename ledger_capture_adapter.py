"""Ledger sink for turns observed by the existing conversation adapter."""

from conversation_ledger import append_observed_turn, verify_ledger


def capture_observed_turn(ledger, source, conversation_id, turn_id, human_text, assistant_text,
                          human_source_id=None, assistant_source_id=None):
    result = append_observed_turn(ledger, source, conversation_id, turn_id, human_text, assistant_text,
                                  human_source_id, assistant_source_id)
    result["verification"] = verify_ledger(ledger)
    result["status"] = "CHECKPOINTED"
    return result
