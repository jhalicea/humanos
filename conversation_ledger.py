"""Append-only import of already-observed conversation messages."""

import hashlib
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
    with Path(source).open(encoding="utf-8") as stream:
        for line in stream:
            record = json.loads(line)
            payload = record.get("payload", {})
            if record.get("type") != "response_item" or payload.get("role") not in ROLES:
                continue
            text = _text(payload)
            if not isinstance(payload.get("id"), str) or not text:
                continue
            yield {
                "source": "codex-rollout",
                "source_id": payload["id"],
                "conversation_id": payload.get("thread_id"),
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
    added = 0
    with path.open("a", encoding="utf-8") as stream:
        for row in _messages(source):
            key = (row["source"], row["source_id"])
            if key in existing:
                if existing[key] != row:
                    raise ValueError("source message changed: " + row["source_id"])
                continue
            row["content_digest"] = hashlib.sha256(row["text"].encode("utf-8")).hexdigest()
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            existing[key] = row
            added += 1
    return {"added": added, "total": len(existing)}


def read_ledger(ledger):
    path = Path(ledger)
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]
