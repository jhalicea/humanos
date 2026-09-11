"""Explicit, authenticated continuation for a sealed HumanOS recovery ledger.

This module never runs automatically. A sealed recovery.jsonl is first preserved
as exact bytes in a durable archive. Only then is the active path replaced with a
new LF-terminated continuation header whose lineage is HMAC-authenticated under
the existing vault integrity key. Raw SHA-256 is retained only as a forensic
checksum of the predecessor bytes.
"""
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import stat
import uuid

from recovery_ledger import parse_recovery_file

CONTINUATION_SCHEMA = 'humanos-recovery-continuation-v1'
CONTINUATION_DOMAIN = b'HumanOS recovery ledger continuation v1\x00'
CONTINUATION_PROOF_PREFIX = 'hmac-sha256-continuation-v1:'
ARCHIVE_DIR = 'recovery-archive'


class ContinuationError(RuntimeError):
    pass


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def _fsync_directory(path):
    if os.name != 'posix':
        return
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _write_new_file(path, data):
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    try:
        offset = 0
        while offset < len(data):
            count = os.write(fd, data[offset:])
            if count <= 0:
                raise OSError('short recovery continuation write')
            offset += count
        os.fsync(fd)
    finally:
        os.close(fd)


def _read_private_regular(path):
    path = Path(path)
    try:
        before = path.lstat()
    except FileNotFoundError as error:
        raise ContinuationError('Recovery continuation artifact is missing: ' + path.name) from error
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise ContinuationError('Recovery continuation artifact must be one ordinary non-linked file: ' + path.name)
    if os.name == 'posix':
        if before.st_uid != os.getuid():
            raise ContinuationError('Recovery continuation artifact is not owned by the current user: ' + path.name)
        if stat.S_IMODE(before.st_mode) & 0o077:
            raise ContinuationError('Recovery continuation artifact permissions are unsafe: ' + path.name)
    fd = os.open(str(path), os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    try:
        after = os.fstat(fd)
        if not stat.S_ISREG(after.st_mode) or after.st_nlink != 1:
            raise ContinuationError('Recovery continuation artifact changed identity while opening: ' + path.name)
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise ContinuationError('Recovery continuation artifact changed identity while opening: ' + path.name)
        chunks = []
        while True:
            block = os.read(fd, 1024 * 1024)
            if not block:
                break
            chunks.append(block)
    finally:
        os.close(fd)
    return b''.join(chunks)


def _proof(key, unsigned):
    if not isinstance(key, (bytes, bytearray)) or not key:
        raise ContinuationError('Recovery continuation requires the bound vault integrity key')
    mac = hmac.new(bytes(key), CONTINUATION_DOMAIN + _canonical(unsigned).encode('utf-8'), hashlib.sha256).hexdigest()
    return CONTINUATION_PROOF_PREFIX + mac


def _manifest_for(raw, classification, key, created=None):
    forensic_sha = hashlib.sha256(raw).hexdigest()
    continuation_id = 'cont-' + forensic_sha
    created = created or datetime.now(timezone.utc).isoformat()
    unsigned = {
        'schema': CONTINUATION_SCHEMA,
        'continuation_id': continuation_id,
        'created_at_utc': created,
        'predecessor_path': 'recovery.jsonl',
        'archive_path': ARCHIVE_DIR + '/' + continuation_id,
        'predecessor_bytes': len(raw),
        'predecessor_forensic_sha256': forensic_sha,
        'predecessor_state': classification,
    }
    return dict(unsigned, link_proof=_proof(key, unsigned))


def _verify_manifest(manifest, key):
    required = {
        'schema', 'continuation_id', 'created_at_utc', 'predecessor_path',
        'archive_path', 'predecessor_bytes', 'predecessor_forensic_sha256',
        'predecessor_state', 'link_proof',
    }
    if not isinstance(manifest, dict) or set(manifest) != required:
        raise ContinuationError('Recovery continuation manifest is malformed')
    if manifest['schema'] != CONTINUATION_SCHEMA or manifest['predecessor_path'] != 'recovery.jsonl':
        raise ContinuationError('Recovery continuation manifest identity is invalid')
    expected_id = 'cont-' + str(manifest['predecessor_forensic_sha256'])
    expected_path = ARCHIVE_DIR + '/' + expected_id
    if manifest['continuation_id'] != expected_id or manifest['archive_path'] != expected_path:
        raise ContinuationError('Recovery continuation archive identity is invalid')
    if (isinstance(manifest['predecessor_bytes'], bool)
            or not isinstance(manifest['predecessor_bytes'], int)
            or manifest['predecessor_bytes'] < 1):
        raise ContinuationError('Recovery continuation predecessor size is invalid')
    unsigned = {key_name: value for key_name, value in manifest.items() if key_name != 'link_proof'}
    expected = _proof(key, unsigned)
    if not isinstance(manifest['link_proof'], str) or not hmac.compare_digest(manifest['link_proof'], expected):
        raise ContinuationError('Recovery continuation authentication failed')
    return manifest


def _load_archive(root, continuation_id, key):
    root = Path(root)
    archive = root / ARCHIVE_DIR / continuation_id
    if not archive.exists() or archive.is_symlink() or not archive.is_dir():
        raise ContinuationError('Recovery continuation archive is missing or unsafe')
    if os.name == 'posix':
        info = archive.stat()
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise ContinuationError('Recovery continuation archive permissions are unsafe')
    archived = _read_private_regular(archive / 'recovery.jsonl')
    stored_manifest_raw = _read_private_regular(archive / 'manifest.json')
    try:
        stored_manifest = json.loads(stored_manifest_raw.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ContinuationError('Recovery continuation archive manifest is unreadable') from error
    _verify_manifest(stored_manifest, key)
    if stored_manifest['continuation_id'] != continuation_id:
        raise ContinuationError('Recovery continuation archive manifest has the wrong identity')
    if len(archived) != stored_manifest['predecessor_bytes']:
        raise ContinuationError('Recovery continuation archive predecessor length mismatch')
    if not hmac.compare_digest(hashlib.sha256(archived).hexdigest(), stored_manifest['predecessor_forensic_sha256']):
        raise ContinuationError('Recovery continuation archive predecessor checksum mismatch')
    return archive, stored_manifest, archived


def _verify_archive(root, manifest, key):
    manifest = _verify_manifest(manifest, key)
    archive, stored_manifest, _ = _load_archive(root, manifest['continuation_id'], key)
    if stored_manifest != manifest:
        raise ContinuationError('Recovery continuation archive manifest differs from active lineage header')
    return archive


def _manifest_from_continuation_record(record, key):
    required = {'tx', 'scope', 'error', 'payload', 'created'}
    if not isinstance(record, dict) or set(record) != required:
        raise ContinuationError('Recovery continuation header is malformed')
    if record.get('scope') != 'LEDGER_CONTINUATION' or record.get('tx') is not None:
        raise ContinuationError('Recovery continuation header identity is invalid')
    if record.get('error') != 'Owner-authorized recovery ledger continuation':
        raise ContinuationError('Recovery continuation header description is invalid')
    manifest = _verify_manifest(record.get('payload'), key)
    if record.get('created') != manifest['created_at_utc']:
        raise ContinuationError('Recovery continuation header timestamp differs from authenticated manifest')
    return manifest


def verify_active_recovery_continuation(runtime_root, integrity_key):
    """Verify an active continuation header and its immediate archived predecessor on every open.

    Ordinary non-continuation or currently sealed ledgers are left to recovery_ledger.py.
    A recognized continuation header is never accepted without its HMAC-authenticated archive.
    """
    root = Path(runtime_root)
    active = root / 'recovery.jsonl'
    if not active.exists():
        return None
    raw = _read_private_regular(active)
    newline = raw.find(b'\n')
    if newline < 0:
        return None
    first_raw = raw[:newline]
    if not first_raw:
        return None
    try:
        first = json.loads(first_raw.decode('utf-8', errors='strict'))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(first, dict) or first.get('scope') != 'LEDGER_CONTINUATION':
        return None
    manifest = _manifest_from_continuation_record(first, integrity_key)
    _verify_archive(root, manifest, integrity_key)
    return manifest


def _existing_continuation(root, records, key):
    if not records:
        return None
    first = records[0]
    if first.get('scope') != 'LEDGER_CONTINUATION':
        return None
    manifest = _manifest_from_continuation_record(first, key)
    _verify_archive(root, manifest, key)
    return {
        'continued': True,
        'already_continued': True,
        'continuation_id': manifest['continuation_id'],
        'archive_path': manifest['archive_path'],
        'predecessor_bytes': manifest['predecessor_bytes'],
        'predecessor_forensic_sha256': manifest['predecessor_forensic_sha256'],
        'link_proof': manifest['link_proof'],
    }


def _ensure_archive(root, raw, manifest, key):
    root = Path(root)
    archive_parent = root / ARCHIVE_DIR
    created_parent = not archive_parent.exists()
    if not created_parent and (archive_parent.is_symlink() or not archive_parent.is_dir()):
        raise ContinuationError('Recovery continuation archive root is unsafe')
    archive_parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == 'posix':
        info = archive_parent.stat()
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise ContinuationError('Recovery continuation archive root permissions are unsafe')
    if created_parent:
        _fsync_directory(root)

    final = root / manifest['archive_path']
    if final.exists():
        _, stored_manifest, archived = _load_archive(root, manifest['continuation_id'], key)
        if archived != raw:
            raise ContinuationError('Existing recovery continuation archive does not match sealed ledger bytes')
        return stored_manifest

    pending = archive_parent / ('.' + manifest['continuation_id'] + '.pending-' + uuid.uuid4().hex)
    pending.mkdir(mode=0o700)
    try:
        _write_new_file(pending / 'recovery.jsonl', raw)
        encoded_manifest = (_canonical(manifest) + '\n').encode('utf-8')
        _write_new_file(pending / 'manifest.json', encoded_manifest)
        _fsync_directory(pending)
        try:
            os.rename(pending, final)
        except FileExistsError:
            _, stored_manifest, archived = _load_archive(root, manifest['continuation_id'], key)
            if archived != raw:
                raise ContinuationError('Concurrent recovery continuation archive differs from sealed ledger bytes')
            return stored_manifest
        _fsync_directory(archive_parent)
    finally:
        if pending.exists():
            try:
                for child in pending.iterdir():
                    child.unlink()
                pending.rmdir()
            except OSError:
                pass
    return manifest


def continue_recovery_ledger(runtime_root, integrity_key):
    """Explicitly archive one sealed ledger and open a fresh authenticated continuation."""
    root = Path(runtime_root)
    active = root / 'recovery.jsonl'
    if not active.exists():
        raise ContinuationError('Recovery ledger does not exist')

    parsed = parse_recovery_file(active)
    if not parsed.anomaly and not parsed.quarantine:
        existing = _existing_continuation(root, parsed.records, integrity_key)
        if existing:
            return existing
        raise ContinuationError('Recovery ledger is not sealed; continuation is unnecessary')

    raw = _read_private_regular(active)
    classification = (parsed.quarantine or parsed.anomaly or {}).get('classification', 'SEALED_FINAL_RECORD')
    manifest = _manifest_for(raw, classification, integrity_key)
    manifest = _ensure_archive(root, raw, manifest, integrity_key)

    header = {
        'tx': None,
        'scope': 'LEDGER_CONTINUATION',
        'error': 'Owner-authorized recovery ledger continuation',
        'payload': manifest,
        'created': manifest['created_at_utc'],
    }
    new_active = (_canonical(header) + '\n').encode('utf-8')
    pending_active = root / ('.recovery.jsonl.continue-' + manifest['continuation_id'] + '-' + uuid.uuid4().hex)
    _write_new_file(pending_active, new_active)
    try:
        current = _read_private_regular(active)
        if current != raw:
            raise ContinuationError('Recovery ledger changed after archive verification; refusing continuation')
        os.replace(pending_active, active)
        _fsync_directory(root)
    finally:
        if pending_active.exists():
            try:
                pending_active.unlink()
            except OSError:
                pass

    return {
        'continued': True,
        'already_continued': False,
        'continuation_id': manifest['continuation_id'],
        'archive_path': manifest['archive_path'],
        'predecessor_bytes': manifest['predecessor_bytes'],
        'predecessor_forensic_sha256': manifest['predecessor_forensic_sha256'],
        'link_proof': manifest['link_proof'],
    }
