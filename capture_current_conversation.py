"""Explicit, local capture command for the current observed Codex session."""

import argparse
import os
from pathlib import Path

from conversation_ledger import import_messages


def resolve_source(session_id, sessions_root=None):
    root = Path(sessions_root or Path.home() / ".codex" / "sessions")
    matches = sorted(root.glob(f"**/rollout-*{session_id}.jsonl"))
    if not matches:
        raise FileNotFoundError(f"no rollout found for session {session_id}")
    return matches[-1]


def main():
    parser = argparse.ArgumentParser(description="Capture the current Codex conversation into the local ledger")
    parser.add_argument("--source", type=Path, help="explicit observed rollout JSONL")
    parser.add_argument("--ledger", type=Path, default=Path("var/current-conversation.jsonl"))
    args = parser.parse_args()
    session_id = os.environ.get("CODEX_SESSION_ID")
    if args.source is None and not session_id:
        parser.error("CODEX_SESSION_ID is required when --source is omitted")
    source = args.source or resolve_source(session_id)
    print(import_messages(source, args.ledger))


if __name__ == "__main__":
    main()
