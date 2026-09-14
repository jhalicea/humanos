#!/usr/bin/env python3
"""Encrypted PostgreSQL transport for HumanOS Capture Fabric.

The writer encrypts validated CaptureEvent objects before database insertion.
The reader requires the owner-controlled X25519 private key and decrypts only on
the local HumanOS side.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from capture_encryption import (
    ciphertext_digest,
    decrypt_event,
    encrypt_event,
    validate_envelope,
)
from capture_fabric import CaptureEvent, CaptureReceipt


@dataclass(frozen=True)
class EncryptedCaptureReceipt:
    seq: int
    event_id: str
    payload_digest: str
    received_at: str
    state: str = 'REMOTE_CAPTURED_ENCRYPTED'

    def as_capture_receipt(self) -> CaptureReceipt:
        return CaptureReceipt(
            self.seq,
            self.event_id,
            self.payload_digest,
            self.received_at,
            self.state,
        )


class _PostgresBase:
    def __init__(self, dsn: str):
        if not isinstance(dsn, str) or not dsn:
            raise ValueError('Postgres DSN is required')
        try:
            import psycopg
        except ImportError as error:
            raise RuntimeError('Install requirements-capture.txt to use encrypted capture') from error
        self._psycopg = psycopg
        self.dsn = dsn


class EncryptedPostgresCaptureWriter(_PostgresBase):
    """Write-only adapter. Requires public recipient key, never private key."""

    def __init__(self, dsn: str, recipient_public_key: bytes, relay_token_secret: bytes):
        super().__init__(dsn)
        self.recipient_public_key = recipient_public_key
        self.relay_token_secret = relay_token_secret

    def append(self, event: CaptureEvent) -> EncryptedCaptureReceipt:
        event = event.validated()
        envelope = encrypt_event(event, self.recipient_public_key, self.relay_token_secret)
        payload = json.dumps(envelope, ensure_ascii=False, separators=(',', ':'))
        with self._psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT seq,event_id,ciphertext_digest,received_at,state '
                    'FROM humanos_append_capture_envelope(%s::jsonb)',
                    (payload,),
                )
                row = cur.fetchone()
        if row is None:
            raise RuntimeError('Encrypted Postgres capture append returned no receipt')
        seq, event_id, digest, received_at, state = row
        if state != 'REMOTE_CAPTURED_ENCRYPTED':
            raise RuntimeError('Unexpected encrypted Postgres capture state')
        return EncryptedCaptureReceipt(
            int(seq), str(event_id), str(digest), received_at.isoformat(), str(state)
        )


class EncryptedPostgresCaptureReader(_PostgresBase):
    """Read/decrypt adapter intended only for owner-controlled local HumanOS."""

    def __init__(self, dsn: str, recipient_private_key: bytes):
        super().__init__(dsn)
        self.recipient_private_key = recipient_private_key

    def after(self, seq: int, limit: int = 100) -> list[tuple[CaptureReceipt, CaptureEvent]]:
        if type(seq) is not int or seq < 0:
            raise ValueError('seq must be a nonnegative integer')
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError('limit must be from 1 to 1000')
        with self._psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT seq,event_id,envelope,ciphertext_digest,received_at '
                    'FROM humanos_capture_envelopes_after(%s,%s)',
                    (seq, limit),
                )
                rows = cur.fetchall()
        result: list[tuple[CaptureReceipt, CaptureEvent]] = []
        for db_seq, event_id, envelope, digest, received_at in rows:
            envelope = validate_envelope(envelope)
            local_ciphertext_digest = ciphertext_digest(envelope)
            if local_ciphertext_digest != str(digest):
                raise IOError('Encrypted relay ciphertext digest mismatch')
            event = decrypt_event(envelope, self.recipient_private_key)
            result.append((
                CaptureReceipt(
                    int(db_seq), str(event_id), str(digest),
                    received_at.isoformat(), 'REMOTE_CAPTURED_ENCRYPTED'
                ),
                event,
            ))
        return result
