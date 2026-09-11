#!/usr/bin/env python3
"""Install the HumanOS ChatGPT capture native host for Chrome on macOS."""
import argparse
import json
import os
from pathlib import Path
import stat
import sys


def install(extension_id, root=None):
    if not extension_id or any(ch not in "abcdefghijklmnopqrstuvwxyz" for ch in extension_id):
        raise ValueError("Chrome extension ID must contain only lowercase a-z")
    source_root = Path(root or Path(__file__).resolve().parent).resolve()
    host = source_root / "chat_capture_host.py"
    if not host.is_file():
        raise FileNotFoundError("chat_capture_host.py is missing")
    private = source_root / "HumanOS_Vault" / "runtime" / "chat-capture"
    private.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(private, 0o700)
    launcher = private / "host"
    launcher.write_text(
        "#!/bin/sh\nexec " + json.dumps(sys.executable) + " " +
        json.dumps(str(host)) + "\n", encoding="utf-8")
    os.chmod(launcher, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

    manifest_dir = Path.home() / "Library" / "Application Support" / "Google" / "Chrome" / "NativeMessagingHosts"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    manifest = manifest_dir / "com.humanos.chat_capture.json"
    payload = {
        "name": "com.humanos.chat_capture",
        "description": "HumanOS exact visible ChatGPT turn capture",
        "path": str(launcher),
        "type": "stdio",
        "allowed_origins": ["chrome-extension://" + extension_id + "/"],
    }
    pending = manifest.with_suffix(".json.pending")
    pending.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    os.chmod(pending, 0o600)
    os.replace(pending, manifest)
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description="Install HumanOS ChatGPT capture host")
    parser.add_argument("extension_id", help="ID shown by chrome://extensions")
    parser.add_argument("--root", help="HumanOS repository root")
    args = parser.parse_args(argv)
    print(install(args.extension_id, args.root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
