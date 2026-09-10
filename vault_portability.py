#!/usr/bin/env python3
"""Verified local HumanOS vault backup/restore for macOS and Linux.

This format preserves integrity and portability, not confidentiality: the bundle
contains the plaintext SQLite database and the raw vault integrity key. The bundle
is therefore created owner-only (0700 directory, 0600 files) and must be stored on
trusted encrypted storage until application-level backup encryption is implemented.
"""
import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import shutil
import sqlite3
import stat
import tempfile

from integrity_lifecycle import KEY_BYTES, KEY_FILE, key_id

FORMAT = 'humanos-portable-vault'
VERSION = 1
MANIFEST = 'manifest.json'
DB_FILE = 'notebook.sqlite3'
RECOVERY_FILE = 'recovery.jsonl'
PROOF_PREFIX = 'hmac-sha256:'


class VaultBackupError(RuntimeError):
    pass


def _encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def _proof(key, data):
    return PROOF_PREFIX + hmac.new(key, data, hashlib.sha256).hexdigest()


def _fsync_file(path):
    fd = os.open(str(path), os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _fsync_directory(path):
    if os.name != 'posix':
        return
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _validate_private_directory(path):
    path = Path(path)
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or path.is_symlink():
        raise VaultBackupError('Backup path must be an ordinary directory')
    if os.name == 'posix':
        if info.st_uid != os.getuid():
            raise VaultBackupError('Backup directory must be owned by the current user')
        if stat.S_IMODE(info.st_mode) & 0o077:
            raise VaultBackupError('Backup directory permissions are unsafe; require owner-only access')


def _read_private_file(path, *, expected_bytes=None):
    path = Path(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise VaultBackupError('Backup contains a linked or non-regular file: ' + path.name)
    if os.name == 'posix':
        if before.st_uid != os.getuid():
            raise VaultBackupError('Backup file is not owned by the current user: ' + path.name)
        if stat.S_IMODE(before.st_mode) & 0o077:
            raise VaultBackupError('Backup file permissions are unsafe: ' + path.name)
    fd = os.open(str(path), os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    try:
        after = os.fstat(fd)
        if not stat.S_ISREG(after.st_mode) or after.st_nlink != 1:
            raise VaultBackupError('Backup file changed identity: ' + path.name)
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise VaultBackupError('Backup file changed identity: ' + path.name)
        chunks = []
        while True:
            block = os.read(fd, 1024 * 1024)
            if not block:
                break
            chunks.append(block)
    finally:
        os.close(fd)
    data = b''.join(chunks)
    if expected_bytes is not None and len(data) != expected_bytes:
        raise VaultBackupError('Unexpected size for ' + path.name)
    return data


def _write_private(path, data):
    path = Path(path)
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    try:
        offset = 0
        while offset < len(data):
            count = os.write(fd, data[offset:])
            if count <= 0:
                raise OSError('short backup write')
            offset += count
        os.fsync(fd)
    finally:
        os.close(fd)


def _manifest_payload(key, files):
    return {
        'format': FORMAT,
        'version': VERSION,
        'key_id': key_id(key),
        'confidentiality': 'PLAINTEXT_OWNER_ONLY',
        'files': {
            name: {'bytes': len(data), 'proof': _proof(key, data)}
            for name, data in sorted(files.items())
        },
    }


def _seal_manifest(key, files):
    payload = _manifest_payload(key, files)
    payload['manifest_proof'] = _proof(key, _encode(payload).encode('utf-8'))
    return payload


def _verify_manifest(key, manifest):
    if not isinstance(manifest, dict):
        raise VaultBackupError('Backup manifest is invalid')
    required = {'format', 'version', 'key_id', 'confidentiality', 'files', 'manifest_proof'}
    if set(manifest) != required or manifest['format'] != FORMAT or manifest['version'] != VERSION:
        raise VaultBackupError('Unsupported or malformed backup manifest')
    if manifest['confidentiality'] != 'PLAINTEXT_OWNER_ONLY':
        raise VaultBackupError('Unexpected backup confidentiality declaration')
    if not hmac.compare_digest(str(manifest['key_id']), key_id(key)):
        raise VaultBackupError('Backup integrity key does not match its manifest')
    unsigned = {key_name: value for key_name, value in manifest.items() if key_name != 'manifest_proof'}
    expected = _proof(key, _encode(unsigned).encode('utf-8'))
    if not hmac.compare_digest(str(manifest['manifest_proof']), expected):
        raise VaultBackupError('Backup manifest authentication failed')
    files = manifest['files']
    if not isinstance(files, dict) or DB_FILE not in files or KEY_FILE not in files:
        raise VaultBackupError('Backup manifest is missing required files')
    if set(files) - {DB_FILE, KEY_FILE, RECOVERY_FILE}:
        raise VaultBackupError('Backup manifest contains unsupported files')
    return files


def verify_portable_backup(bundle):
    """Cryptographically verify a bundle without modifying it."""
    bundle = Path(bundle).resolve()
    _validate_private_directory(bundle)
    key = _read_private_file(bundle / KEY_FILE, expected_bytes=KEY_BYTES)
    raw_manifest = _read_private_file(bundle / MANIFEST)
    try:
        manifest = json.loads(raw_manifest.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise VaultBackupError('Backup manifest is unreadable') from error
    entries = _verify_manifest(key, manifest)
    actual_names = {path.name for path in bundle.iterdir()}
    expected_names = set(entries) | {MANIFEST}
    if actual_names != expected_names:
        raise VaultBackupError('Backup directory contents differ from the authenticated manifest')
    for name, record in entries.items():
        if not isinstance(record, dict) or set(record) != {'bytes', 'proof'}:
            raise VaultBackupError('Malformed file record in backup manifest: ' + name)
        data = _read_private_file(bundle / name)
        if record['bytes'] != len(data) or not hmac.compare_digest(str(record['proof']), _proof(key, data)):
            raise VaultBackupError('Backup file authentication failed: ' + name)
    return {'format': FORMAT, 'version': VERSION, 'key_id': key_id(key),
            'files': sorted(entries), 'verified': True}


def _copy_bundle_runtime(bundle, vault):
    bundle, vault = Path(bundle), Path(vault)
    runtime = vault / 'runtime'
    runtime.mkdir(parents=True, exist_ok=False, mode=0o700)
    manifest = json.loads(_read_private_file(bundle / MANIFEST).decode('utf-8'))
    for name in manifest['files']:
        data = _read_private_file(bundle / name)
        _write_private(runtime / name, data)
    _fsync_directory(runtime)


def _open_verify_staged(vault):
    # Delayed import avoids a module cycle: notebook imports integrity_lifecycle.
    from notebook import Notebook
    book = Notebook(vault)
    try:
        # Projections are replaceable and intentionally excluded from the portable bundle.
        book.project()
        book.verify()
    finally:
        book.close()


def _stage_verify_bundle(bundle, parent):
    stage = Path(tempfile.mkdtemp(prefix='.humanos-verify-', dir=str(parent)))
    os.chmod(stage, 0o700)
    try:
        vault = stage / 'vault'
        vault.mkdir(mode=0o700)
        _copy_bundle_runtime(bundle, vault)
        _open_verify_staged(vault)
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def create_portable_backup(vault, destination):
    """Create, authenticate, and staged-restore-verify one non-overwriting backup."""
    from notebook import Notebook
    vault = Path(vault).resolve()
    destination = Path(destination).resolve(strict=False)
    try:
        destination.relative_to(vault)
        raise VaultBackupError('Backup destination must be outside the source vault')
    except ValueError:
        pass
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('Backup destination already exists')
    destination.parent.mkdir(parents=True, exist_ok=True)
    book = Notebook(vault)
    try:
        book.verify()
        destination.mkdir(mode=0o700)
        os.chmod(destination, 0o700)
        db_path = destination / DB_FILE
        target = sqlite3.connect(str(db_path))
        try:
            book.db.backup(target)
            target.commit()
        finally:
            target.close()
        os.chmod(db_path, 0o600)
        _fsync_file(db_path)
        files = {DB_FILE: _read_private_file(db_path), KEY_FILE: bytes(book.integrity_key)}
        _write_private(destination / KEY_FILE, files[KEY_FILE])
        fallback = book.root / RECOVERY_FILE
        if fallback.exists() or fallback.is_symlink():
            files[RECOVERY_FILE] = _read_private_file(fallback)
            _write_private(destination / RECOVERY_FILE, files[RECOVERY_FILE])
        manifest = _seal_manifest(book.integrity_key, files)
        _write_private(destination / MANIFEST, (_encode(manifest) + '\n').encode('utf-8'))
        _fsync_directory(destination)
    except BaseException:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    finally:
        book.close()
    result = verify_portable_backup(destination)
    _stage_verify_bundle(destination, destination.parent)
    result['staged_restore_verified'] = True
    result['path'] = str(destination)
    return result


def restore_portable_backup(bundle, destination_vault):
    """Verify a bundle, stage a full Notebook verification, then atomically place it."""
    bundle = Path(bundle).resolve()
    destination = Path(destination_vault).resolve(strict=False)
    verify_portable_backup(bundle)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() or destination.is_symlink():
        if destination.is_symlink() or not destination.is_dir() or any(destination.iterdir()):
            raise FileExistsError('Restore destination must not exist or must be an empty directory')
        destination.rmdir()
    stage = Path(tempfile.mkdtemp(prefix='.humanos-restore-', dir=str(destination.parent)))
    os.chmod(stage, 0o700)
    placed = False
    try:
        _copy_bundle_runtime(bundle, stage)
        _open_verify_staged(stage)
        os.replace(stage, destination)
        placed = True
        _fsync_directory(destination.parent)
    finally:
        if not placed:
            shutil.rmtree(stage, ignore_errors=True)
    return {'format': FORMAT, 'version': VERSION, 'path': str(destination),
            'key_id': json.loads(_read_private_file(bundle / MANIFEST).decode('utf-8'))['key_id'],
            'verified': True, 'restored': True}


def main(argv=None):
    parser = argparse.ArgumentParser(description='HumanOS verified portable vault backup/restore')
    sub = parser.add_subparsers(dest='command', required=True)
    backup = sub.add_parser('backup')
    backup.add_argument('vault')
    backup.add_argument('destination')
    restore = sub.add_parser('restore')
    restore.add_argument('bundle')
    restore.add_argument('destination_vault')
    verify = sub.add_parser('verify')
    verify.add_argument('bundle')
    args = parser.parse_args(argv)
    if args.command == 'backup':
        result = create_portable_backup(args.vault, args.destination)
    elif args.command == 'restore':
        result = restore_portable_backup(args.bundle, args.destination_vault)
    else:
        result = verify_portable_backup(args.bundle)
    print(_encode(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
