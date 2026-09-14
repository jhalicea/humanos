#!/usr/bin/env python3
"""Generate HumanOS capture recipient keys on the owner's machine.

This command intentionally prints only the public key and key id. The private
X25519 key is written owner-only and must never be pasted into ChatGPT, Render,
Neon, GitHub, CI, or other remote services.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from capture_encryption import save_recipient_keypair


def main() -> int:
    parser = argparse.ArgumentParser(description='Generate local HumanOS capture encryption keys')
    parser.add_argument(
        '--directory',
        default='~/.humanos/keys',
        help='owner-only key directory (default: ~/.humanos/keys)',
    )
    args = parser.parse_args()
    result = save_recipient_keypair(Path(args.directory).expanduser())
    # Do not print private_path or any private-key material in machine-readable output.
    print(json.dumps({
        'recipient_key_id': result['recipient_key_id'],
        'public_key_b64': result['public_key_b64'],
        'public_key_path': result['public_path'],
        'private_key_saved_locally': True,
    }, indent=2, sort_keys=True))
    print('Private key was created locally and was not printed. Keep it off remote services.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
