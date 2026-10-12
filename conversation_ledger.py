"""Append-only import of already-observed conversation messages."""

import hashlib
import argparse
import json
from pathlib import Path


ROLES = {"user": "HUMAN", "assistant": "ASSISTANT"}


def _text(payload):
    parts = []
    for item in payload.get("content", []):
        if item.get("type") in {"text", "input_text", "output_text"} and isinstance(item.get("text"), str):
            parts.append(item["text"])
    return "".join(parts)


def _codex_source_id(record, line_number, conversation_id):
    """Distinguish a genuine source ID from a stable *local* record reference."""
    payload = record["payload"]
    provider_id = payload.get("id")
    if isinstance(provider_id, str) and provider_id:
        return provider_id, "PROVIDER_MESSAGE_ID"
    # A local record fingerprint is not a provider-issued message ID.
    # Canonical JSON makes whitespace-only formatting changes harmless;
    # source session, original line and entire record bind evidence position.
    canonical = json.dumps(record, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":"))
    fingerprint = hashlib.sha256(
        ("codex-local-record-v1\\n" + str(conversation_id) + "\\n"
         + str(line_number) + "\\n" + canonical).encode("utf-8")
    ).hexdigest()
    return "local-record-v1:" + fingerprint, "LOCAL_DERIVED_RECORD_V1"


def _messages(source, allow_derived_ids=False):
    conversation_id = None
    with Path(source).open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            record = json.loads(line)
            payload = record.get("payload", {})
            if record.get("type") == "session_meta":
                conversation_id = payload.get("session_id") or payload.get("id")
            if record.get("type") != "response_item" or payload.get("role") not in ROLES:
                continue
            text = _text(payload)
            if not text:
                continue
            if not isinstance(payload.get("id"), str) or not payload.get("id"):
                if not allow_derived_ids:
                    continue
            source_id, origin = _codex_source_id(record, line_number, conversation_id)
            row = {
                "source": "codex-rollout",
                "source_id": source_id,
                "conversation_id": payload.get("thread_id") or conversation_id,
                "role": ROLES[payload["role"]],
                "text": text,
                "timestamp": record.get("timestamp"),
            }
            if origin == "LOCAL_DERIVED_RECORD_V1":
                row["source_id_origin"] = origin
                row["source_line"] = line_number
            yield row


def import_messages(source, ledger, selected_source_ids=None, allow_derived_ids=False):
    """Append unseen source messages; optionally select one explicitly named pair.

    Existing rows are keyed by source/source_id and conflicting duplicates fail
    closed, so a rerun cannot silently change evidence.
    """
    path = Path(ledger)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if path.exists():
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                row = json.loads(line)
                key = (row["source"], row["source_id"])
                if key in existing and existing[key] != row:
                    raise ValueError("conflicting ledger duplicate: " + row["source_id"])
                existing[key] = row
    pending = []
    pending_keys = set()
    messages = list(_messages(source, allow_derived_ids=allow_derived_ids))
    if selected_source_ids is not None:
        if (not isinstance(selected_source_ids, (tuple, list))
                or len(selected_source_ids) != 2
                or any(not isinstance(item, str) or not item for item in selected_source_ids)
                or selected_source_ids[0] == selected_source_ids[1]):
            raise ValueError("Explicit source selection requires two distinct message IDs")
        messages = [row for row in messages if row["source_id"] in selected_source_ids]
        if (len(messages) != 2
                or [row["source_id"] for row in messages] != list(selected_source_ids)
                or [row["role"] for row in messages] != ["HUMAN", "ASSISTANT"]):
            raise ValueError("Explicit selected messages are absent, duplicated or unordered")
    for row in messages:
        if not row.get("conversation_id"):
            raise ValueError("source message has no conversation ID: " + row["source_id"])
        row["content_digest"] = hashlib.sha256(row["text"].encode("utf-8")).hexdigest()
        key = (row["source"], row["source_id"])
        if key in existing:
            if existing[key] != row:
                raise ValueError("source message changed: " + row["source_id"])
            continue
        if key in pending_keys:
            raise ValueError("duplicate source message: " + row["source_id"])
        pending_keys.add(key)
        pending.append(row)
    added = 0
    with path.open("a", encoding="utf-8") as stream:
        for row in pending:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            existing[(row["source"], row["source_id"])] = row
            added += 1
    return {"added": added, "total": len(existing)}


def append_observed_turn(ledger, source, conversation_id, turn_id, human_text, assistant_text,
                         human_source_id=None, assistant_source_id=None):
    """Append one already-observed provider turn as two ledger evidence rows."""
    values = ((human_source_id or turn_id + ":HUMAN", "HUMAN", human_text),
              (assistant_source_id or turn_id + ":ASSISTANT", "ASSISTANT", assistant_text))
    for source_id, role, text in values:
        if not isinstance(source_id, str) or not source_id or not isinstance(text, str) or not text:
            raise ValueError("observed turn fields must be nonempty")
    path = Path(ledger)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = {(row["source"], row["source_id"]): row for row in read_ledger(path)} if path.exists() else {}
    pending = []
    for source_id, role, text in values:
        row = {"source": source, "source_id": source_id, "conversation_id": conversation_id,
               "role": role, "text": text, "timestamp": None,
               "content_digest": hashlib.sha256(text.encode("utf-8")).hexdigest()}
        key = (source, source_id)
        if key in existing:
            if existing[key] != row:
                raise ValueError("observed source message changed: " + source_id)
            continue
        pending.append(row)
    with path.open("a", encoding="utf-8") as stream:
        for row in pending:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return {"added": len(pending), "total": len(existing) + len(pending)}


def append_observed_message(ledger, source, conversation_id, turn_id, role, text,
                            source_id=None, timestamp=None):
    """Append one exact message delivered by the local browser observer."""
    if role not in ("HUMAN", "ASSISTANT") or not isinstance(text, str) or not text:
        raise ValueError("observed message role/text is invalid")
    if not isinstance(conversation_id, str) or not conversation_id:
        raise ValueError("observed message has no conversation ID")
    source_id = source_id or f"{turn_id}:{role}"
    row = {"source": source, "source_id": source_id,
           "conversation_id": conversation_id, "role": role, "text": text,
           "timestamp": timestamp,
           "content_digest": hashlib.sha256(text.encode("utf-8")).hexdigest()}
    path = Path(ledger)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = {(item["source"], item["source_id"]): item for item in read_ledger(path)} if path.exists() else {}
    key = (source, source_id)
    if key in existing:
        if existing[key] != row:
            raise ValueError("observed source message changed: " + source_id)
        return {"added": 0, "row": existing[key]}
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return {"added": 1, "row": row}


def append_conversation_id_correction(ledger, source_id, conversation_id):
    """Append a metadata correction without mutating an earlier evidence row."""
    path = Path(ledger)
    correction = {"source": "codex-rollout", "source_id": source_id,
                  "event_type": "METADATA_CORRECTION",
                  "field": "conversation_id", "value": conversation_id}
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(correction, ensure_ascii=False, sort_keys=True) + "\n")
    return correction


def read_ledger(ledger):
    path = Path(ledger)
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def verify_ledger(ledger):
    """Read back evidence and fail closed on malformed or unverifiable rows."""
    rows = read_ledger(ledger)
    evidence = [row for row in rows if row.get("event_type") != "METADATA_CORRECTION"]
    seen = set()
    for row in evidence:
        key = (row.get("source"), row.get("source_id"))
        if not all(isinstance(value, str) and value for value in key):
            raise ValueError("ledger row has no source identity")
        if key in seen:
            raise ValueError("duplicate ledger identity: " + row["source_id"])
        seen.add(key)
        if row.get("role") not in ("HUMAN", "ASSISTANT") or not row.get("conversation_id"):
            raise ValueError("ledger row has incomplete conversation metadata: " + row["source_id"])
        if hashlib.sha256(row["text"].encode("utf-8")).hexdigest() != row.get("content_digest"):
            raise ValueError("ledger digest mismatch: " + row["source_id"])
    return {"rows": len(evidence), "status": "CHECKPOINTED"}


def main():
    parser = argparse.ArgumentParser(description="Import newly observed Codex turns into a local JSONL ledger")
    parser.add_argument("source", type=Path)
    parser.add_argument("ledger", type=Path)
    args = parser.parse_args()
    print(json.dumps(import_messages(args.source, args.ledger), sort_keys=True))


if __name__ == "__main__":
    main()
