#!/usr/bin/env python3
"""Chrome native-messaging adapter for HumanOS conversation capture.

The browser extension never receives the local capture secret. This process reads
an owner-only config file, signs each event for the Unix-socket capture daemon,
and returns the daemon's verified-local-storage acknowledgement to the extension.
"""

import json
import os
from pathlib import Path
import stat
import sys

from browser_bridge import native_read, native_write
from conversation_transport import capture_sender


DEFAULT_CONFIG = Path.home() / '.humanos' / 'conversation-capture-native.json'


def load_config(path=None):
    path = Path(path or os.environ.get('HUMANOS_CAPTURE_NATIVE_CONFIG', DEFAULT_CONFIG)).expanduser().resolve()
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or path.is_symlink():
        raise PermissionError('Capture native-host config must be a regular file')
    if os.name == 'posix' and stat.S_IMODE(info.st_mode) & 0o077:
        raise PermissionError('Capture native-host config must be owner-only')
    value = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(value, dict) or set(value) != {'socket', 'secret'}:
        raise ValueError('Capture native-host config must contain socket and secret')
    socket_path = Path(value['socket']).expanduser().resolve()
    secret_path = Path(value['secret']).expanduser().resolve()
    if not socket_path.is_absolute() or not secret_path.is_absolute():
        raise ValueError('Capture native-host paths must be absolute')
    return socket_path, secret_path


def main():
    socket_path, secret_path = load_config()
    send = capture_sender(socket_path, secret_path)
    while True:
        try:
            message = native_read(sys.stdin.buffer)
        except EOFError:
            return
        try:
            if not isinstance(message, dict) or set(message) != {
                    'source', 'conversation_id', 'turn_id', 'role', 'text'}:
                raise ValueError('Malformed browser capture event')
            response = send(message['source'], message['conversation_id'], message['turn_id'],
                            message['role'], message['text'])
        except Exception as error:
            response = {'ok': False, 'error': str(error)}
        native_write(sys.stdout.buffer, response)


if __name__ == '__main__':
    main()
