"""Append-only import of already-observed conversation messages."""

import hashlib
import argparse
import json
import os
import stat
import fcntl
import uuid
from datetime import datetime, timezone
from recovery_ledger import _write_new_file, _fsync_directory, TAIL_SIZE_LIMIT
from contextlib import contextmanager
from io import StringIO
from pathlib import Path


ROLES = {"user": "HUMAN", "assistant": "ASSISTANT"}

@contextmanager
def _ledger_writer(ledger):
    """Enforce one cooperative local writer during read/dedup/append."""
    path = Path(ledger)
    path.parent.mkdir(parents=True, exist_ok=True)
    sidecar = path.with_name(path.name + ".writer.lock")
    # Persistent lock inode: never unlink it or concurrent writers split locks.
    fd = os.open(sidecar, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) & 0o077):
            raise PermissionError("Conversation writer lock must be owner-private")
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield path
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _append_rows(path, rows):
    """Append evidence under a caller-held lock with owner-private file mode."""
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) & 0o077):
            raise PermissionError("Conversation ledger must be owner-private")
        data = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
                       for row in rows).encode("utf-8")
        while data:
            written = os.write(fd, data)
            if written <= 0:
                raise OSError("Conversation ledger write did not advance")
            data = data[written:]
        os.fsync(fd)
    finally:
        os.close(fd)




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


def _messages(source, allow_derived_ids=False, snapshot_bytes=None):
    """Parse an immutable source snapshot when explicitly supplied."""
    conversation_id = None
    if snapshot_bytes is not None and not isinstance(snapshot_bytes, bytes):
        raise ValueError("Observed source snapshot must be bytes")
    stream_source = (Path(source).open(encoding="utf-8") if snapshot_bytes is None
                     else StringIO(snapshot_bytes.decode("utf-8")))
    with stream_source as stream:
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


def import_messages(source, ledger, selected_source_ids=None, allow_derived_ids=False,
                    snapshot_bytes=None):
    """Append unseen source messages; optionally select one explicitly named pair.

    Existing rows are keyed by source/source_id and conflicting duplicates fail
    closed, so a rerun cannot silently change evidence.
    """
    path = Path(ledger)
    path.parent.mkdir(parents=True, exist_ok=True)
    with _ledger_writer(path):
        existing = {}
        if path.exists():
            for row in read_ledger(path):
                key = (row["source"], row["source_id"])
                if key in existing and existing[key] != row:
                    raise ValueError("conflicting ledger duplicate: " + row["source_id"])
                existing[key] = row
        pending = []
        pending_keys = set()
        messages = list(_messages(source, allow_derived_ids=allow_derived_ids,
                                  snapshot_bytes=snapshot_bytes))
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
        _append_rows(path, pending)
        return {"added": len(pending), "total": len(existing) + len(pending)}


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
    with _ledger_writer(path):
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
        _append_rows(path, pending)
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
    with _ledger_writer(path):
        existing = {(item["source"], item["source_id"]): item for item in read_ledger(path)} if path.exists() else {}
        key = (source, source_id)
        if key in existing:
            if existing[key] != row:
                raise ValueError("observed source message changed: " + source_id)
            return {"added": 0, "row": existing[key]}
        _append_rows(path, [row])
        return {"added": 1, "row": row}


def append_conversation_id_correction(ledger, source_id, conversation_id):
    """Append a metadata correction without mutating an earlier evidence row."""
    path = Path(ledger)
    correction = {"source": "codex-rollout", "source_id": source_id,
                  "event_type": "METADATA_CORRECTION",
                  "field": "conversation_id", "value": conversation_id}
    with _ledger_writer(path):
        _append_rows(path, [correction])
    return correction



def _quarantine_torn_conversation_tail(path, raw):
    """Copy final physical tail to a separate durable 0700 forensic artifact.

    Never modify the source ledger. A matching artifact is reused; a
    suspicious preexisting quarantine path causes a hard stop.
    """
    path = Path(path)
    offset = raw.rfind(b"\n") + 1
    tail = raw[offset:]
    if not tail:
        raise ValueError("Expected a nonempty unterminated ledger tail")
    if len(tail) > TAIL_SIZE_LIMIT:
        raise ValueError("Conversation ledger tail too large to quarantine safely")
    root = path.parent / "conversation-quarantine"
    if not root.exists():
        root.mkdir(mode=0o700)
    info = root.lstat()
    if (not stat.S_ISDIR(info.st_mode) or root.is_symlink()
            or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077):
        raise PermissionError("Conversation evidence quarantine directory is not owner-private")
    original_hash = hashlib.sha256(raw).hexdigest()
    final = root / original_hash
    meta = {
        "schema": "humanos-conversation-torn-tail-v1",
        "original_sha256": original_hash,
        "original_bytes": len(raw),
        "valid_prefix_bytes": offset,
        "valid_prefix_sha256": hashlib.sha256(raw[:offset]).hexdigest(),
        "tail_bytes": len(tail),
        "tail_sha256": hashlib.sha256(tail).hexdigest(),
        "classification": "UNTERMINATED_FINAL_RECORD",
        "detected_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    if final.exists() or final.is_symlink():
        existing = final.lstat()
        if (not stat.S_ISDIR(existing.st_mode) or final.is_symlink()
                or existing.st_uid != os.getuid()
                or stat.S_IMODE(existing.st_mode) & 0o077):
            raise PermissionError("Existing conversation quarantine artifact is unsafe")
        prior_tail = (final / "tail.bin").read_bytes()
        prior_meta = json.loads((final / "metadata.json").read_text(encoding="utf-8"))
        if (prior_tail != tail or prior_meta.get("original_sha256") != original_hash
                or prior_meta.get("valid_prefix_bytes") != offset
                or prior_meta.get("tail_sha256") != meta["tail_sha256"]):
            raise ValueError("Existing conversation quarantine evidence conflicts")
    else:
        pending = root / (".pending-" + uuid.uuid4().hex)
        pending.mkdir(mode=0o700)
        try:
            _write_new_file(pending / "tail.bin", tail)
            _write_new_file(pending / "metadata.json",
                            (json.dumps(meta, sort_keys=True) + "\n").encode("utf-8"))
            _fsync_directory(pending)
            # Under the cooperative ledger lock, the quarantine name is
            # content-addressed; never intentionally overwrite an artifact.
            if final.exists() or final.is_symlink():
                raise ValueError("Conversation quarantine was replaced during creation")
            os.rename(pending, final)
            _fsync_directory(root)
        finally:
            if pending.exists():
                # Only our uniquely named staging directory is removed.
                import shutil
                shutil.rmtree(pending)
    if path.read_bytes() != raw:
        raise RuntimeError("Conversation ledger changed during tail preservation")
    return meta


def _read_physical_conversation_rows(raw, path, *, quarantine=True):
    if not raw:
        return []
    if not raw.endswith(b"\n"):
        if quarantine:
            _quarantine_torn_conversation_tail(path, raw)
        raise ValueError("Conversation ledger has an unterminated final record; operator recovery required")
    rows = []
    for line in raw.split(b"\n")[:-1]:
        if not line:
            raise ValueError("Conversation ledger contains a blank physical record")
        value = json.loads(line.decode("utf-8"))
        if not isinstance(value, dict):
            raise ValueError("Conversation ledger record must be a JSON object")
        rows.append(value)
    return rows

def read_ledger(ledger):
    path = Path(ledger)
    return _read_physical_conversation_rows(path.read_bytes(), path)


def verify_ledger(ledger):
    """Read back evidence and fail closed on malformed or unverifiable rows."""
    return _verify_conversation_rows(read_ledger(ledger))


def _verify_conversation_rows(rows):
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


def export_verified_conversation_prefix(ledger, destination, expected_sha256, *, confirm=False):
    """Owner-confirmed, non-destructive salvage to a NEW private evidence file.

    Never rewrites a torn ledger, advances receipts, or projects Notebook data.
    """
    source, target = Path(ledger), Path(destination)
    if confirm is not True:
        raise PermissionError("Explicit owner approval required to export a ledger prefix")
    if (not source.is_absolute() or not target.is_absolute() or source == target
            or source.is_symlink() or target.is_symlink()
            or target.parent != source.parent or target.exists()):
        raise ValueError("Export requires a new absolute nonlinked file beside the original ledger")
    parent = source.parent
    info = parent.lstat()
    if (not stat.S_ISDIR(info.st_mode) or parent.is_symlink()
            or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077):
        raise PermissionError("Conversation ledger prefix export parent must be owner-private")
    if (not isinstance(expected_sha256, str) or len(expected_sha256) != 64):
        raise ValueError("Exact SHA-256 of original torn evidence is required")
    with _ledger_writer(source):
        raw = source.read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected_sha256:
            raise ValueError("Original ledger changed since recovery was approved")
        if not raw or raw.endswith(b"\n"):
            raise ValueError("No torn final physical record to recover")
        _quarantine_torn_conversation_tail(source, raw)
        prefix = raw[:raw.rfind(b"\n") + 1]
        if not prefix:
            raise ValueError("No complete evidence rows to export")
        rows = _read_physical_conversation_rows(prefix, source, quarantine=False)
        _verify_conversation_rows(rows)
        _write_new_file(target, prefix)
        _fsync_directory(target.parent)
        if target.read_bytes() != prefix:
            raise RuntimeError("Exported conversation prefix did not read back exactly")
    return {"status": "EXPORTED_NOT_PROMOTED", "rows": len(rows),
            "source_sha256": expected_sha256,
            "export_sha256": hashlib.sha256(prefix).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description="Import newly observed Codex turns into a local JSONL ledger")
    parser.add_argument("source", type=Path)
    parser.add_argument("ledger", type=Path)
    args = parser.parse_args()
    print(json.dumps(import_messages(args.source, args.ledger), sort_keys=True))


if __name__ == "__main__":
    main()
