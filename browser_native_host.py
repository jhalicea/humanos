#!/usr/bin/env python3
"""Chrome native-messaging host for the HumanOS Browser Bridge."""
import argparse
import os
from pathlib import Path
import socket
import sys
from browser_bridge import NativeBridge


def main():
    parser = argparse.ArgumentParser(description='HumanOS browser native host')
    parser.add_argument('--socket', required=True, help='Absolute Unix-socket path')
    parser.add_argument('--secret', required=True, help='Owner-only 32-byte secret path')
    args = parser.parse_args()
    path = Path(args.socket)
    if not path.is_absolute():
        raise ValueError('Socket path must be absolute')
    if path.exists() or path.is_socket():
        path.unlink()
    bridge = NativeBridge(path, args.secret, sys.stdin.buffer, sys.stdout.buffer)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        server.bind(str(path)); os.chmod(path, 0o600); server.listen(1)
        while True:
            connection, _ = server.accept()
            with connection:
                bridge.serve_once(connection)


if __name__ == '__main__':
    main()
