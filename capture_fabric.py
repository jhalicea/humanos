#!/usr/bin/env python3
"""HumanOS Capture Fabric core.

This module defines the provider-neutral event contract used by every capture
route. It deliberately separates *how an event reaches HumanOS* from *what the
event means*.

Production intent:

    provider-native webhook / MCP gateway / direct DB connector / browser bridge
                                  |
                                  v
                         append-only remote relay
                                  |
                                  v
                         local Life Notebook

No language model is used here. The relay is not the canonical Life Notebook;
it is a durable synchronization mailbox. The local Notebook remains the owner-
controlled source of truth after verified import.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import json
import sqlite3
from pathlib import Path
from typing import Any, Callable, Mapping, Optional
import uuid


FORMAT_VERSION = 1
MAX_TEXT_BYTES = 1_000_000
DIGEST_DOMAIN = b'HumanOS Capture Event v1|'
ALLOWED_EVENT_TYPES = frozenset({
    'human_message',
    'assistant_message',
    'human_edit',
    'assistant_regeneration',
})
ALLOWED_ROLES = frozenset({'human', 'assistant'})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: Any) -> str:
    """Stable UTF-8 JSON for local storage and signed test webhook bodies."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def _bounded(name: str, value: Any, maximum: int) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(name + ' must be nonempty text')
    if len(value.encode('utf-8')) > maximum:
        raise ValueError(name + ' is too large')
    return value


def _digest_part(value: Any) -> bytes:
    """Unambiguous length-prefixed UTF-8 field encoding shared with PostgreSQL."""
    if value is None:
        return b'-1:'
    raw = str(value).encode('utf-8')
    return str(len(raw)).encode('ascii') + b':' + raw


@dataclass(frozen=True)
class CaptureEvent:
    """One immutable conversation event.

    ``idempotency_key`` is supplied by the source adapter and must remain stable
    across retries. A repeated key with the same exact event is idempotent; a
    repeated key with different content fails closed.
    """

    source: str
    conversation_id: str
    turn_id: str
    event_type: str
    role: str
    text: str
    idempotency_key: str
    variant_id: str = 'primary'
    source_created_at: Optional[str] = None
    version: int = FORMAT_VERSION

    def validated(self) -> 'CaptureEvent':
        if self.version != FORMAT_VERSION:
            raise ValueError('Unsupported capture event version')
        _bounded('source', self.source, 128)
        _bounded('conversation_id', self.conversation_id, 4096)
        _bounded('turn_id', self.turn_id, 4096)
        _bounded('variant_id', self.variant_id, 4096)
        _bounded('idempotency_key', self.idempotency_key, 4096)
        if self.event_type not in ALLOWED_EVENT_TYPES:
            raise ValueError('Unsupported event_type')
        if self.role not in ALLOWED_ROLES:
            raise ValueError('Unsupported role')
        if self.event_type.startswith('human') and self.role != 'human':
            raise ValueError('Human event must have human role')
        if self.event_type.startswith('assistant') and self.role != 'assistant':
            raise ValueError('Assistant event must have assistant role')
        if not isinstance(self.text, str) or not self.text:
            raise ValueError('text must be nonempty exact text')
        if len(self.text.encode('utf-8')) > MAX_TEXT_BYTES:
            raise ValueError('text is too large')
        if self.source_created_at is not None:
            _bounded('source_created_at', self.source_created_at, 128)
        return self

    def payload(self) -> dict[str, Any]:
        self.validated()
        return {
            'version': self.version,
            'source': self.source,
            'conversation_id': self.conversation_id,
            'turn_id': self.turn_id,
            'event_type': self.event_type,
            'role': self.role,
            'text': self.text,
            'idempotency_key': self.idempotency_key,
            'variant_id': self.variant_id,
            'source_created_at': self.source_created_at,
        }

    def digest(self) -> str:
        self.validated()
        values = (
            self.version,
            self.source,
            self.conversation_id,
            self.turn_id,
            self.event_type,
            self.role,
            self.text,
            self.idempotency_key,
            self.variant_id,
            self.source_created_at,
        )
        digest = hashlib.sha256()
        digest.update(DIGEST_DOMAIN)
        for value in values:
            digest.update(_digest_part(value))
        return digest.hexdigest()

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> 'CaptureEvent':
        expected = {
            'version', 'source', 'conversation_id', 'turn_id', 'event_type',
            'role', 'text', 'idempotency_key', 'variant_id', 'source_created_at',
        }
        if set(value) != expected:
            raise ValueError('Unexpected or missing capture event fields')
        return cls(**dict(value)).validated()


@dataclass(frozen=True)
class CaptureReceipt:
    seq: int
    event_id: str
    payload_digest: str
    received_at: str
    state: str = 'REMOTE_CAPTURED'

    def payload(self) -> dict[str, Any]:
        return {
            'seq': self.seq,
            'event_id': self.event_id,
            'payload_digest': self.payload_digest,
            'received_at': self.received_at,
            'state': self.state,
        }


class SQLiteRelay:
    """Reference append-only relay used for tests and local experiments.

    Production remote deployments use PostgreSQL through the SQL migration in
    ``sql/capture_fabric_postgres.sql``. Keeping this tiny SQLite implementation
    lets the protocol be tested without a network or cloud account.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(self.path))
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS capture_events (
                seq INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                idempotency_key TEXT NOT NULL UNIQUE,
                payload TEXT NOT NULL,
                payload_digest TEXT NOT NULL,
                received_at TEXT NOT NULL
            );
            CREATE TRIGGER IF NOT EXISTS capture_events_no_update
            BEFORE UPDATE ON capture_events
            BEGIN SELECT RAISE(ABORT, 'capture events are append-only'); END;
            CREATE TRIGGER IF NOT EXISTS capture_events_no_delete
            BEFORE DELETE ON capture_events
            BEGIN SELECT RAISE(ABORT, 'capture events are append-only'); END;
        ''')
        self.db.commit()

    def append(self, event: CaptureEvent) -> CaptureReceipt:
        event = event.validated()
        payload = canonical_json(event.payload())
        digest = event.digest()
        existing = self.db.execute(
            'SELECT * FROM capture_events WHERE idempotency_key=?',
            (event.idempotency_key,),
        ).fetchone()
        if existing is not None:
            if existing['payload'] != payload or existing['payload_digest'] != digest:
                raise ValueError('Conflicting retry for idempotency_key')
            return CaptureReceipt(existing['seq'], existing['event_id'],
                                  existing['payload_digest'], existing['received_at'])

        received_at = _now()
        event_id = str(uuid.uuid4())
        with self.db:
            cur = self.db.execute(
                'INSERT INTO capture_events '
                '(event_id,idempotency_key,payload,payload_digest,received_at) '
                'VALUES (?,?,?,?,?)',
                (event_id, event.idempotency_key, payload, digest, received_at),
            )
            seq = int(cur.lastrowid)
        row = self.db.execute('SELECT * FROM capture_events WHERE seq=?', (seq,)).fetchone()
        if row is None or row['payload'] != payload or row['payload_digest'] != digest:
            raise IOError('Relay readback verification failed')
        return CaptureReceipt(seq, event_id, digest, received_at)

    def after(self, seq: int, limit: int = 100) -> list[tuple[CaptureReceipt, CaptureEvent]]:
        if type(seq) is not int or seq < 0:
            raise ValueError('seq must be a nonnegative integer')
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError('limit must be from 1 to 1000')
        rows = self.db.execute(
            'SELECT * FROM capture_events WHERE seq>? ORDER BY seq LIMIT ?',
            (seq, limit),
        ).fetchall()
        result = []
        for row in rows:
            payload = json.loads(row['payload'])
            event = CaptureEvent.from_mapping(payload)
            if event.digest() != row['payload_digest']:
                raise IOError('Relay payload digest mismatch')
            result.append((
                CaptureReceipt(row['seq'], row['event_id'], row['payload_digest'], row['received_at']),
                event,
            ))
        return result

    def close(self) -> None:
        self.db.close()


class CaptureGateway:
    """Small authority boundary exposed by an MCP tool or HTTP endpoint."""

    def __init__(self, append_event: Callable[[CaptureEvent], CaptureReceipt]):
        self._append_event = append_event

    def append_event(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        event = CaptureEvent.from_mapping(payload)
        receipt = self._append_event(event)
        return receipt.payload()


class ProviderWebhookIngress:
    """Adapter contract for future provider-native signed webhooks.

    HumanOS does *not* assume that ChatGPT, Claude, Gemini, or another provider
    currently emits the required conversation webhook. A provider adapter is
    enabled only when a real verifier and mapper for that provider exist.
    """

    def __init__(self,
                 gateway: CaptureGateway,
                 verify_request: Callable[[Mapping[str, str], bytes], bool],
                 map_request: Callable[[bytes], Mapping[str, Any]]):
        self.gateway = gateway
        self.verify_request = verify_request
        self.map_request = map_request

    def receive(self, headers: Mapping[str, str], body: bytes) -> dict[str, Any]:
        if not isinstance(body, (bytes, bytearray)) or not body:
            raise ValueError('Webhook body must be nonempty bytes')
        if not self.verify_request(headers, bytes(body)):
            raise PermissionError('Provider webhook signature verification failed')
        payload = self.map_request(bytes(body))
        return self.gateway.append_event(payload)


def hmac_webhook_verifier(secret: bytes,
                          header_name: str = 'x-humanos-signature') -> Callable[[Mapping[str, str], bytes], bool]:
    """Deterministic verifier for tests or owner-controlled webhook sources.

    Real provider-native adapters should implement the provider's documented
    signing algorithm instead of reusing this helper by assumption.
    """
    if not isinstance(secret, bytes) or len(secret) < 32:
        raise ValueError('Webhook secret must contain at least 32 bytes')
    wanted = header_name.lower()

    def verify(headers: Mapping[str, str], body: bytes) -> bool:
        lowered = {str(k).lower(): str(v) for k, v in headers.items()}
        supplied = lowered.get(wanted, '')
        expected = hmac.new(secret, body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(supplied, expected)

    return verify
