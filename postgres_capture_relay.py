#!/usr/bin/env python3
"""PostgreSQL adapter for the HumanOS Capture Fabric.

The schema and authorization boundary live in ``sql/capture_fabric_postgres.sql``.
This adapter calls only the two RPC functions exposed by that schema. It does not
issue UPDATE or DELETE against capture evidence.

`psycopg` is an optional runtime dependency so the core/local test suite remains
lightweight. Production HumanOS installs it only when a PostgreSQL relay is used.
"""

from __future__ import annotations

import json
import os
from typing import Optional

from capture_fabric import CaptureEvent, CaptureReceipt, canonical_json


class PostgresCaptureRelay:
    def __init__(self, dsn: Optional[str] = None, connection=None):
        if connection is not None:
            self.db = connection
            self._owns_connection = False
            return
        dsn = dsn or os.environ.get('HUMANOS_CAPTURE_DATABASE_URL')
        if not dsn:
            raise ValueError('PostgreSQL relay DSN is required')
        try:
            import psycopg
        except ImportError as error:
            raise RuntimeError(
                'PostgreSQL capture relay requires the optional psycopg package'
            ) from error
        self.db = psycopg.connect(dsn)
        self._owns_connection = True

    def append(self, event: CaptureEvent) -> CaptureReceipt:
        event = event.validated()
        payload = canonical_json(event.payload())
        with self.db.cursor() as cur:
            cur.execute(
                'SELECT seq,event_id::text,payload_digest,received_at::text,state '
                'FROM humanos_append_capture_event(%s::jsonb)',
                (payload,),
            )
            row = cur.fetchone()
        self.db.commit()
        if row is None:
            raise IOError('PostgreSQL append returned no receipt')
        receipt = CaptureReceipt(
            seq=int(row[0]),
            event_id=str(row[1]),
            payload_digest=str(row[2]),
            received_at=str(row[3]),
            state=str(row[4]),
        )
        if receipt.state != 'REMOTE_CAPTURED' or receipt.payload_digest != event.digest():
            raise IOError('PostgreSQL receipt failed HumanOS protocol verification')
        return receipt

    def after(self, seq: int, limit: int = 100):
        if type(seq) is not int or seq < 0:
            raise ValueError('seq must be a nonnegative integer')
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError('limit must be from 1 to 1000')
        with self.db.cursor() as cur:
            cur.execute(
                'SELECT seq,event_id::text,payload,payload_digest,received_at::text '
                'FROM humanos_capture_after(%s,%s)',
                (seq, limit),
            )
            rows = cur.fetchall()
        result = []
        for row in rows:
            payload = row[2]
            if isinstance(payload, str):
                payload = json.loads(payload)
            event = CaptureEvent.from_mapping(payload)
            receipt = CaptureReceipt(
                seq=int(row[0]),
                event_id=str(row[1]),
                payload_digest=str(row[3]),
                received_at=str(row[4]),
            )
            if receipt.payload_digest != event.digest():
                raise IOError('PostgreSQL relay event digest mismatch')
            result.append((receipt, event))
        return result

    def close(self):
        if self._owns_connection:
            self.db.close()
