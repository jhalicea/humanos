"""Small local-kernel entrypoint for recording one complete conversation turn."""

import argparse
import json
from pathlib import Path

from ledger_capture_adapter import capture_observed_turn


def capture_turn(ledger, conversation_id, turn_id, human_text, assistant_text):
    return capture_observed_turn(ledger, "humanos-local", conversation_id, turn_id,
                                 human_text, assistant_text)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--conversation-id", required=True)
    parser.add_argument("--turn-id", required=True)
    parser.add_argument("--human", required=True)
    parser.add_argument("--assistant", required=True)
    args = parser.parse_args(argv)
    print(json.dumps(capture_turn(args.ledger, args.conversation_id, args.turn_id,
                                  args.human, args.assistant), ensure_ascii=False,
                     sort_keys=True))


if __name__ == "__main__":
    main()
