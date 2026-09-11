"""Crash-safe physical-record parsing for the HumanOS recovery fallback ledger.

SQLite remains authoritative. This module never rewrites recovery.jsonl; it only
parses complete physical LF-delimited records and preserves a suspect final tail
in an owner-local forensic quarantine artifact.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import uuid

TAIL_SIZE_LIMIT = 8 * 1024 * 1024
QUARANTINE_SCHEMA = 'humanos-recovery-quarantine-v1'


class RecoveryLedgerCorrupt(RuntimeError):
    pass


@dataclass(frozen=True)
class RecoveryParseResult:
    records: tuple
    anomaly: dict | None = None
    quarantine: dict | None = None


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
                raise OSError('short write')
            offset += count
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_directory(path.parent)


def _parse_line(raw, line_number):
    try:
        value = json.loads(raw)
    except (TypeError, ValueError) as error:
        raise RecoveryLedgerCorrupt('Recovery record is invalid JSON at line ' + str(line_number)) from error
    if not isinstance(value, dict):
        raise RecoveryLedgerCorrupt('Recovery record must be an object at line ' + str(line_number))
    return value


def parse_recovery_file(path):
    path = Path(path)
    if not path.exists():
        return RecoveryParseResult(())
    raw = path.read_bytes()
    if len(raw) > TAIL_SIZE_LIMIT:
        raise RecoveryLedgerCorrupt('Recovery ledger exceeds bounded parse size')
    if raw and not raw.endswith(b'\n'):
        return RecoveryParseResult((), {'kind': 'TRUNCATED_FINAL_RECORD', 'bytes': len(raw)}, None)
    lines = raw.decode('utf-8').splitlines()
    return RecoveryParseResult(tuple(_parse_line(line, i) for i, line in enumerate(lines, 1)))


def validate_recovery_appendable_bytes(raw):
    if not isinstance(raw, bytes):
        raise TypeError('Recovery bytes must be bytes')
    if raw and not raw.endswith(b'\n'):
        raise RecoveryLedgerCorrupt('Recovery ledger has an incomplete final record')
    return parse_recovery_file_from_bytes(raw)


def parse_recovery_file_from_bytes(raw):
    if len(raw) > TAIL_SIZE_LIMIT:
        raise RecoveryLedgerCorrupt('Recovery ledger exceeds bounded parse size')
    if not raw:
        return RecoveryParseResult(())
    lines = raw.decode('utf-8').splitlines()
    return RecoveryParseResult(tuple(_parse_line(line, i) for i, line in enumerate(lines, 1)))


def quarantine_tail(path, raw_tail, reason='TRUNCATED_FINAL_RECORD'):
    path = Path(path)
    if len(raw_tail) > TAIL_SIZE_LIMIT:
        raise RecoveryLedgerCorrupt('Recovery tail exceeds bounded size')
    record = {'schema': QUARANTINE_SCHEMA, 'reason': reason, 'tail_sha256': hashlib.sha256(raw_tail).hexdigest(),
              'bytes': len(raw_tail), 'created': datetime.now(timezone.utc).isoformat()}
    target = path.with_name(path.name + '.quarantine-' + uuid.uuid4().hex)
    _write_new_file(target, json.dumps(record, sort_keys=True).encode('utf-8') + b'\n')
    return record
