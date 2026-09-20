"""Thin local command surface for the verified conversation kernel."""

import argparse
import json
from pathlib import Path

from capture_current_conversation import capture_audit, capture_current, capture_status


def main(argv=None):
    parser = argparse.ArgumentParser(prog="humanos")
    parser.add_argument("command", choices=("capture", "status", "audit"))
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--source", type=Path)
    args = parser.parse_args(argv)
    if args.command == "capture":
        result = capture_current(args.ledger, args.source)
    elif args.command == "status":
        result = capture_status(args.ledger)
    else:
        result = capture_audit(args.ledger)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
