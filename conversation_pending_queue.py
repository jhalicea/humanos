"""Provider-neutral durable queue for already-observed conversation events.

This module records facts supplied by an authorized observer.  It does not read
ChatGPT (or another provider), claim that a source was observed, deliver to a
relay, import a Notebook, or create a recovery export.  Those are separate
adapters and projections.

The queue is intentionally small: one immutable event row and one pending row
for each downstream destination are committed in the same local SQLite
transaction.  A successful return means only that this local transaction
committed and was read back; it is not an observation or delivery receipt.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import sqlite3
import stat
from typing import Iterator, Optional, Union


DESTINATIONS = ("relay", "notebook", "recovery_export")
PENDING = "PENDING"
ROLE_HUMAN = "human"
ROLE_ASSISTANT = "assistant"


class PendingQueueError(RuntimeError):
    """Base class for queue errors."""


class EventConflictError(PendingQueueError):
    """The event identity was reused for different immutable evidence."""


class QueueClosedError(PendingQueueError):
    """The queue has already been closed."""


@dataclass(frozen=True)
class ObservedConversationEvent:
    """Exact evidence supplied by a caller that has already observed a turn.

    ``content`` is encoded with strict UTF-8 before it is written.  The queue
    derives ``content_hash`` from those bytes, so Unicode normalization and
    replacement decoding are never performed here.
    """

    event_id: str
    conversation_id: str
    source: str
    role: str
    content: str
    observed_timestamp: str
    ordering_evidence: str
    capture_method: str
    privacy_policy_version: str
    source_timestamp: Optional[str] = None
    parent_event_id: Optional[str] = None
    revision_id: Optional[str] = None
    supersedes_event_id: Optional[str] = None


# The shorter name is useful to provider-neutral callers.  The explicit
# ``Observed`` name remains available to make the source-observation boundary
# visible at call sites.
ConversationEvent = ObservedConversationEvent


class ConversationPendingQueue:
    """Durably enqueue complete, already-observed events in a local SQLite DB."""

    def __init__(self, db_path: Union[str, Path]):
        self.path = Path(db_path)
        self._closed = False
        self._prepare_path()
        self.db = sqlite3.connect(str(self.path), timeout=5.0)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA busy_timeout=5000")
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversation_events(
                event_id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                source TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('human','assistant')),
                content_utf8 BLOB NOT NULL,
                content_hash TEXT NOT NULL,
                observed_timestamp TEXT NOT NULL,
                source_timestamp TEXT,
                ordering_evidence TEXT NOT NULL,
                capture_method TEXT NOT NULL,
                parent_event_id TEXT,
                revision_id TEXT,
                supersedes_event_id TEXT,
                privacy_policy_version TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS pending_destinations(
                event_id TEXT NOT NULL REFERENCES conversation_events(event_id)
                    ON DELETE CASCADE,
                destination TEXT NOT NULL CHECK(destination IN
                    ('relay','notebook','recovery_export')),
                status TEXT NOT NULL CHECK(status='PENDING'),
                PRIMARY KEY(event_id, destination)
            );
            """
        )
        self.db.commit()
        # This DB is local queue state, not a public/shared artifact.
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            # The database remains usable on platforms without POSIX modes.
            pass

    def _prepare_path(self) -> None:
        if self.path.exists() or self.path.is_symlink():
            if self.path.is_symlink():
                raise PendingQueueError("queue database path must not be a symlink")
            if not self.path.is_file():
                raise PendingQueueError("queue database path must be a regular file")
        parent = self.path.parent
        if not parent.exists():
            parent.mkdir(parents=True, mode=0o700)
        if parent.is_symlink() or not parent.is_dir():
            raise PendingQueueError("queue database parent must be a real directory")
        parent_mode = stat.S_IMODE(parent.stat().st_mode)
        if parent_mode & 0o077:
            raise PendingQueueError(
                "queue database parent must not grant group or other access"
            )

    def _ensure_open(self) -> None:
        if self._closed:
            raise QueueClosedError("pending queue is closed")

    @staticmethod
    def _required_string(name: str, value: object) -> str:
        if not isinstance(value, str) or not value:
            raise ValueError(name + " must be a nonempty string")
        return value

    @classmethod
    def _validate(cls, event: ObservedConversationEvent) -> bytes:
        if not isinstance(event, ObservedConversationEvent):
            raise TypeError("event must be an ObservedConversationEvent")
        for name in (
            "event_id", "conversation_id", "source", "observed_timestamp",
            "ordering_evidence", "capture_method", "privacy_policy_version",
        ):
            cls._required_string(name, getattr(event, name))
        if event.role not in (ROLE_HUMAN, ROLE_ASSISTANT):
            raise ValueError("role must be 'human' or 'assistant'")
        if not isinstance(event.content, str):
            raise ValueError("content must be a string")
        try:
            content = event.content.encode("utf-8", errors="strict")
        except UnicodeEncodeError as error:
            raise ValueError("content must be valid UTF-8") from error
        for name in (
            "source_timestamp", "parent_event_id", "revision_id",
            "supersedes_event_id",
        ):
            value = getattr(event, name)
            if value is not None:
                cls._required_string(name, value)
        return content

    @contextmanager
    def _write_transaction(self) -> Iterator[sqlite3.Cursor]:
        self._ensure_open()
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield self.db
        except BaseException:
            self.db.rollback()
            raise
        else:
            # No caller-visible receipt is returned until this commit succeeds.
            self.db.commit()

    @staticmethod
    def _event_tuple(row: sqlite3.Row) -> tuple:
        return (
            row["event_id"], row["conversation_id"], row["source"], row["role"],
            bytes(row["content_utf8"]), row["observed_timestamp"],
            row["source_timestamp"], row["ordering_evidence"],
            row["capture_method"], row["parent_event_id"], row["revision_id"],
            row["supersedes_event_id"], row["privacy_policy_version"],
            row["content_hash"],
        )

    @staticmethod
    def _requested_tuple(
        event: ObservedConversationEvent, content: bytes, content_hash: str
    ) -> tuple:
        return (
            event.event_id, event.conversation_id, event.source, event.role, content,
            event.observed_timestamp, event.source_timestamp,
            event.ordering_evidence, event.capture_method, event.parent_event_id,
            event.revision_id, event.supersedes_event_id,
            event.privacy_policy_version, content_hash,
        )

    def _record(self, event_id: str, *, idempotent: bool = False) -> dict:
        row = self.db.execute(
            "SELECT * FROM conversation_events WHERE event_id=?", (event_id,)
        ).fetchone()
        if row is None:
            return None
        content = bytes(row["content_utf8"])
        if hashlib.sha256(content).hexdigest() != row["content_hash"]:
            raise PendingQueueError("event content hash does not match preserved bytes")
        destinations = {
            destination: status
            for destination, status in self.db.execute(
                "SELECT destination,status FROM pending_destinations "
                "WHERE event_id=? ORDER BY destination", (event_id,)
            )
        }
        return {
            "event_id": row["event_id"],
            "conversation_id": row["conversation_id"],
            "source": row["source"],
            "role": row["role"],
            "content": content.decode("utf-8", errors="strict"),
            "content_hash": row["content_hash"],
            "observed_timestamp": row["observed_timestamp"],
            "source_timestamp": row["source_timestamp"],
            "ordering_evidence": row["ordering_evidence"],
            "capture_method": row["capture_method"],
            "parent_event_id": row["parent_event_id"],
            "revision_id": row["revision_id"],
            "supersedes_event_id": row["supersedes_event_id"],
            "privacy_policy_version": row["privacy_policy_version"],
            "destinations": destinations,
            "committed": True,
            "idempotent": idempotent,
        }

    def enqueue(self, event: ObservedConversationEvent) -> dict:
        """Commit one event and all three pending destination rows atomically.

        The returned record is read only after a successful commit.  A repeated
        identical event returns the preserved record with ``idempotent=True``;
        an event-ID collision with any changed immutable field raises
        ``EventConflictError`` and leaves the preserved row untouched.
        """
        content = self._validate(event)
        content_hash = hashlib.sha256(content).hexdigest()
        requested = self._requested_tuple(event, content, content_hash)
        idempotent = False
        with self._write_transaction() as db:
            existing = db.execute(
                "SELECT * FROM conversation_events WHERE event_id=?",
                (event.event_id,),
            ).fetchone()
            if existing is not None:
                if self._event_tuple(existing) != requested:
                    raise EventConflictError(
                        "event ID already exists with different immutable evidence"
                    )
                destination_count = db.execute(
                    "SELECT COUNT(*) FROM pending_destinations WHERE event_id=?",
                    (event.event_id,),
                ).fetchone()[0]
                if destination_count != len(DESTINATIONS):
                    raise PendingQueueError(
                        "existing event has incomplete pending destination state"
                    )
                idempotent = True
            else:
                db.execute(
                    """INSERT INTO conversation_events(
                        event_id,conversation_id,source,role,content_utf8,
                        content_hash,observed_timestamp,source_timestamp,
                        ordering_evidence,capture_method,parent_event_id,
                        revision_id,supersedes_event_id,privacy_policy_version
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        event.event_id, event.conversation_id, event.source,
                        event.role, sqlite3.Binary(content), content_hash,
                        event.observed_timestamp, event.source_timestamp,
                        event.ordering_evidence, event.capture_method,
                        event.parent_event_id, event.revision_id,
                        event.supersedes_event_id, event.privacy_policy_version,
                    ),
                )
                db.executemany(
                    "INSERT INTO pending_destinations(event_id,destination,status) "
                    "VALUES(?,?,?)",
                    [(event.event_id, destination, PENDING)
                     for destination in DESTINATIONS],
                )
        return self._record(event.event_id, idempotent=idempotent)

    def get(self, event_id: str) -> Optional[dict]:
        """Read a committed event and its pending destination state."""
        self._required_string("event_id", event_id)
        self._ensure_open()
        return self._record(event_id)

    def pending_destinations(self, event_id: str) -> dict:
        record = self.get(event_id)
        return {} if record is None else dict(record["destinations"])

    def close(self) -> None:
        if not self._closed:
            self.db.close()
            self._closed = True

    def __enter__(self) -> "ConversationPendingQueue":
        self._ensure_open()
        return self

    def __exit__(self, _type, _value, _traceback) -> None:
        self.close()
