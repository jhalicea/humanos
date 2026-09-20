"""Thin local command surface for the verified conversation kernel."""

import argparse
import json
from pathlib import Path

from capture_current_conversation import capture_audit, capture_current, capture_status
from local_kernel_capture import capture_turn


def main(argv=None):
    parser = argparse.ArgumentParser(prog="humanos")
    parser.add_argument("command", choices=("capture", "turn", "status", "audit"))
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--conversation-id")
    parser.add_argument("--turn-id")
    parser.add_argument("--human")
    parser.add_argument("--assistant")
    args = parser.parse_args(argv)
    if args.command == "capture":
        result = capture_current(args.ledger, args.source)
    elif args.command == "turn":
        required = (args.conversation_id, args.turn_id, args.human, args.assistant)
        if any(value is None for value in required):
            parser.error("turn requires --conversation-id, --turn-id, --human, and --assistant")
        result = capture_turn(args.ledger, args.conversation_id, args.turn_id,
                              args.human, args.assistant)
    elif args.command == "status":
        result = capture_status(args.ledger)
    else:
        result = capture_audit(args.ledger)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
