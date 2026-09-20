"""Explicit, local capture command for the current observed Codex session."""

import argparse
import os
from pathlib import Path

from conversation_ledger import import_messages, verify_ledger


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
    result = import_messages(source or resolve_source(session_id), ledger)
    result["verification"] = verify_ledger(ledger)
    result["status"] = "CHECKPOINTED"
    return result


def main():
    parser = argparse.ArgumentParser(description="Capture the current Codex conversation into the local ledger")
    parser.add_argument("--source", type=Path, help="explicit observed rollout JSONL")
    parser.add_argument("--ledger", type=Path, default=Path("var/current-conversation.jsonl"))
    args = parser.parse_args()
    try:
        print(capture_current(args.ledger, args.source))
    except (FileNotFoundError, RuntimeError) as error:
        parser.error(str(error))


if __name__ == "__main__":
    main()
