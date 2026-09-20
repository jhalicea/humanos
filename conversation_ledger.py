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


def _messages(source):
    conversation_id = None
    with Path(source).open(encoding="utf-8") as stream:
        for line in stream:
            record = json.loads(line)
            payload = record.get("payload", {})
            if record.get("type") == "session_meta":
                conversation_id = payload.get("session_id") or payload.get("id")
            if record.get("type") != "response_item" or payload.get("role") not in ROLES:
                continue
            text = _text(payload)
            if not isinstance(payload.get("id"), str) or not text:
                continue
            yield {
                "source": "codex-rollout",
                "source_id": payload["id"],
                "conversation_id": payload.get("thread_id") or conversation_id,
                "role": ROLES[payload["role"]],
                "text": text,
                "timestamp": record.get("timestamp"),
            }


def import_messages(source, ledger):
    """Append unseen source messages; return added and total counts.

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
    for row in _messages(source):
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
