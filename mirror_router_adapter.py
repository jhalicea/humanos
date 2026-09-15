"""Thin Mirror-facing adapter for the HumanOS model router.

Learning mode only. This module emits and can persist routing recommendations.
It never dispatches a model, grants authority, or promotes experimental workflows
into policy.
"""
from __future__ import annotations

from contextlib import contextmanager
import json
import os
import stat
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import fcntl
except ImportError:  # pragma: no cover - current supported local targets are POSIX
    fcntl = None

from audit import AuditEvent, canonical_json, hash_event, verify_chain
from model_router import TaskProfile, route_task
from recovery_ledger import RecoveryLedgerCorrupt, validate_recovery_appendable_bytes

ROUTING_EVENT_SCHEMA = "routing-event-v0"


class RoutingLedgerError(RuntimeError):
    pass


class RoutingLedgerUnsafe(RoutingLedgerError):
    pass


class RoutingLedgerCorrupt(RoutingLedgerError):
    pass


class RoutingLedgerConflict(RoutingLedgerError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fsync_directory(path: Path) -> None:
    if os.name != "posix":
        return
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _ensure_directory(path: Path) -> None:
    if path.exists():
        if path.is_symlink() or not path.is_dir():
            raise RoutingLedgerUnsafe("routing ledger directory is not a safe directory")
        return
    path.mkdir(parents=True, mode=0o700)
    if path.is_symlink() or not path.is_dir():
        raise RoutingLedgerUnsafe("routing ledger directory is not a safe directory")


def _reject_symlink_path(path: Path) -> None:
    if path.is_symlink():
        raise RoutingLedgerUnsafe("routing ledger path must not be a symlink")
    if path.exists() and not path.is_file():
        raise RoutingLedgerUnsafe("routing ledger path must be a regular file")


def _safe_open(path: Path, flags: int, mode: int = 0o600) -> int:
    _reject_symlink_path(path)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(str(path), flags, mode)
    except OSError as error:
        raise RoutingLedgerUnsafe(f"unable to open routing ledger safely: {error}") from error
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode):
        os.close(fd)
        raise RoutingLedgerUnsafe("routing ledger path is not a regular file")
    return fd


def build_mirror_routing_event(
    task: TaskProfile,
    *,
    event_id: Optional[str] = None,
    created_at: Optional[str] = None,
) -> dict:
    """Return a Mirror-consumable recommendation with zero execution authority."""
    recommendation = route_task(task)
    return {
        "schema_version": ROUTING_EVENT_SCHEMA,
        "event_id": event_id or f"route-{uuid.uuid4()}",
        "created_at": created_at or _utc_now(),
        "event_type": "MODEL_ROUTING_RECOMMENDATION",
        "status": "PROPOSED",
        "task_id": task.task_id,
        "task_profile": asdict(task),
        "recommendation": recommendation,
        "dispatch_allowed": False,
        "automatic_execution": False,
        "authority_granted": False,
        "policy_promotion": False,
    }


class RoutingEventLedger:
    """Append-only JSONL routing ledger with fail-closed local durability controls."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.root = self.path.parent
        self.lock_path = self.root / ".routing-events.lock"

    def _prepare_root(self) -> None:
        _ensure_directory(self.root)
        _reject_symlink_path(self.path)
        if self.lock_path.is_symlink():
            raise RoutingLedgerUnsafe("routing ledger lock path must not be a symlink")

    @contextmanager
    def _lock(self, *, exclusive: bool):
        if fcntl is None:
            raise RoutingLedgerUnsafe("routing ledger single-writer locking is unavailable on this platform")
        self._prepare_root()
        fd = _safe_open(self.lock_path, os.O_RDWR | os.O_CREAT)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH)
            yield
        finally:
            try:
                fcntl.flock(fd, fcntl.LOCK_UN)
            finally:
                os.close(fd)

    def _read_raw_unlocked(self) -> bytes:
        if not self.path.exists():
            return b""
        _reject_symlink_path(self.path)
        try:
            raw = self.path.read_bytes()
            validate_recovery_appendable_bytes(raw)
        except RecoveryLedgerCorrupt as error:
            raise RoutingLedgerCorrupt(str(error)) from error
        except OSError as error:
            raise RoutingLedgerUnsafe(f"unable to read routing ledger safely: {error}") from error
        return raw

    def _read_all_unlocked(self) -> list[AuditEvent]:
        raw = self._read_raw_unlocked()
        if not raw:
            return []
        events: list[AuditEvent] = []
        for line in raw.split(b"\n")[:-1]:
            try:
                value = json.loads(line.decode("utf-8", errors="strict"))
                events.append(AuditEvent(**value))
            except (UnicodeDecodeError, json.JSONDecodeError, TypeError, KeyError) as error:
                raise RoutingLedgerCorrupt("routing ledger contains an invalid audit record") from error
        return events

    def read_all(self) -> list[AuditEvent]:
        with self._lock(exclusive=False):
            return self._read_all_unlocked()

    def _append_bytes_unlocked(self, data: bytes) -> None:
        existed = self.path.exists()
        fd = _safe_open(self.path, os.O_WRONLY | os.O_APPEND | os.O_CREAT)
        try:
            offset = 0
            while offset < len(data):
                count = os.write(fd, data[offset:])
                if count <= 0:
                    raise OSError("short routing-ledger write")
                offset += count
            os.fsync(fd)
        finally:
            os.close(fd)
        if not existed:
            _fsync_directory(self.root)

    def append(self, *, action_id: str, body: dict) -> AuditEvent:
        """Append once by action_id; identical retries are idempotent, conflicts fail closed."""
        with self._lock(exclusive=True):
            events = self._read_all_unlocked()
            if events and not verify_chain(events):
                raise RoutingLedgerCorrupt("routing event ledger failed hash-chain verification")

            for existing in events:
                if existing.action_id != action_id:
                    continue
                if existing.body == body:
                    return existing
                raise RoutingLedgerConflict("routing event id already exists with different content")

            seq = len(events) + 1
            previous_hash = events[-1].event_hash if events else "GENESIS"
            event_type = "MODEL_ROUTING_RECOMMENDATION"
            event_hash = hash_event(seq, event_type, action_id, body, previous_hash)
            event = AuditEvent(
                seq=seq,
                event_type=event_type,
                action_id=action_id,
                body=body,
                previous_hash=previous_hash,
                event_hash=event_hash,
            )
            encoded = (canonical_json(asdict(event)) + "\n").encode("utf-8")
            self._append_bytes_unlocked(encoded)
            return event

    def verify(self) -> bool:
        try:
            return verify_chain(self.read_all())
        except RoutingLedgerError:
            return False


def route_for_mirror(
    task: TaskProfile,
    *,
    ledger: Optional[RoutingEventLedger] = None,
    event_id: Optional[str] = None,
    created_at: Optional[str] = None,
) -> dict:
    """Emit a recommendation and optionally record it; never execute the route."""
    event = build_mirror_routing_event(
        task,
        event_id=event_id,
        created_at=created_at,
    )
    ledger_record = None
    if ledger is not None:
        ledger_record = ledger.append(action_id=event["event_id"], body=event)

    return {
        "routing_event": event,
        "ledger_record": asdict(ledger_record) if ledger_record else None,
        "model_dispatched": False,
        "authority_granted": False,
    }
