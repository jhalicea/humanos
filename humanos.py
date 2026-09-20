"""Thin local command surface for the verified conversation kernel."""

import argparse
import json
from pathlib import Path

from capture_current_conversation import capture_audit, capture_current, capture_status
from local_kernel_capture import capture_turn
from ledger_notebook_projection import project_all_pairs
from conversation_ledger import verify_ledger

DEFAULT_LEDGER = Path(__file__).resolve().parent / "var" / "current-conversation.jsonl"


def main(argv=None):
    parser = argparse.ArgumentParser(prog="humanos")
    parser.add_argument("command", choices=("capture", "turn", "project", "verify", "status", "audit"))
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--conversation-id")
    parser.add_argument("--turn-id")
    parser.add_argument("--human")
    parser.add_argument("--assistant")
    parser.add_argument("--notebook", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "capture":
        result = capture_current(args.ledger, args.source)
    elif args.command == "turn":
        required = (args.conversation_id, args.turn_id, args.human, args.assistant)
        if any(value is None for value in required):
            parser.error("turn requires --conversation-id, --turn-id, --human, and --assistant")
        result = capture_turn(args.ledger or DEFAULT_LEDGER, args.conversation_id, args.turn_id,
                              args.human, args.assistant)
    elif args.command == "project":
        if args.notebook is None:
            parser.error("project requires --notebook")
        result = project_all_pairs(args.ledger or DEFAULT_LEDGER, args.notebook)
    elif args.command == "verify":
        ledger = args.ledger or DEFAULT_LEDGER
        result = {"ledger": verify_ledger(ledger), "capture": capture_status(ledger)}
        if args.notebook is not None:
            result["notebook"] = project_all_pairs(ledger, args.notebook)
    elif args.command == "status":
        result = capture_status(args.ledger)
    else:
        result = capture_audit(args.ledger)
    if args.pretty and args.command == "verify":
        print("HumanOS verification")
        print("  Ledger:  " + result["ledger"]["status"] + f" ({result['ledger'].get('rows', 0)} rows)")
        print("  Capture: " + result["capture"]["status"])
        if "notebook" in result:
            notebook = result["notebook"]
            print("  Notebook: " + notebook["status"] +
                  f" (projected={notebook.get('projected', 0)}, skipped={notebook.get('skipped', 0)})")
    else:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
