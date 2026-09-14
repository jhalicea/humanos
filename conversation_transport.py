#!/usr/bin/env python3
"""Durable local transport for Universal Conversation Capture.

The transport is intentionally split from the Life Notebook writer. A browser or
other host can fsync an exact message into the local capture spool immediately,
even while another HumanOS process owns the Notebook writer lock. When the
Notebook is available, the ingestor moves the already-preserved event into the
canonical Life Notebook through UniversalConversationCapture.

The spool lives beside, not inside, ``vault/runtime`` so creating it first can
never make a fresh Notebook vault look like a damaged pre-existing protected
runtime. No language model is called anywhere in this module.
"""

import argparse
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import socket
import sqlite3
import stat
from datetime import datetime, timezone

from conversation_capture import UniversalConversationCapture
from notebook import Notebook


FORMAT_VERSION = 1
MAX_FRAME = 2 * 1024 * 1024
ROLES = {'human': 'HUMAN', 'assistant': 'ASSISTANT'}


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def _required(name, value, maximum):
    if not isinstance(value, str) or not value or len(value.encode('utf-8')) > maximum:
        raise ValueError(name + ' must be nonempty bounded text')
    return value


def _private_dir(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == 'posix':
        os.chmod(path, 0o700)
        info = path.lstat()
        if path.is_symlink() or stat.S_IMODE(info.st_mode) != 0o700:
            raise PermissionError('Capture directory must be owner-only')
    return path


def _load_or_create_secret(path):
    path = Path(path)
    if path.exists():
        data = path.read_bytes()
    else:
        data = secrets.token_bytes(32)
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                     getattr(os, 'O_NOFOLLOW', 0), 0o600)
        try:
            os.write(fd, data)
            os.fsync(fd)
        finally:
            os.close(fd)
    if len(data) != 32:
        raise PermissionError('Invalid capture transport secret')
    if os.name == 'posix' and stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise PermissionError('Capture transport secret permissions are unsafe')
    return data


class CaptureSpool:
    """A tiny durable inbox that never depends on the Notebook writer lock."""

    def __init__(self, vault):
        self.vault = Path(vault).resolve()
        self.root = _private_dir(self.vault / 'capture-transport')
        self.secret_path = self.root / 'capture.key'
        self.secret = _load_or_create_secret(self.secret_path)
        self.db_path = self.root / 'capture.sqlite3'
        self.db = sqlite3.connect(str(self.db_path), timeout=5)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
          PRAGMA journal_mode=WAL;
          PRAGMA synchronous=FULL;
          PRAGMA foreign_keys=ON;
          PRAGMA busy_timeout=5000;
          CREATE TABLE IF NOT EXISTS events(
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL UNIQUE,
            source TEXT NOT NULL,
            conversation_key TEXT NOT NULL,
            turn_key TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('HUMAN','ASSISTANT')),
            text TEXT NOT NULL,
            text_proof TEXT NOT NULL,
            created TEXT NOT NULL,
            UNIQUE(source,conversation_key,turn_key,role));
          CREATE TABLE IF NOT EXISTS receipts(
            event_id TEXT PRIMARY KEY REFERENCES events(event_id),
            tx TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            ingested TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS bindings(
            source TEXT NOT NULL,
            conversation_key TEXT NOT NULL,
            hcid TEXT NOT NULL,
            page TEXT NOT NULL,
            owner TEXT NOT NULL,
            created TEXT NOT NULL,
            PRIMARY KEY(source,conversation_key));
          CREATE TRIGGER IF NOT EXISTS capture_events_no_update
            BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'append-only capture event'); END;
          CREATE TRIGGER IF NOT EXISTS capture_events_no_delete
            BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'append-only capture event'); END;
          CREATE TRIGGER IF NOT EXISTS capture_receipts_no_update
            BEFORE UPDATE ON receipts BEGIN SELECT RAISE(ABORT,'append-only capture receipt'); END;
          CREATE TRIGGER IF NOT EXISTS capture_receipts_no_delete
            BEFORE DELETE ON receipts BEGIN SELECT RAISE(ABORT,'append-only capture receipt'); END;
          CREATE TRIGGER IF NOT EXISTS capture_bindings_no_update
            BEFORE UPDATE ON bindings BEGIN SELECT RAISE(ABORT,'immutable capture binding'); END;
          CREATE TRIGGER IF NOT EXISTS capture_bindings_no_delete
            BEFORE DELETE ON bindings BEGIN SELECT RAISE(ABORT,'immutable capture binding'); END;
        ''')

    def close(self):
        self.db.close()

    def _proof(self, domain, value):
        raw = domain.encode('utf-8') + b'\x00' + value.encode('utf-8')
        return 'hmac-sha256:' + hmac.new(self.secret, raw, hashlib.sha256).hexdigest()

    def _key(self, domain, source, value):
        return self._proof(domain, source + '\x00' + value)

    def append(self, source, conversation_id, turn_id, role, text):
        source = _required('source', source, 64)
        conversation_id = _required('conversation_id', conversation_id, 2048)
        turn_id = _required('turn_id', turn_id, 2048)
        if role not in ROLES:
            raise ValueError('role must be human or assistant')
        if not isinstance(text, str):
            raise ValueError('text must be a string')
        stored_role = ROLES[role]
        conversation_key = self._key('conversation', source, conversation_id)
        turn_key = self._key('turn', source, turn_id)
        identity = source + '\x00' + conversation_key + '\x00' + turn_key + '\x00' + stored_role
        event_id = self._proof('event', identity)
        text_proof = self._proof('text', text)
        prior = self.db.execute('SELECT * FROM events WHERE event_id=?', (event_id,)).fetchone()
        if prior:
            if (prior['source'] != source or prior['conversation_key'] != conversation_key or
                    prior['turn_key'] != turn_key or prior['role'] != stored_role or
                    prior['text'] != text or prior['text_proof'] != text_proof):
                raise ValueError('Capture retry differs from preserved local evidence')
            return dict(prior)
        with self.db:
            self.db.execute('''INSERT INTO events(event_id,source,conversation_key,turn_key,role,text,text_proof,created)
                               VALUES(?,?,?,?,?,?,?,?)''',
                            (event_id, source, conversation_key, turn_key, stored_role,
                             text, text_proof, now()))
        row = self.db.execute('SELECT * FROM events WHERE event_id=?', (event_id,)).fetchone()
        if not row or row['text'] != text or row['text_proof'] != self._proof('text', row['text']):
            raise RuntimeError('Local capture spool readback verification failed')
        if self.db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('Local capture spool database integrity failure')
        return dict(row)

    def pending(self, limit=200):
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 10000:
            raise ValueError('Invalid capture pending limit')
        return [dict(row) for row in self.db.execute('''
            SELECT e.* FROM events e LEFT JOIN receipts r USING(event_id)
             WHERE r.event_id IS NULL ORDER BY e.seq LIMIT ?''', (limit,))]

    def receipt(self, event_id):
        row = self.db.execute('SELECT * FROM receipts WHERE event_id=?', (event_id,)).fetchone()
        return dict(row) if row else None

    def add_receipt(self, event_id, tx, ordinal):
        prior = self.receipt(event_id)
        if prior:
            if prior['tx'] != tx or prior['ordinal'] != ordinal:
                raise RuntimeError('Capture ingest receipt conflicts with preserved evidence')
            return prior
        with self.db:
            self.db.execute('INSERT INTO receipts VALUES(?,?,?,?)',
                            (event_id, tx, int(ordinal), now()))
        result = self.receipt(event_id)
        if not result:
            raise RuntimeError('Capture ingest receipt readback failed')
        return result

    def binding(self, source, conversation_key):
        row = self.db.execute('SELECT * FROM bindings WHERE source=? AND conversation_key=?',
                              (source, conversation_key)).fetchone()
        return dict(row) if row else None

    def ensure_binding(self, source, conversation_key, record):
        prior = self.binding(source, conversation_key)
        if prior:
            if prior['hcid'] != record['hcid'] or prior['page'] != record['page'] or prior['owner'] != record['owner']:
                raise RuntimeError('Capture conversation binding conflicts with preserved state')
            return prior
        with self.db:
            self.db.execute('INSERT INTO bindings VALUES(?,?,?,?,?,?)',
                            (source, conversation_key, record['hcid'], record['page'],
                             record['owner'], now()))
        return self.binding(source, conversation_key)

    def human_for(self, event):
        row = self.db.execute('''SELECT * FROM events
            WHERE source=? AND conversation_key=? AND turn_key=? AND role='HUMAN' ''',
            (event['source'], event['conversation_key'], event['turn_key'])).fetchone()
        return dict(row) if row else None


class CaptureIngestor:
    """Move already-fsynced spool events into the canonical Life Notebook."""

    def __init__(self, book, spool, owner='Jon'):
        self.book, self.spool, self.owner = book, spool, owner

    def ingest_pending(self, limit=200):
        ingested = []
        for event in self.spool.pending(limit):
            capture = UniversalConversationCapture(self.book, event['source'])
            binding = self.spool.binding(event['source'], event['conversation_key'])
            if event['role'] == 'HUMAN':
                if binding is None:
                    binding = self.book.bind(self.owner, event['text'])
                    binding = self.spool.ensure_binding(event['source'], event['conversation_key'], binding)
                tx = capture.begin_turn(binding['hcid'], event['conversation_key'],
                                        event['turn_key'], event['text'])
                self.spool.add_receipt(event['event_id'], tx, 0)
                ingested.append(event['event_id'])
                continue

            human = self.spool.human_for(event)
            if human is None:
                continue
            human_receipt = self.spool.receipt(human['event_id'])
            if human_receipt is None:
                continue
            capture.finish_turn(human_receipt['tx'], event['text'])
            self.spool.add_receipt(event['event_id'], human_receipt['tx'], 1)
            ingested.append(event['event_id'])
        return ingested


def try_ingest(vault, spool, owner='Jon'):
    """Try canonical ingestion; return False when another Notebook writer owns it."""
    try:
        book = Notebook(vault)
    except RuntimeError as error:
        if 'already has a Notebook writer' in str(error):
            return False
        raise
    try:
        book.recover()
        CaptureIngestor(book, spool, owner).ingest_pending()
        return True
    finally:
        book.close()


def _recv_line(connection):
    stream = connection.makefile('rb')
    raw = stream.readline(MAX_FRAME + 1)
    if not raw or len(raw) > MAX_FRAME or not raw.endswith(b'\n'):
        raise ValueError('Invalid capture frame')
    return json.loads(raw.decode('utf-8'))


def _send_line(connection, value):
    raw = (canonical(value) + '\n').encode('utf-8')
    if len(raw) > MAX_FRAME:
        raise ValueError('Capture response too large')
    connection.sendall(raw)


class CaptureDaemon:
    """Owner-only Unix-socket service used by browser/native host adapters."""

    def __init__(self, vault, socket_path, owner='Jon'):
        self.vault = Path(vault).resolve()
        self.spool = CaptureSpool(self.vault)
        self.socket_path = Path(socket_path).resolve()
        self.owner = owner

    def _authenticate(self, message):
        if not isinstance(message, dict) or set(message) != {'request', 'mac'}:
            raise ValueError('Malformed capture request')
        request = message['request']
        if not isinstance(request, dict) or set(request) != {
                'version', 'source', 'conversation_id', 'turn_id', 'role', 'text'}:
            raise ValueError('Malformed capture payload')
        if request['version'] != FORMAT_VERSION:
            raise ValueError('Unsupported capture transport version')
        expected = hmac.new(self.spool.secret, canonical(request).encode('utf-8'),
                            hashlib.sha256).hexdigest()
        if not isinstance(message['mac'], str) or not hmac.compare_digest(expected, message['mac']):
            raise PermissionError('Unauthenticated capture request')
        return request

    def handle(self, message):
        request = self._authenticate(message)
        event = self.spool.append(request['source'], request['conversation_id'],
                                  request['turn_id'], request['role'], request['text'])
        canonical_now = try_ingest(self.vault, self.spool, self.owner)
        receipt = self.spool.receipt(event['event_id'])
        return {'ok': True, 'event_id': event['event_id'], 'seq': event['seq'],
                'stored_local': True, 'notebook_ingested': receipt is not None,
                'notebook_available': canonical_now}

    def serve_forever(self):
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)
        if self.socket_path.exists() or self.socket_path.is_socket():
            if self.socket_path.is_symlink():
                raise PermissionError('Refusing symlink capture socket')
            self.socket_path.unlink()
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            server.bind(str(self.socket_path))
            os.chmod(self.socket_path, 0o600)
            server.listen(16)
            server.settimeout(2.0)
            try:
                while True:
                    try:
                        connection, _ = server.accept()
                    except socket.timeout:
                        try_ingest(self.vault, self.spool, self.owner)
                        continue
                    with connection:
                        try:
                            response = self.handle(_recv_line(connection))
                        except Exception as error:
                            response = {'ok': False, 'error': str(error)}
                        _send_line(connection, response)
            finally:
                try:
                    self.socket_path.unlink()
                except FileNotFoundError:
                    pass
                self.spool.close()


def capture_sender(socket_path, secret_path):
    secret = Path(secret_path).read_bytes()
    if len(secret) != 32:
        raise PermissionError('Invalid capture transport secret')

    def send(source, conversation_id, turn_id, role, text):
        request = {'version': FORMAT_VERSION, 'source': source,
                   'conversation_id': conversation_id, 'turn_id': turn_id,
                   'role': role, 'text': text}
        mac = hmac.new(secret, canonical(request).encode('utf-8'), hashlib.sha256).hexdigest()
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.connect(str(socket_path))
            _send_line(client, {'request': request, 'mac': mac})
            return _recv_line(client)
    return send


def main():
    parser = argparse.ArgumentParser(description='HumanOS local conversation capture transport')
    sub = parser.add_subparsers(dest='command', required=True)
    serve = sub.add_parser('serve')
    serve.add_argument('--vault', required=True)
    serve.add_argument('--socket', required=True)
    serve.add_argument('--owner', default='Jon')
    ingest = sub.add_parser('ingest')
    ingest.add_argument('--vault', required=True)
    ingest.add_argument('--owner', default='Jon')
    args = parser.parse_args()
    if args.command == 'serve':
        CaptureDaemon(args.vault, args.socket, args.owner).serve_forever()
    else:
        spool = CaptureSpool(args.vault)
        try:
            if not try_ingest(args.vault, spool, args.owner):
                raise SystemExit('Notebook writer is active; capture remains safely queued locally')
        finally:
            spool.close()


if __name__ == '__main__':
    main()
