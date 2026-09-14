#!/usr/bin/env python3
"""Install the HumanOS desktop ChatGPT capture transport on macOS.

This installer does not install or enable a browser extension silently. The owner
loads ``browser-extension`` as an unpacked extension, then supplies its visible
extension ID here. The installer creates owner-only local config, a LaunchAgent
for the capture daemon, and native-messaging manifests for the selected browser.
"""

import argparse
import json
import os
from pathlib import Path
import plistlib
import stat
import subprocess
import sys


BASE = Path(__file__).resolve().parent
LABEL = 'com.humanos.conversation-capture'


def write_private(path, data, executable=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    mode = 0o700 if executable else 0o600
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(str(path), flags, mode)
    try:
        raw = data.encode('utf-8') if isinstance(data, str) else data
        os.write(fd, raw)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.chmod(path, mode)


def browser_manifest_dirs(browser):
    home = Path.home()
    paths = {
        'chrome': home / 'Library/Application Support/Google/Chrome/NativeMessagingHosts',
        'brave': home / 'Library/Application Support/BraveSoftware/Brave-Browser/NativeMessagingHosts',
    }
    return [paths[name] for name in (('chrome', 'brave') if browser == 'both' else (browser,))]


def resolve_vault(value):
    if value:
        return Path(value).expanduser().resolve()
    config = json.loads((BASE / 'config.json').read_text(encoding='utf-8'))
    configured = Path(config.get('vault', 'HumanOS_Vault'))
    return (configured if configured.is_absolute() else BASE / configured).resolve()


def main():
    if sys.platform != 'darwin':
        raise SystemExit('This installer is for macOS only')
    parser = argparse.ArgumentParser(description='Install HumanOS ChatGPT web capture on macOS')
    parser.add_argument('--extension-id', required=True,
                        help='ID shown for the unpacked HumanOS extension in the browser')
    parser.add_argument('--browser', choices=('chrome', 'brave', 'both'), default='chrome')
    parser.add_argument('--vault', help='HumanOS vault path; defaults to config.json')
    parser.add_argument('--owner', default='Jon')
    parser.add_argument('--no-launch', action='store_true',
                        help='Write installation files but do not load the LaunchAgent')
    args = parser.parse_args()

    if not args.extension_id.isalnum():
        raise SystemExit('Extension ID must contain only letters/numbers')
    vault = resolve_vault(args.vault)
    humanos = Path.home() / '.humanos'
    logs = humanos / 'logs'
    logs.mkdir(parents=True, exist_ok=True, mode=0o700)
    socket_path = humanos / 'conversation-capture.sock'
    secret_path = vault / 'capture-transport' / 'capture.key'
    native_config = humanos / 'conversation-capture-native.json'
    wrapper = humanos / 'conversation-capture-native-host'

    write_private(native_config, json.dumps({
        'socket': str(socket_path),
        'secret': str(secret_path),
    }, indent=2) + '\n')
    write_private(wrapper,
                  '#!/bin/sh\nexec ' + json.dumps(sys.executable) + ' ' +
                  json.dumps(str(BASE / 'conversation_capture_native_host.py')) + '\n',
                  executable=True)

    manifest = {
        'name': 'com.humanos.conversation_capture',
        'description': 'HumanOS Universal Conversation Capture native host',
        'path': str(wrapper),
        'type': 'stdio',
        'allowed_origins': ['chrome-extension://' + args.extension_id + '/'],
    }
    for directory in browser_manifest_dirs(args.browser):
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / 'com.humanos.conversation_capture.json'
        target.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
        os.chmod(target, 0o600)

    launch_agent = Path.home() / 'Library/LaunchAgents' / (LABEL + '.plist')
    launch_agent.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        'Label': LABEL,
        'ProgramArguments': [sys.executable, str(BASE / 'conversation_transport.py'), 'serve',
                             '--vault', str(vault), '--socket', str(socket_path),
                             '--owner', args.owner],
        'RunAtLoad': True,
        'KeepAlive': True,
        'StandardOutPath': str(logs / 'conversation-capture.out.log'),
        'StandardErrorPath': str(logs / 'conversation-capture.err.log'),
        'ProcessType': 'Background',
    }
    with open(launch_agent, 'wb') as stream:
        plistlib.dump(payload, stream)
    os.chmod(launch_agent, 0o600)

    if not args.no_launch:
        domain = 'gui/' + str(os.getuid())
        subprocess.run(['launchctl', 'bootout', domain, str(launch_agent)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(['launchctl', 'bootstrap', domain, str(launch_agent)], check=True)
        subprocess.run(['launchctl', 'kickstart', '-k', domain + '/' + LABEL], check=True)

    print('HumanOS conversation capture installation prepared.')
    print('Vault: ' + str(vault))
    print('Socket: ' + str(socket_path))
    print('Extension folder: ' + str(BASE / 'browser-extension'))
    print('Restart/reload the browser extension after installing the native host.')
    print('This enables desktop ChatGPT web capture only; it does not capture the native iOS ChatGPT app.')


if __name__ == '__main__':
    main()
