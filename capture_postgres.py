#!/usr/bin/env python3
"""PostgreSQL adapter for the HumanOS Capture Fabric.

This module connects only to the two SECURITY DEFINER functions created by
``sql/capture_fabric_postgres.sql``. The recommended writer credential has
EXECUTE on ``humanos_append_capture_event`` and no table privileges. The local
HumanOS importer uses a separate reader credential with EXECUTE on
``humanos_capture_after``.
"""

from __future__ import annotations

import json
from typing import Any

from capture_fabric import CaptureEvent, CaptureReceipt


class PostgresCaptureRelay:
    def __init__(self, dsn: str):
        if not isinstance(dsn, str) or not dsn:
            raise ValueError('Postgres DSN is required')
        try:
            import psycopg
        except ImportError as error:
            raise RuntimeError('Install psycopg[binary] to use PostgreSQL capture') from error
        self._psycopg = psycopg
        self.dsn = dsn

    def append(self, event: CaptureEvent) -> CaptureReceipt:
        event = event.validated()
        payload = json.dumps(event.payload(), ensure_ascii=False, separators=(',', ':'))
        with self._psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT seq,event_id,payload_digest,received_at,state '
                            'FROM humanos_append_capture_event(%s::jsonb)', (payload,))
                row = cur.fetchone()
        if row is None:
            raise RuntimeError('Postgres capture append returned no receipt')
        seq, event_id, digest, received_at, state = row
        if state != 'REMOTE_CAPTURED':
            raise RuntimeError('Unexpected Postgres capture state')
        return CaptureReceipt(int(seq), str(event_id), str(digest),
                              received_at.isoformat(), str(state))

    def after(self, seq: int, limit: int = 100) -> list[tuple[CaptureReceipt, CaptureEvent]]:
        if type(seq) is not int or seq < 0:
            raise ValueError('seq must be a nonnegative integer')
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError('limit must be from 1 to 1000')
        with self._psycopg.connect(self.dsn) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT seq,event_id,payload,payload_digest,received_at '
                            'FROM humanos_capture_after(%s,%s)', (seq, limit))
                rows = cur.fetchall()
        result = []
        for db_seq, event_id, payload, digest, received_at in rows:
            event = CaptureEvent.from_mapping(payload)
            result.append((CaptureReceipt(int(db_seq), str(event_id), str(digest),
                                          received_at.isoformat()), event))
        return result
