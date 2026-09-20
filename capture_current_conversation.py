"""Explicit, local capture command for the current observed Codex session."""

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from conversation_ledger import import_messages, read_ledger, verify_ledger


def resolve_source(session_id, sessions_root=None):
    root = Path(sessions_root or Path.home() / ".codex" / "sessions")
    matches = sorted(root.glob(f"**/rollout-*{session_id}.jsonl"))
    if not matches:
        raise FileNotFoundError(f"no rollout found for session {session_id}")
    return matches[-1]


def capture_current(ledger=Path("var/current-conversation.jsonl"), source=None):
    session_id = os.environ.get("CODEX_SESSION_ID")
    if source is None and not session_id:
        raise RuntimeError("CODEX_SESSION_ID is required for /capture")
    source = source or resolve_source(session_id)
    result = import_messages(source, ledger)
    result["verification"] = verify_ledger(ledger)
    result["status"] = "CHECKPOINTED"
    receipt = ledger.parent / "capture-receipts.jsonl"
    receipt.parent.mkdir(parents=True, exist_ok=True)
    with receipt.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps({
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "source": str(source),
            "conversation_id": next(iter({row["conversation_id"] for row in read_ledger(ledger) if row.get("conversation_id")})),
            "added": result["added"], "total": result["total"],
            "ledger_digest": hashlib.sha256(ledger.read_bytes()).hexdigest(),
            "status": result["status"],
        }, sort_keys=True) + "\n")
    return result


def capture_status(ledger=Path("var/current-conversation.jsonl")):
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


def main():
    parser = argparse.ArgumentParser(description="Capture the current Codex conversation into the local ledger")
    parser.add_argument("--source", type=Path, help="explicit observed rollout JSONL")
    parser.add_argument("--ledger", type=Path, default=Path("var/current-conversation.jsonl"))
    parser.add_argument("--status", action="store_true")
    args = parser.parse_args()
    try:
        print(capture_status(args.ledger) if args.status else capture_current(args.ledger, args.source))
    except (FileNotFoundError, RuntimeError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
