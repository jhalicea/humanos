"""Translate the historical local browser observer event into ledger evidence."""

from conversation_ledger import append_observed_message, verify_ledger


def accept_browser_event(event, ledger):
    """Accept one native-messaging event; no provider plugin or model is involved."""
    required = {"source", "conversation_id", "turn_id", "role", "text"}
    if not isinstance(event, dict) or set(event) != required:
        raise ValueError("malformed browser capture event")
    role = {"human": "HUMAN", "assistant": "ASSISTANT"}.get(event["role"])
    if role is None:
        raise ValueError("unsupported browser capture role")
    result = append_observed_message(ledger, event["source"], event["conversation_id"],
                                     event["turn_id"], role, event["text"])
    result["verification"] = verify_ledger(ledger)
    result["status"] = "CHECKPOINTED"
    return result
