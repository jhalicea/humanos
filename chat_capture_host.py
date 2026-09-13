#!/usr/bin/env python3
"""Chrome native-messaging host for exact visible ChatGPT turn capture."""
import json
from pathlib import Path
import sys

from browser_bridge import native_read, native_write
from capture_ledger import CaptureConflict, CaptureLedger


BASE = Path(__file__).resolve().parent
DEFAULT_LEDGER = BASE / "HumanOS_Vault" / "runtime" / "capture-ledger.sqlite3"


def serve(extension_in, extension_out, ledger):
    while True:
        try:
            message = native_read(extension_in)
        except EOFError:
            return
        try:
            if not isinstance(message, dict) or set(message) != {"kind", "record"}:
                raise ValueError("Unexpected native capture message")
            if message["kind"] != "CAPTURE_VISIBLE_TURN":
                raise ValueError("Unsupported native capture message")
            result = ledger.capture(json.loads(json.dumps(message["record"])))
            native_write(extension_out, {"ok": True, "result": result})
        except (ValueError, TypeError, PermissionError, CaptureConflict,
                OSError) as error:
            native_write(extension_out, {"ok": False, "error": str(error)})


def main():
    ledger = CaptureLedger(DEFAULT_LEDGER)
    try:
        serve(sys.stdin.buffer, sys.stdout.buffer, ledger)
    finally:
        ledger.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
