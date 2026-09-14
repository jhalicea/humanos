#!/usr/bin/env python3
"""Verified HumanOS Capture Fabric importer.

Remote PostgreSQL is a durable relay, not the canonical notebook. This importer
first stages verified remote events into a local fsynced inbox, then translates
them into Universal Conversation Capture transactions. Staging and Notebook
import are separate so an out-of-order assistant event or a temporary Notebook
problem cannot cause the remote cursor to lose evidence.

No language model is called.
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
from conversation_capture import UniversalConversationCapture


STAGED = 'STAGED'
IMPORTED = 'IMPORTED'
ERROR = 'ERROR'


class _UnresolvedDependency(Exception):
    pass


def _private_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == 'posix':
        os.chmod(path, 0o700)
        info = path.lstat()
        if path.is_symlink() or stat.S_IMODE(info.st_mode) != 0o700:
            raise PermissionError('Capture importer state must be owner-only')
    return path


def _opaque(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


class CaptureImporter:
    """Stage remote events durably, then import them into the Life Notebook."""

    def __init__(self, book, state_dir, owner='Jon'):
        self.book = book
        self.owner = owner
        self.state_dir = _private_dir(Path(state_dir))
        self.db = sqlite3.connect(str(self.state_dir / 'capture-import.sqlite3'))
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS meta(
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS inbox(
                remote_seq INTEGER PRIMARY KEY,
                event_id TEXT NOT NULL UNIQUE,
                payload TEXT NOT NULL,
                payload_digest TEXT NOT NULL,
                status TEXT NOT NULL CHECK(status IN ('STAGED','IMPORTED','ERROR')),
                imported_tx TEXT,
                error TEXT
            );
            CREATE TABLE IF NOT EXISTS conversations(
                source TEXT NOT NULL,
                conversation_key TEXT NOT NULL,
                hcid TEXT NOT NULL,
                PRIMARY KEY(source, conversation_key)
            );
            CREATE TABLE IF NOT EXISTS turns(
                source TEXT NOT NULL,
                conversation_key TEXT NOT NULL,
                turn_key TEXT NOT NULL,
                variant_key TEXT NOT NULL,
                tx TEXT NOT NULL,
                hcid TEXT NOT NULL,
                PRIMARY KEY(source, conversation_key, turn_key, variant_key)
            );
        ''')
        self.db.commit()
        if self._meta('staged_remote_seq') is None:
            with self.db:
                self.db.execute(
                    'INSERT INTO meta(key,value) VALUES(?,?)',
                    ('staged_remote_seq', '0'),
                )

    def _meta(self, key):
        row = self.db.execute('SELECT value FROM meta WHERE key=?', (key,)).fetchone()
        return row['value'] if row else None

    @property
    def staged_remote_seq(self) -> int:
        value = int(self._meta('staged_remote_seq') or '0')
        if value < 0:
            raise RuntimeError('Invalid capture importer cursor')
        return value

    def stage(self, reader: Callable[[int, int], list[tuple[CaptureReceipt, CaptureEvent]]],
              limit=100) -> int:
        """Copy verified remote events into the local recovery inbox.

        ``reader`` has the same shape as ``SQLiteRelay.after`` and the production
        PostgreSQL adapter. The remote cursor advances only after the exact event
        and receipt are committed to this local inbox.
        """
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise ValueError('limit must be from 1 to 1000')
        cursor = self.staged_remote_seq
        rows = reader(cursor, limit)
        previous = cursor
        staged = 0
        for receipt, event in rows:
            if not isinstance(receipt, CaptureReceipt) or not isinstance(event, CaptureEvent):
                raise TypeError('reader must return CaptureReceipt/CaptureEvent pairs')
            event.validated()
            if receipt.seq <= previous:
                raise RuntimeError('Remote capture sequence is not strictly increasing')
            if receipt.payload_digest != event.digest():
                raise RuntimeError('Remote capture digest mismatch')
            payload = canonical_json(event.payload())
            existing = self.db.execute(
                'SELECT * FROM inbox WHERE remote_seq=? OR event_id=?',
                (receipt.seq, receipt.event_id),
            ).fetchone()
            if existing:
                if (existing['remote_seq'] != receipt.seq or existing['event_id'] != receipt.event_id
                        or existing['payload'] != payload
                        or existing['payload_digest'] != receipt.payload_digest):
                    raise RuntimeError('Remote capture identity conflicts with staged evidence')
            else:
                with self.db:
                    self.db.execute(
                        'INSERT INTO inbox(remote_seq,event_id,payload,payload_digest,status) '
                        'VALUES(?,?,?,?,?)',
                        (receipt.seq, receipt.event_id, payload, receipt.payload_digest, STAGED),
                    )
                staged += 1
            with self.db:
                self.db.execute(
                    'UPDATE meta SET value=? WHERE key=?',
                    (str(receipt.seq), 'staged_remote_seq'),
                )
            previous = receipt.seq
        return staged

    def _conversation(self, event: CaptureEvent, create=False):
        conversation_key = _opaque(event.conversation_id)
        row = self.db.execute(
            'SELECT hcid FROM conversations WHERE source=? AND conversation_key=?',
            (event.source, conversation_key),
        ).fetchone()
        if row:
            return conversation_key, row['hcid']
        if not create:
            raise _UnresolvedDependency('conversation has no imported human event yet')
        binding = self.book.bind(self.owner, event.text)
        with self.db:
            self.db.execute(
                'INSERT INTO conversations(source,conversation_key,hcid) VALUES(?,?,?)',
                (event.source, conversation_key, binding['hcid']),
            )
        return conversation_key, binding['hcid']

    def _turn_keys(self, event: CaptureEvent):
        return _opaque(event.turn_id), _opaque(event.variant_id)

    def _capture_ids(self, event: CaptureEvent):
        # Provider IDs stay in the private relay/inbox. The Notebook receives
        # deterministic opaque identities no longer than its capture API bounds.
        conversation_id = 'remote-' + _opaque(event.conversation_id)
        turn_material = event.turn_id + '\x00' + event.variant_id
        turn_id = 'remote-' + _opaque(turn_material)
        return conversation_id, turn_id

    def _remember_turn(self, event, conversation_key, hcid, tx):
        turn_key, variant_key = self._turn_keys(event)
        existing = self.db.execute(
            'SELECT tx,hcid FROM turns WHERE source=? AND conversation_key=? '
            'AND turn_key=? AND variant_key=?',
            (event.source, conversation_key, turn_key, variant_key),
        ).fetchone()
        if existing:
            if existing['tx'] != tx or existing['hcid'] != hcid:
                raise RuntimeError('Local capture turn mapping conflict')
            return
        with self.db:
            self.db.execute(
                'INSERT INTO turns(source,conversation_key,turn_key,variant_key,tx,hcid) '
                'VALUES(?,?,?,?,?,?)',
                (event.source, conversation_key, turn_key, variant_key, tx, hcid),
            )

    def _mapped_turn(self, event, variant_id=None):
        conversation_key = _opaque(event.conversation_id)
        turn_key = _opaque(event.turn_id)
        variant_key = _opaque(event.variant_id if variant_id is None else variant_id)
        return self.db.execute(
            'SELECT tx,hcid FROM turns WHERE source=? AND conversation_key=? '
            'AND turn_key=? AND variant_key=?',
            (event.source, conversation_key, turn_key, variant_key),
        ).fetchone()

    def _human_text(self, tx):
        row = self.book.db.execute(
            "SELECT text FROM transcript WHERE tx=? AND ordinal=0 AND role='HUMAN'",
            (tx,),
        ).fetchone()
        if not row:
            raise _UnresolvedDependency('parent human evidence is not imported yet')
        return row['text']

    def _import_event(self, event: CaptureEvent) -> str:
        capture = UniversalConversationCapture(self.book, event.source)
        local_conversation_id, local_turn_id = self._capture_ids(event)

        if event.role == 'human':
            conversation_key, hcid = self._conversation(event, create=True)
            tx = capture.begin_turn(hcid, local_conversation_id, local_turn_id, event.text)
            self._remember_turn(event, conversation_key, hcid, tx)
            return tx

        # Assistant event: normally its matching human event already created the
        # transaction. If this is a regeneration with no repeated human event,
        # branch from the preserved primary human evidence instead of inventing it.
        conversation_key, hcid = self._conversation(event, create=False)
        mapped = self._mapped_turn(event)
        if mapped:
            tx = mapped['tx']
            capture.finish_turn(tx, event.text)
            return tx

        primary = self._mapped_turn(event, variant_id='primary')
        if not primary:
            raise _UnresolvedDependency('assistant event is waiting for human evidence')
        human_text = self._human_text(primary['tx'])
        tx = capture.begin_turn(hcid, local_conversation_id, local_turn_id, human_text)
        self._remember_turn(event, conversation_key, hcid, tx)
        capture.finish_turn(tx, event.text)
        return tx

    def drain(self, max_passes=4) -> dict:
        """Import staged events, tolerating temporary out-of-order dependencies."""
        if type(max_passes) is not int or not 1 <= max_passes <= 20:
            raise ValueError('max_passes must be from 1 to 20')
        imported = 0
        for _ in range(max_passes):
            progress = False
            rows = self.db.execute(
                "SELECT * FROM inbox WHERE status='STAGED' ORDER BY remote_seq"
            ).fetchall()
            if not rows:
                break
            for row in rows:
                event = CaptureEvent.from_mapping(json.loads(row['payload']))
                if event.digest() != row['payload_digest']:
                    raise RuntimeError('Staged capture payload digest mismatch')
                try:
                    tx = self._import_event(event)
                except _UnresolvedDependency:
                    continue
                except Exception as error:
                    with self.db:
                        self.db.execute(
                            "UPDATE inbox SET status='ERROR', error=? WHERE remote_seq=?",
                            (str(error), row['remote_seq']),
                        )
                    raise
                with self.db:
                    self.db.execute(
                        "UPDATE inbox SET status='IMPORTED', imported_tx=?, error=NULL "
                        'WHERE remote_seq=?',
                        (tx, row['remote_seq']),
                    )
                imported += 1
                progress = True
            if not progress:
                break
        self.book.verify()
        return {
            'imported': imported,
            'pending': self.db.execute(
                "SELECT COUNT(*) FROM inbox WHERE status='STAGED'"
            ).fetchone()[0],
            'errors': self.db.execute(
                "SELECT COUNT(*) FROM inbox WHERE status='ERROR'"
            ).fetchone()[0],
            'staged_remote_seq': self.staged_remote_seq,
            'acknowledged_seq': self.acknowledged_seq(),
        }

    def acknowledged_seq(self) -> int:
        """Highest contiguous remote sequence imported into the Life Notebook."""
        rows = self.db.execute(
            'SELECT remote_seq,status FROM inbox ORDER BY remote_seq'
        ).fetchall()
        acknowledged = 0
        for row in rows:
            if row['remote_seq'] != acknowledged + 1 or row['status'] != IMPORTED:
                break
            acknowledged = row['remote_seq']
        return acknowledged

    def status(self) -> dict:
        return {
            'staged_remote_seq': self.staged_remote_seq,
            'acknowledged_seq': self.acknowledged_seq(),
            'staged': self.db.execute(
                "SELECT COUNT(*) FROM inbox WHERE status='STAGED'"
            ).fetchone()[0],
            'imported': self.db.execute(
                "SELECT COUNT(*) FROM inbox WHERE status='IMPORTED'"
            ).fetchone()[0],
            'errors': self.db.execute(
                "SELECT COUNT(*) FROM inbox WHERE status='ERROR'"
            ).fetchone()[0],
        }

    def close(self):
        self.db.close()
