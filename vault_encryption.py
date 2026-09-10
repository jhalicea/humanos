#!/usr/bin/env python3
"""Encrypted portable HumanOS vault backups.

The Notebook integrity key remains stable vault identity. Backup confidentiality is
provided by a separate passphrase-derived AES-256-GCM key. The encrypted artifact
contains an authenticated archive of the already-verified portable bundle.
"""
import argparse
import base64
import getpass
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import struct
import tarfile
import tempfile

from vault_portability import (DB_FILE, KEY_FILE, MANIFEST, RECOVERY_FILE,
                               create_portable_backup, restore_portable_backup,
                               verify_portable_backup)

MAGIC = b'HUMANOS-ENCRYPTED-VAULT-v1\n'
FORMAT = 'humanos-encrypted-vault'
VERSION = 1
TAG_BYTES = 16
SALT_BYTES = 16
NONCE_BYTES = 12
KDF_N = 1 << 15
KDF_R = 8
KDF_P = 1
KDF_MAXMEM = 64 * 1024 * 1024
CHUNK = 1024 * 1024
_ALLOWED_BUNDLE_FILES = {DB_FILE, KEY_FILE, MANIFEST, RECOVERY_FILE}


class EncryptedBackupError(RuntimeError):
    pass


def _encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def _crypto():
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    except ImportError as error:
        raise EncryptedBackupError(
            'Encrypted backups require the optional cryptography package; install requirements-encrypted-backup.txt'
        ) from error
    return Cipher, algorithms, modes


def _derive_key(passphrase, salt):
    if not isinstance(passphrase, str) or not passphrase:
        raise EncryptedBackupError('Backup passphrase must be a nonempty string')
    return hashlib.scrypt(passphrase.encode('utf-8'), salt=salt, n=KDF_N, r=KDF_R, p=KDF_P,
                          maxmem=KDF_MAXMEM, dklen=32)


def _fsync_dir(path):
    if os.name != 'posix':
        return
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _validate_private_regular(path):
    path = Path(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise EncryptedBackupError('Encrypted backup must be one ordinary non-linked file')
    if os.name == 'posix':
        if before.st_uid != os.getuid():
            raise EncryptedBackupError('Encrypted backup must be owned by the current user')
        if stat.S_IMODE(before.st_mode) & 0o077:
            raise EncryptedBackupError('Encrypted backup permissions are unsafe; require owner-only access')
    return before


def _open_private_read(path):
    path = Path(path)
    before = _validate_private_regular(path)
    fd = os.open(str(path), os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    after = os.fstat(fd)
    if (not stat.S_ISREG(after.st_mode) or after.st_nlink != 1 or
            (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino)):
        os.close(fd)
        raise EncryptedBackupError('Encrypted backup changed identity while opening')
    return os.fdopen(fd, 'rb', closefd=True)


def _new_private_file(path):
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    return os.fdopen(fd, 'wb', closefd=True)


def _header(salt, nonce):
    return {
        'format': FORMAT,
        'version': VERSION,
        'kdf': {'name': 'scrypt', 'n': KDF_N, 'r': KDF_R, 'p': KDF_P,
                'salt': base64.b64encode(salt).decode('ascii')},
        'cipher': {'name': 'AES-256-GCM', 'nonce': base64.b64encode(nonce).decode('ascii')},
        'payload': 'humanos-portable-vault-v1-tar',
    }


def _parse_header(raw):
    try:
        value = json.loads(raw.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EncryptedBackupError('Encrypted backup header is unreadable') from error
    if not isinstance(value, dict) or set(value) != {'format', 'version', 'kdf', 'cipher', 'payload'}:
        raise EncryptedBackupError('Encrypted backup header is malformed')
    if value['format'] != FORMAT or value['version'] != VERSION or value['payload'] != 'humanos-portable-vault-v1-tar':
        raise EncryptedBackupError('Unsupported encrypted backup format')
    kdf, cipher = value['kdf'], value['cipher']
    if (not isinstance(kdf, dict) or set(kdf) != {'name', 'n', 'r', 'p', 'salt'} or
            kdf['name'] != 'scrypt' or kdf['n'] != KDF_N or kdf['r'] != KDF_R or kdf['p'] != KDF_P):
        raise EncryptedBackupError('Unsupported encrypted backup KDF parameters')
    if not isinstance(cipher, dict) or set(cipher) != {'name', 'nonce'} or cipher['name'] != 'AES-256-GCM':
        raise EncryptedBackupError('Unsupported encrypted backup cipher parameters')
    try:
        salt = base64.b64decode(kdf['salt'], validate=True)
        nonce = base64.b64decode(cipher['nonce'], validate=True)
    except Exception as error:
        raise EncryptedBackupError('Encrypted backup header encoding is invalid') from error
    if len(salt) != SALT_BYTES or len(nonce) != NONCE_BYTES:
        raise EncryptedBackupError('Encrypted backup salt or nonce length is invalid')
    return value, salt, nonce


def _safe_bundle_to_tar(bundle, tar_path):
    bundle = Path(bundle)
    verified = verify_portable_backup(bundle)
    expected = set(verified['files']) | {MANIFEST}
    if not expected <= _ALLOWED_BUNDLE_FILES:
        raise EncryptedBackupError('Portable bundle contains unsupported files')
    with _new_private_file(tar_path) as raw:
        with tarfile.open(fileobj=raw, mode='w') as archive:
            for name in sorted(expected):
                source = bundle / name
                info = source.lstat()
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise EncryptedBackupError('Portable bundle contains a linked or non-regular file')
                fd = os.open(str(source), os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
                try:
                    current = os.fstat(fd)
                    if ((info.st_dev, info.st_ino) != (current.st_dev, current.st_ino) or
                            not stat.S_ISREG(current.st_mode) or current.st_nlink != 1):
                        raise EncryptedBackupError('Portable bundle file changed identity while archiving')
                    member = tarfile.TarInfo(name=name)
                    member.size = current.st_size
                    member.mode = 0o600
                    member.uid = member.gid = 0
                    member.uname = member.gname = ''
                    member.mtime = 0
                    with os.fdopen(os.dup(fd), 'rb', closefd=True) as source_file:
                        archive.addfile(member, source_file)
                finally:
                    os.close(fd)
        raw.flush()
        os.fsync(raw.fileno())


def _safe_tar_to_bundle(tar_path, bundle):
    bundle = Path(bundle)
    bundle.mkdir(mode=0o700)
    os.chmod(bundle, 0o700)
    seen = set()
    try:
        with open(tar_path, 'rb') as raw, tarfile.open(fileobj=raw, mode='r:') as archive:
            members = archive.getmembers()
            for member in members:
                name = member.name
                if (name in seen or name not in _ALLOWED_BUNDLE_FILES or '/' in name or '\\' in name or
                        not member.isfile()):
                    raise EncryptedBackupError('Encrypted backup archive contains an unsafe entry')
                seen.add(name)
                stream = archive.extractfile(member)
                if stream is None:
                    raise EncryptedBackupError('Encrypted backup archive entry is unreadable')
                target = bundle / name
                with _new_private_file(target) as out:
                    remaining = member.size
                    while remaining:
                        block = stream.read(min(CHUNK, remaining))
                        if not block:
                            raise EncryptedBackupError('Encrypted backup archive entry is truncated')
                        out.write(block)
                        remaining -= len(block)
                    if stream.read(1):
                        raise EncryptedBackupError('Encrypted backup archive entry exceeds declared size')
                    out.flush()
                    os.fsync(out.fileno())
        if MANIFEST not in seen or DB_FILE not in seen or KEY_FILE not in seen:
            raise EncryptedBackupError('Encrypted backup archive is missing required files')
        _fsync_dir(bundle)
    except BaseException:
        shutil.rmtree(bundle, ignore_errors=True)
        raise


def _encrypt_tar(tar_path, destination, passphrase):
    Cipher, algorithms, modes = _crypto()
    salt, nonce = os.urandom(SALT_BYTES), os.urandom(NONCE_BYTES)
    header = _header(salt, nonce)
    raw_header = _encode(header)
    if len(raw_header) > 65535:
        raise EncryptedBackupError('Encrypted backup header is unexpectedly large')
    key = _derive_key(passphrase, salt)
    encryptor = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
    encryptor.authenticate_additional_data(raw_header)
    with _new_private_file(destination) as out, open(tar_path, 'rb') as source:
        out.write(MAGIC)
        out.write(struct.pack('>I', len(raw_header)))
        out.write(raw_header)
        while True:
            block = source.read(CHUNK)
            if not block:
                break
            out.write(encryptor.update(block))
        out.write(encryptor.finalize())
        out.write(encryptor.tag)
        out.flush()
        os.fsync(out.fileno())
    _fsync_dir(Path(destination).parent)


def _decrypt_to_tar(encrypted_path, tar_path, passphrase):
    Cipher, algorithms, modes = _crypto()
    with _open_private_read(encrypted_path) as source:
        if source.read(len(MAGIC)) != MAGIC:
            raise EncryptedBackupError('Encrypted backup magic/version is invalid')
        raw_length = source.read(4)
        if len(raw_length) != 4:
            raise EncryptedBackupError('Encrypted backup header is truncated')
        header_length = struct.unpack('>I', raw_length)[0]
        if header_length <= 0 or header_length > 65535:
            raise EncryptedBackupError('Encrypted backup header length is invalid')
        raw_header = source.read(header_length)
        if len(raw_header) != header_length:
            raise EncryptedBackupError('Encrypted backup header is truncated')
        _, salt, nonce = _parse_header(raw_header)
        payload_start = len(MAGIC) + 4 + header_length
        source.seek(0, os.SEEK_END)
        total = source.tell()
        if total < payload_start + TAG_BYTES:
            raise EncryptedBackupError('Encrypted backup payload is truncated')
        ciphertext_bytes = total - payload_start - TAG_BYTES
        source.seek(total - TAG_BYTES)
        tag = source.read(TAG_BYTES)
        source.seek(payload_start)
        key = _derive_key(passphrase, salt)
        decryptor = Cipher(algorithms.AES(key), modes.GCM(nonce, tag)).decryptor()
        decryptor.authenticate_additional_data(raw_header)
        try:
            with _new_private_file(tar_path) as out:
                remaining = ciphertext_bytes
                while remaining:
                    block = source.read(min(CHUNK, remaining))
                    if not block:
                        raise EncryptedBackupError('Encrypted backup ciphertext is truncated')
                    remaining -= len(block)
                    out.write(decryptor.update(block))
                out.write(decryptor.finalize())
                out.flush()
                os.fsync(out.fileno())
        except Exception as error:
            try:
                Path(tar_path).unlink()
            except OSError:
                pass
            if isinstance(error, EncryptedBackupError):
                raise
            raise EncryptedBackupError('Encrypted backup authentication failed: wrong passphrase or tampered artifact') from error


def _decrypt_bundle(encrypted_path, parent, passphrase):
    stage = Path(tempfile.mkdtemp(prefix='.humanos-encrypted-', dir=str(parent)))
    os.chmod(stage, 0o700)
    try:
        tar_path = stage / 'payload.tar'
        _decrypt_to_tar(encrypted_path, tar_path, passphrase)
        bundle = stage / 'bundle'
        _safe_tar_to_bundle(tar_path, bundle)
        tar_path.unlink()
        verify_portable_backup(bundle)
        return stage, bundle
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise


def verify_encrypted_backup(encrypted_path, passphrase):
    encrypted_path = Path(encrypted_path).resolve()
    stage, bundle = _decrypt_bundle(encrypted_path, encrypted_path.parent, passphrase)
    try:
        probe = stage / 'verified-vault'
        restored = restore_portable_backup(bundle, probe)
        return {'format': FORMAT, 'version': VERSION, 'path': str(encrypted_path),
                'key_id': restored['key_id'], 'verified': True,
                'staged_restore_verified': True}
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def create_encrypted_backup(vault, destination, passphrase):
    vault = Path(vault).resolve()
    destination = Path(destination).resolve(strict=False)
    try:
        destination.relative_to(vault)
        raise EncryptedBackupError('Encrypted backup destination must be outside the source vault')
    except ValueError:
        pass
    if destination.exists() or destination.is_symlink():
        raise FileExistsError('Encrypted backup destination already exists')
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.humanos-encrypt-', dir=str(destination.parent)))
    os.chmod(stage, 0o700)
    created = False
    try:
        bundle = stage / 'portable'
        create_portable_backup(vault, bundle)
        tar_path = stage / 'portable.tar'
        _safe_bundle_to_tar(bundle, tar_path)
        _encrypt_tar(tar_path, destination, passphrase)
        created = True
        result = verify_encrypted_backup(destination, passphrase)
        result['created'] = True
        return result
    except BaseException:
        if created:
            try:
                destination.unlink()
            except OSError:
                pass
        raise
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def _destination_available(destination):
    destination = Path(destination).resolve(strict=False)
    if destination.exists() or destination.is_symlink():
        if destination.is_symlink() or not destination.is_dir() or any(destination.iterdir()):
            raise FileExistsError('Restore destination must not exist or must be an empty directory')
    return destination


def restore_encrypted_backup(encrypted_path, destination_vault, passphrase):
    encrypted_path = Path(encrypted_path).resolve()
    destination = _destination_available(destination_vault)
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage, bundle = _decrypt_bundle(encrypted_path, destination.parent, passphrase)
    try:
        result = restore_portable_backup(bundle, destination)
        result.update(format=FORMAT, encrypted=True, encrypted_backup=str(encrypted_path))
        return result
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def _prompt_new_passphrase():
    first = getpass.getpass('Encrypted backup passphrase: ')
    second = getpass.getpass('Confirm passphrase: ')
    if first != second:
        raise EncryptedBackupError('Passphrases do not match')
    if not first:
        raise EncryptedBackupError('Backup passphrase must not be empty')
    return first


def main(argv=None):
    parser = argparse.ArgumentParser(description='HumanOS encrypted portable vault backup/restore')
    sub = parser.add_subparsers(dest='command', required=True)
    backup = sub.add_parser('backup')
    backup.add_argument('vault')
    backup.add_argument('destination')
    verify = sub.add_parser('verify')
    verify.add_argument('encrypted_backup')
    restore = sub.add_parser('restore')
    restore.add_argument('encrypted_backup')
    restore.add_argument('destination_vault')
    args = parser.parse_args(argv)
    if args.command == 'backup':
        result = create_encrypted_backup(args.vault, args.destination, _prompt_new_passphrase())
    elif args.command == 'verify':
        result = verify_encrypted_backup(args.encrypted_backup, getpass.getpass('Encrypted backup passphrase: '))
    else:
        result = restore_encrypted_backup(args.encrypted_backup, args.destination_vault,
                                          getpass.getpass('Encrypted backup passphrase: '))
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
