#!/usr/bin/env python3
"""Local owner CLI for the HumanOS Control Room mailbox."""
from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

from control_room import ControlRoomStore


def db_path() -> Path:
    raw = os.environ.get("HUMANOS_CONTROL_DB")
    return Path(raw).expanduser() if raw else Path.home() / ".humanos" / "control-room" / "control.sqlite3"


def baseline() -> str | None:
    root = os.environ.get("HUMANOS_REPO_ROOT")
    if not root:
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(Path(root).expanduser()), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip().lower() or None


def main() -> int:
    parser = argparse.ArgumentParser(description="HumanOS Control Room local mailbox")
    sub = parser.add_subparsers(dest="command", required=True)

    send = sub.add_parser("send", help="Queue a local request")
    send.add_argument("text")
    send.add_argument("--data-class", default="INTERNAL")
    send.add_argument(
        "--approve-external",
        action="store_true",
        help="Explicitly allow this exact request to cross the MCP boundary",
    )

    response = sub.add_parser("response", help="Read a returned response")
    response.add_argument("request_id")

    sub.add_parser("next-external", help="Preview the next externally approved request")
    sub.add_parser("work-orders", help="List recorded work-order baseline states")

    args = parser.parse_args()
    store = ControlRoomStore(db_path())
    try:
        if args.command == "send":
            print(store.queue_local_request(
                args.text,
                data_class=args.data_class,
                external_approved=args.approve_external,
            ))
        elif args.command == "response":
            print(store.local_response(args.request_id))
        elif args.command == "next-external":
            print(store.next_external_request())
        elif args.command == "work-orders":
            print(store.pending_work_orders(current_baseline=baseline()))
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
