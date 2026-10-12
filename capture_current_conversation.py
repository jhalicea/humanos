"""Explicit, local capture command for the current observed Codex session."""

import argparse
import hashlib
import json
import os
import stat
import fcntl
from datetime import datetime, timezone
from pathlib import Path

from conversation_ledger import import_messages, read_ledger, verify_ledger

RUNTIME_ROOT = Path(__file__).resolve().parent
DEFAULT_LEDGER = RUNTIME_ROOT / "var" / "current-conversation.jsonl"



def _receipt_preflight(receipt):
    """Refuse preexisting exposed receipts before ledger capture begins."""
    try:
        info = Path(receipt).lstat()
    except FileNotFoundError:
        return
    if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
            or stat.S_IMODE(info.st_mode) & 0o077):
        raise PermissionError("Capture receipts must be owner-private")


def _append_private_receipt(receipt, record):
    """Append bounded, content-light receipts through one 0600 locked file."""
    fd = os.open(receipt, os.O_APPEND | os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) & 0o077):
            raise PermissionError("Capture receipts must be owner-private")
        fcntl.flock(fd, fcntl.LOCK_EX)
        data = (json.dumps(record, sort_keys=True) + "\n").encode("utf-8")
        while data:
            written = os.write(fd, data)
            if written <= 0:
                raise OSError("Receipt append did not advance")
            data = data[written:]
        os.fsync(fd)
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def resolve_source(session_id, sessions_root=None):
    root = Path(sessions_root or Path.home() / ".codex" / "sessions")
    matches = sorted(root.glob(f"**/rollout-*{session_id}.jsonl"))
    if not matches:
        raise FileNotFoundError(f"no rollout found for session {session_id}")
    return matches[-1]


def capture_current(ledger=None, source=None, selected_source_ids=None, allow_derived_ids=False,
                    snapshot_bytes=None):
    ledger = Path(ledger or DEFAULT_LEDGER)
    session_id = os.environ.get("CODEX_SESSION_ID")
    if source is None and not session_id:
        raise RuntimeError("CODEX_SESSION_ID is required for /capture")
    source = source or resolve_source(session_id)
    receipt = ledger.parent / "capture-receipts.jsonl"
    receipt.parent.mkdir(parents=True, exist_ok=True)
    _receipt_preflight(receipt)
    try:
        result = import_messages(source, ledger, selected_source_ids=selected_source_ids,
                                 allow_derived_ids=allow_derived_ids, snapshot_bytes=snapshot_bytes)
        result["verification"] = verify_ledger(ledger)
        result["status"] = "CHECKPOINTED"
    except Exception:
        _append_private_receipt(receipt, {
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "source": "codex-rollout",
            "status": "RECOVERY REQUIRED",
            "reason": "capture_failed",
        })
        raise
    _append_private_receipt(receipt, {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "source": "codex-rollout",
        "conversation_id": next(iter({row["conversation_id"] for row in read_ledger(ledger) if row.get("conversation_id")})),
        "added": result["added"], "total": result["total"],
        "ledger_digest": hashlib.sha256(ledger.read_bytes()).hexdigest(),
        "status": result["status"],
    })
    return result


def capture_status(ledger=None):
    ledger = Path(ledger or DEFAULT_LEDGER)
    receipt_path = ledger.parent / "capture-receipts.jsonl"
    if not receipt_path.exists() or not ledger.exists():
        return {"status": "PENDING", "reason": "no capture receipt or ledger"}
    lines = [line for line in receipt_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return {"status": "PENDING", "reason": "no capture receipt"}
    receipt = json.loads(lines[-1])
    digest = hashlib.sha256(ledger.read_bytes()).hexdigest()
    if digest != receipt.get("ledger_digest"):
        return {"status": "RECOVERY REQUIRED", "reason": "ledger digest differs from latest receipt"}
    return {"status": receipt.get("status", "PENDING"), "rows": receipt.get("total", 0),
            "conversation_id": receipt.get("conversation_id")}


def capture_audit(ledger=None):
    ledger = Path(ledger or DEFAULT_LEDGER)
    receipt_path = ledger.parent / "capture-receipts.jsonl"
    if not receipt_path.exists():
        return {"status": "PENDING", "receipts": 0, "reason": "no capture receipt"}
    receipts = [json.loads(line) for line in receipt_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    status = capture_status(ledger)
    return {"status": status["status"], "rows": status.get("rows", 0),
            "receipts": len(receipts), "last": receipts[-1]}


def main():
    parser = argparse.ArgumentParser(description="Capture the current Codex conversation into the local ledger")
    parser.add_argument("--source", type=Path, help="explicit observed rollout JSONL")
    parser.add_argument("--ledger", type=Path, default=None)
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    try:
        print(capture_audit(args.ledger) if args.audit else (capture_status(args.ledger) if args.status else capture_current(args.ledger, args.source)))
    except (FileNotFoundError, RuntimeError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
