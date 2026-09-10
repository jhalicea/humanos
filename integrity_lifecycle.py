"""Vault-scoped integrity-key lifecycle for HumanOS.

The key is stable vault identity. This module creates it once for a fresh vault,
refuses silent replacement on protected state, validates owner-only file safety,
and binds the key identity into SQLite before recovery code may mutate state.
"""
import hashlib
import hmac
import os
from pathlib import Path
import sqlite3
import stat

KEY_BYTES = 32
KEY_FILE = 'integrity.key'
KEY_ID_LABEL = b'HumanOS integrity key identity v1'
KEY_ID_PREFIX = 'key-hmac-sha256:'
CONTENT_DIGEST_PREFIX = 'hmac-sha256:'


class IntegrityKeyError(RuntimeError):
    pass


def key_id(key):
    if not isinstance(key, (bytes, bytearray)) or len(key) != KEY_BYTES:
        raise IntegrityKeyError('Notebook integrity key is invalid')
    return KEY_ID_PREFIX + hmac.new(bytes(key), KEY_ID_LABEL, hashlib.sha256).hexdigest()


def _existing_runtime_state(root):
    root = Path(root)
    if not root.exists():
        return False
    for item in root.iterdir():
        if item.name in ('writer.lock', KEY_FILE):
            continue
        return True
    return False


def _validate_private_regular(path, *, expected_bytes=None):
    path = Path(path)
    try:
        before = path.lstat()
    except FileNotFoundError:
        raise IntegrityKeyError('Notebook integrity key is missing')
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise IntegrityKeyError('Notebook integrity key must be one ordinary non-linked file')
    if os.name == 'posix':
        if before.st_uid != os.getuid():
            raise IntegrityKeyError('Notebook integrity key must be owned by the current user')
        if stat.S_IMODE(before.st_mode) & 0o077:
            raise IntegrityKeyError('Notebook integrity key permissions are unsafe; require owner-only access')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(str(path), flags)
    try:
        after = os.fstat(fd)
        if not stat.S_ISREG(after.st_mode) or after.st_nlink != 1:
            raise IntegrityKeyError('Notebook integrity key changed identity while opening')
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise IntegrityKeyError('Notebook integrity key changed identity while opening')
        data = bytearray()
        while True:
            block = os.read(fd, 4096)
            if not block:
                break
            data.extend(block)
            if expected_bytes is not None and len(data) > expected_bytes:
                break
    finally:
        os.close(fd)
    if expected_bytes is not None and len(data) != expected_bytes:
        raise IntegrityKeyError('Notebook integrity key is invalid')
    return bytes(data)


def _fsync_directory(path):
    if os.name != 'posix':
        return
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _legacy_runtime_can_initialize_key(root):
    """Return True only when existing SQLite state is provably pre-key legacy data.

    A legacy database may contain historical SHA-256 rows or only an old recovery
    table. If any runtime_meta binding or HMAC-tagged value already exists, key loss
    is unrecoverable without the original key and we must fail closed.
    """
    path = Path(root) / 'notebook.sqlite3'
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        return False
    try:
        db = sqlite3.connect('file:' + str(path) + '?mode=ro', uri=True)
        try:
            if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                return False
            tables = {row[0] for row in db.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            if 'runtime_meta' in tables:
                return False
            if 'transcript' in tables and db.execute(
                    'SELECT 1 FROM transcript WHERE sha256 LIKE ? LIMIT 1',
                    (CONTENT_DIGEST_PREFIX + '%',)).fetchone():
                return False
            if 'identities' in tables and db.execute(
                    'SELECT 1 FROM identities WHERE opening_hash LIKE ? LIMIT 1',
                    (CONTENT_DIGEST_PREFIX + '%',)).fetchone():
                return False
            if 'events' in tables and db.execute(
                    'SELECT 1 FROM events WHERE payload LIKE ? LIMIT 1',
                    ('%' + CONTENT_DIGEST_PREFIX + '%',)).fetchone():
                return False
            return True
        finally:
            db.close()
    except (sqlite3.DatabaseError, OSError):
        return False


def load_or_create_integrity_key(root):
    """Load a safe key, create one for fresh or provably pre-key legacy state only."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = root / KEY_FILE
    try:
        path.lstat()
        exists = True
    except FileNotFoundError:
        exists = False
    if exists:
        return _validate_private_regular(path, expected_bytes=KEY_BYTES)
    if _existing_runtime_state(root) and not _legacy_runtime_can_initialize_key(root):
        raise IntegrityKeyError(
            'Notebook integrity key is missing from an existing protected vault; restore the original key or a verified backup. '
            'A replacement key will not be generated.')
    key = os.urandom(KEY_BYTES)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(str(path), flags, 0o600)
    try:
        written = 0
        while written < len(key):
            count = os.write(fd, key[written:])
            if count <= 0:
                raise OSError('short integrity-key write')
            written += count
        os.fsync(fd)
    except BaseException:
        os.close(fd)
        try:
            path.unlink()
        except OSError:
            pass
        raise
    else:
        os.close(fd)
    _fsync_directory(root)
    return _validate_private_regular(path, expected_bytes=KEY_BYTES)


def _digest_matches(key, stored, text):
    if not isinstance(stored, str) or not stored.startswith(CONTENT_DIGEST_PREFIX):
        return True
    expected = CONTENT_DIGEST_PREFIX + hmac.new(key, text.encode('utf-8'), hashlib.sha256).hexdigest()
    return hmac.compare_digest(stored, expected)


def _verify_existing_hmac_rows(db, key):
    """Validate pre-metadata HMAC rows before accepting a key during migration."""
    try:
        rows = db.execute('SELECT text,sha256 FROM transcript WHERE sha256 LIKE ?',
                          (CONTENT_DIGEST_PREFIX + '%',))
    except sqlite3.OperationalError:
        return
    for row in rows:
        if not _digest_matches(key, row[1], row[0]):
            raise IntegrityKeyError('Notebook integrity key does not match existing protected transcript evidence')


def bind_integrity_key(db, key):
    """Bind key identity to this SQLite vault before recover() can write anything.

    Existing Runtime 0.1 databases have no runtime_meta table. We first validate any
    HMAC transcript rows with the supplied key, then create the binding. Legacy-only
    databases have no key-dependent rows, so their existing/generated migration key
    becomes authoritative for all future protected records.
    """
    expected = key_id(key)
    try:
        row = db.execute("SELECT value FROM runtime_meta WHERE key='integrity_key_id'").fetchone()
    except sqlite3.OperationalError as error:
        if 'no such table' not in str(error).casefold():
            raise
        _verify_existing_hmac_rows(db, key)
        with db:
            db.execute('CREATE TABLE runtime_meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)')
            db.execute('INSERT INTO runtime_meta(key,value) VALUES(?,?)', ('integrity_key_id', expected))
            db.execute('INSERT INTO runtime_meta(key,value) VALUES(?,?)', ('integrity_key_policy', 'stable-v1-no-auto-rotation'))
        return expected
    if row is None:
        _verify_existing_hmac_rows(db, key)
        with db:
            db.execute('INSERT INTO runtime_meta(key,value) VALUES(?,?)', ('integrity_key_id', expected))
            db.execute('INSERT OR REPLACE INTO runtime_meta(key,value) VALUES(?,?)',
                       ('integrity_key_policy', 'stable-v1-no-auto-rotation'))
        return expected
    if not hmac.compare_digest(row[0], expected):
        raise IntegrityKeyError('Notebook integrity key identity does not match this vault')
    return expected
