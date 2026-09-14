#!/usr/bin/env python3
"""Verified remote-to-local synchronization for HumanOS Capture Fabric.

The remote PostgreSQL relay is a mailbox, not the canonical memory store.  This
module pulls immutable events into a private local mirror first, verifies and
fsyncs them, then converts them into the existing local CaptureSpool.  The Life
Notebook remains the final owner-controlled source of truth.

The local mirror deliberately preserves *all* supported event types.  Alternate
assistant generations are reconstructed as immutable local branches by copying
the original human prompt into a variant turn before the alternate assistant
message is spooled.  Nothing mutates a prior transcript row.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
from typing import Callable

from capture_fabric import CaptureEvent, CaptureReceipt, canonical_json
from conversation_transport import CaptureSpool, try_ingest


class RemoteSyncError(RuntimeError):
    pass


def _private_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == 'posix':
        os.chmod(path, 0o700)
        info = path.lstat()
        if path.is_symlink() or stat.S_IMODE(info.st_mode) != 0o700:
            raise PermissionError('Remote capture mirror directory must be owner-only')
    return path


class RemoteCaptureMirror:
    """Append-only local replica of remote Capture Fabric events."""

    def __init__(self, vault: str | Path):
        self.vault = Path(vault).resolve()
        self.root = _private_dir(self.vault / 'capture-remote-sync')
        self.path = self.root / 'remote-events.sqlite3'
        self.db = sqlite3.connect(str(self.path), timeout=5)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
            PRAGMA journal_mode=WAL;
            PRAGMA synchronous=FULL;
            PRAGMA busy_timeout=5000;
            CREATE TABLE IF NOT EXISTS remote_events(
                remote_seq INTEGER PRIMARY KEY,
                event_id TEXT NOT NULL UNIQUE,
                payload TEXT NOT NULL,
                local_digest TEXT NOT NULL,
                remote_digest TEXT NOT NULL,
                received_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS spool_receipts(
                remote_seq INTEGER PRIMARY KEY REFERENCES remote_events(remote_seq),
                local_event_ids TEXT NOT NULL,
                spooled_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TRIGGER IF NOT EXISTS remote_events_no_update
              BEFORE UPDATE ON remote_events
              BEGIN SELECT RAISE(ABORT,'remote capture events are append-only'); END;
            CREATE TRIGGER IF NOT EXISTS remote_events_no_delete
              BEFORE DELETE ON remote_events
              BEGIN SELECT RAISE(ABORT,'remote capture events are append-only'); END;
            CREATE TRIGGER IF NOT EXISTS remote_receipts_no_update
              BEFORE UPDATE ON spool_receipts
              BEGIN SELECT RAISE(ABORT,'remote capture receipts are append-only'); END;
            CREATE TRIGGER IF NOT EXISTS remote_receipts_no_delete
              BEFORE DELETE ON spool_receipts
              BEGIN SELECT RAISE(ABORT,'remote capture receipts are append-only'); END;
        ''')
        self.db.commit()

    def close(self) -> None:
        self.db.close()

    def last_remote_seq(self) -> int:
        row = self.db.execute('SELECT COALESCE(MAX(remote_seq),0) FROM remote_events').fetchone()
        return int(row[0])

    def pull(self,
             reader: Callable[[int, int], list[tuple[CaptureReceipt, CaptureEvent]]],
             limit: int = 200) -> list[int]:
        """Fetch one contiguous remote page and commit it atomically locally."""
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError('limit must be from 1 to 1000')
        after = self.last_remote_seq()
        rows = reader(after, limit)
        if not rows:
            return []

        expected = after + 1
        prepared = []
        for receipt, event in rows:
            if receipt.seq != expected:
                raise RemoteSyncError('Remote capture sequence gap or reordering detected')
            event = event.validated()
            payload = canonical_json(event.payload())
            local_digest = hashlib.sha256(payload.encode('utf-8')).hexdigest()
            if not isinstance(receipt.payload_digest, str) or len(receipt.payload_digest) != 64:
                raise RemoteSyncError('Remote capture receipt digest is malformed')
            prepared.append((receipt, payload, local_digest))
            expected += 1

        with self.db:
            for receipt, payload, local_digest in prepared:
                prior = self.db.execute(
                    'SELECT * FROM remote_events WHERE remote_seq=?', (receipt.seq,)
                ).fetchone()
                if prior is not None:
                    if (prior['event_id'] != receipt.event_id or prior['payload'] != payload or
                            prior['local_digest'] != local_digest or
                            prior['remote_digest'] != receipt.payload_digest):
                        raise RemoteSyncError('Remote retry conflicts with local mirror evidence')
                    continue
                self.db.execute('''
                    INSERT INTO remote_events
                    (remote_seq,event_id,payload,local_digest,remote_digest,received_at)
                    VALUES(?,?,?,?,?,?)''',
                    (receipt.seq, receipt.event_id, payload, local_digest,
                     receipt.payload_digest, receipt.received_at))

        # Read back every newly committed row before reporting success.
        for receipt, payload, local_digest in prepared:
            row = self.db.execute(
                'SELECT * FROM remote_events WHERE remote_seq=?', (receipt.seq,)
            ).fetchone()
            if row is None or row['payload'] != payload or row['local_digest'] != local_digest:
                raise RemoteSyncError('Remote capture local mirror readback failed')
        if self.db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RemoteSyncError('Remote capture mirror database integrity failure')
        return [receipt.seq for receipt, _, _ in prepared]

    def pending(self, limit: int = 200) -> list[tuple[int, CaptureEvent]]:
        rows = self.db.execute('''
            SELECT e.remote_seq,e.payload
              FROM remote_events e
              LEFT JOIN spool_receipts r USING(remote_seq)
             WHERE r.remote_seq IS NULL
             ORDER BY e.remote_seq LIMIT ?''', (limit,)).fetchall()
        return [(int(row['remote_seq']), CaptureEvent.from_mapping(json.loads(row['payload'])))
                for row in rows]

    def _human_for_turn(self, event: CaptureEvent) -> CaptureEvent | None:
        rows = self.db.execute(
            'SELECT payload FROM remote_events ORDER BY remote_seq'
        ).fetchall()
        candidate = None
        for row in rows:
            item = CaptureEvent.from_mapping(json.loads(row['payload']))
            if (item.source == event.source and
                    item.conversation_id == event.conversation_id and
                    item.turn_id == event.turn_id and
                    item.role == 'human'):
                candidate = item
        return candidate

    def _receipt(self, remote_seq: int) -> list[str] | None:
        row = self.db.execute(
            'SELECT local_event_ids FROM spool_receipts WHERE remote_seq=?', (remote_seq,)
        ).fetchone()
        return json.loads(row[0]) if row else None

    def _record_spooled(self, remote_seq: int, event_ids: list[str]) -> None:
        prior = self._receipt(remote_seq)
        if prior is not None:
            if prior != event_ids:
                raise RemoteSyncError('Remote spool receipt conflicts with preserved evidence')
            return
        with self.db:
            self.db.execute(
                'INSERT INTO spool_receipts(remote_seq,local_event_ids) VALUES(?,?)',
                (remote_seq, json.dumps(event_ids, ensure_ascii=False, separators=(',', ':'))))

    def spool_pending(self, spool: CaptureSpool, limit: int = 200) -> list[int]:
        """Convert mirrored remote events into the durable local capture spool."""
        completed = []
        for remote_seq, event in self.pending(limit):
            local_ids = []
            if event.event_type == 'human_message':
                local = spool.append(event.source, event.conversation_id,
                                     event.turn_id, 'human', event.text)
                local_ids.append(local['event_id'])
            elif event.event_type == 'assistant_message':
                local = spool.append(event.source, event.conversation_id,
                                     event.turn_id, 'assistant', event.text)
                local_ids.append(local['event_id'])
            elif event.event_type == 'human_edit':
                variant_turn = event.turn_id + ':edit:' + event.variant_id
                local = spool.append(event.source, event.conversation_id,
                                     variant_turn, 'human', event.text)
                local_ids.append(local['event_id'])
            elif event.event_type == 'assistant_regeneration':
                human = self._human_for_turn(event)
                if human is None:
                    # Keep the remote event pending until its branch context arrives.
                    continue
                variant_turn = event.turn_id + ':regen:' + event.variant_id
                h = spool.append(event.source, event.conversation_id,
                                 variant_turn, 'human', human.text)
                a = spool.append(event.source, event.conversation_id,
                                 variant_turn, 'assistant', event.text)
                local_ids.extend([h['event_id'], a['event_id']])
            else:
                raise RemoteSyncError('Unsupported mirrored capture event type')
            self._record_spooled(remote_seq, local_ids)
            completed.append(remote_seq)
        return completed


def sync_remote_once(vault: str | Path,
                     reader: Callable[[int, int], list[tuple[CaptureReceipt, CaptureEvent]]],
                     owner: str = 'Jon',
                     limit: int = 200) -> dict[str, object]:
    """Pull, mirror, spool, then opportunistically ingest into Life Notebook."""
    mirror = RemoteCaptureMirror(vault)
    spool = CaptureSpool(vault)
    try:
        pulled = mirror.pull(reader, limit)
        spooled = mirror.spool_pending(spool, limit)
        notebook_available = try_ingest(vault, spool, owner)
        return {
            'pulled_remote_seq': pulled,
            'spooled_remote_seq': spooled,
            'notebook_available': notebook_available,
            'pending_local_spool': len(spool.pending()),
        }
    finally:
        spool.close()
        mirror.close()
