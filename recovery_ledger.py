"""Crash-safe physical-record parsing for the HumanOS recovery fallback ledger.

SQLite remains authoritative. This module never rewrites recovery.jsonl; it only
parses complete physical LF-delimited records and preserves a suspect final tail
in an owner-local forensic quarantine artifact.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Optional
import uuid

TAIL_SIZE_LIMIT = 8 * 1024 * 1024
QUARANTINE_SCHEMA = 'humanos-recovery-quarantine-v1'


class RecoveryLedgerCorrupt(RuntimeError):
    pass


@dataclass(frozen=True)
class RecoveryParseResult:
    records: tuple
    anomaly: Optional[dict] = None
    quarantine: Optional[dict] = None


def _fsync_directory(path):
    if os.name != 'posix':
        return
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _write_new_file(path, data):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(str(path), flags, 0o600)
    try:
        offset = 0
        while offset < len(data):
            count = os.write(fd, data[offset:])
            if count <= 0:
                raise OSError('short recovery quarantine write')
            offset += count
        os.fsync(fd)
    finally:
        os.close(fd)


def _decode_object(raw, *, offset, location):
    if b'\r' in raw:
        raise RecoveryLedgerCorrupt(
            f'Recovery ledger contains an unexpected carriage return in {location} at byte offset {offset}'
        )
    try:
        text = raw.decode('utf-8', errors='strict')
    except UnicodeDecodeError as error:
        raise RecoveryLedgerCorrupt(
            f'Recovery ledger contains invalid UTF-8 in {location} at byte offset {offset}'
        ) from error
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise RecoveryLedgerCorrupt(
            f'Recovery ledger contains malformed JSON in {location} at byte offset {offset}'
        ) from error
    if not isinstance(value, dict):
        raise RecoveryLedgerCorrupt(
            f'Recovery ledger record in {location} at byte offset {offset} is not a JSON object'
        )
    return value


def validate_recovery_appendable_bytes(raw):
    """Fail closed unless existing bytes are a complete LF-terminated valid ledger."""
    if not raw:
        return True
    if not raw.endswith(b'\n'):
        raise RecoveryLedgerCorrupt(
            'Recovery ledger ends with an unterminated physical record; refusing to append until owner reconciliation'
        )
    offset = 0
    for index, line in enumerate(raw.split(b'\n')[:-1]):
        if not line:
            raise RecoveryLedgerCorrupt(
                f'Recovery ledger contains a blank complete record at byte offset {offset}'
            )
        _decode_object(line, offset=offset, location=f'complete record {index}')
        offset += len(line) + 1
    return True


def _quarantine_tail(source, raw, tail, offset, classification, error_message):
    source = Path(source)
    root = source.parent / 'recovery-quarantine'
    if root.exists() and (root.is_symlink() or not root.is_dir()):
        raise RecoveryLedgerCorrupt('Recovery quarantine path is not a safe directory')
    root.mkdir(parents=True, exist_ok=True, mode=0o700)

    tail_sha = hashlib.sha256(tail).hexdigest()
    key = f'{offset:016x}-{tail_sha}'
    final = root / key
    metadata = {
        'schema': QUARANTINE_SCHEMA,
        'source_path': 'runtime/recovery.jsonl',
        'source_size_bytes': len(raw),
        'tail_offset_bytes': offset,
        'tail_length_bytes': len(tail),
        'tail_sha256': tail_sha,
        'classification': classification,
        'error_message': str(error_message),
        'detected_at_utc': datetime.now(timezone.utc).isoformat(),
    }

    if final.exists():
        if final.is_symlink() or not final.is_dir():
            raise RecoveryLedgerCorrupt('Existing recovery quarantine artifact is unsafe')
        try:
            existing_tail = (final / 'tail.bin').read_bytes()
            existing = json.loads((final / 'metadata.json').read_text(encoding='utf-8'))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise RecoveryLedgerCorrupt('Existing recovery quarantine artifact is unreadable') from error
        if (existing_tail != tail or existing.get('tail_offset_bytes') != offset
                or existing.get('tail_length_bytes') != len(tail)
                or existing.get('tail_sha256') != tail_sha):
            raise RecoveryLedgerCorrupt('Existing recovery quarantine artifact does not match suspect bytes')
        return existing

    pending = root / ('.' + key + '.pending-' + uuid.uuid4().hex)
    pending.mkdir(mode=0o700)
    _write_new_file(pending / 'tail.bin', tail)
    encoded = (json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode('utf-8')
    _write_new_file(pending / 'metadata.json', encoded)
    _fsync_directory(pending)
    try:
        os.rename(pending, final)
    except FileExistsError:
        # A same-content artifact won a race. The original evidence is untouched;
        # validate the durable artifact on the next parser invocation.
        return _quarantine_tail(source, raw, tail, offset, classification, error_message)
    _fsync_directory(root)
    return metadata


def parse_recovery_file(path):
    """Parse recovery.jsonl by physical LF bytes without mutating the source file."""
    path = Path(path)
    if not path.exists():
        return RecoveryParseResult(())
    raw = path.read_bytes()
    if not raw:
        return RecoveryParseResult(())

    parts = raw.split(b'\n')
    terminated = raw.endswith(b'\n')
    complete_lines = parts[:-1]
    tail = b'' if terminated else parts[-1]

    records = []
    offset = 0
    for index, line in enumerate(complete_lines):
        if not line:
            raise RecoveryLedgerCorrupt(
                f'Recovery ledger contains a blank complete record at byte offset {offset}'
            )
        records.append(_decode_object(line, offset=offset, location=f'complete record {index}'))
        offset += len(line) + 1

    if not tail:
        return RecoveryParseResult(tuple(records))

    tail_offset = len(raw) - len(tail)
    if len(tail) > TAIL_SIZE_LIMIT:
        quarantine = _quarantine_tail(
            path, raw, tail, tail_offset, 'OVERSIZE_FINAL_TAIL',
            f'final physical record exceeds {TAIL_SIZE_LIMIT} bytes',
        )
        return RecoveryParseResult(tuple(records), quarantine=quarantine)

    if b'\r' in tail:
        quarantine = _quarantine_tail(
            path, raw, tail, tail_offset, 'UNEXPECTED_CR_FINAL_TAIL',
            'unexpected carriage return in final physical record',
        )
        return RecoveryParseResult(tuple(records), quarantine=quarantine)

    try:
        text = tail.decode('utf-8', errors='strict')
    except UnicodeDecodeError as error:
        quarantine = _quarantine_tail(
            path, raw, tail, tail_offset, 'INVALID_UTF8_FINAL_TAIL', str(error),
        )
        return RecoveryParseResult(tuple(records), quarantine=quarantine)

    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        quarantine = _quarantine_tail(
            path, raw, tail, tail_offset, 'MALFORMED_JSON_FINAL_TAIL', str(error),
        )
        return RecoveryParseResult(tuple(records), quarantine=quarantine)

    if not isinstance(value, dict):
        quarantine = _quarantine_tail(
            path, raw, tail, tail_offset, 'NON_OBJECT_FINAL_TAIL',
            'final physical record is valid JSON but not a JSON object',
        )
        return RecoveryParseResult(tuple(records), quarantine=quarantine)

    records.append(value)
    anomaly = {
        'source_path': 'runtime/recovery.jsonl',
        'tail_offset_bytes': tail_offset,
        'tail_length_bytes': len(tail),
        'classification': 'VALID_UNTERMINATED_FINAL_RECORD',
    }
    return RecoveryParseResult(tuple(records), anomaly=anomaly)
