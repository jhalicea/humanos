"""Local Chrome native-messaging host for regular-chat ledger capture."""

import argparse
import json
import struct
import sys

from browser_ledger_sink import accept_browser_event


def read_message(stream):
    header = stream.read(4)
    if not header:
        return None
    if len(header) != 4:
        raise ValueError("truncated native-message header")
    size = struct.unpack("<I", header)[0]
    if size > 2 * 1024 * 1024:
        raise ValueError("native message exceeds size limit")
    payload = stream.read(size)
    if len(payload) != size:
        raise ValueError("truncated native-message payload")
    return json.loads(payload.decode("utf-8"))


def write_message(stream, value):
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    stream.write(struct.pack("<I", len(payload)) + payload)
    stream.flush()


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", required=True)
    args = parser.parse_args(argv)
    while True:
        try:
            event = read_message(sys.stdin.buffer)
            if event is None:
                return
            response = accept_browser_event(event, args.ledger)
        except Exception as error:
            response = {"status": "REJECTED", "error": str(error)}
        write_message(sys.stdout.buffer, response)


if __name__ == "__main__":
    main()
