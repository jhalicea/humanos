"""HumanOS local Life Notebook adapter. SQLite evidence, replaceable projections.

Historical daily Markdown files are never imported, rebound or modified implicitly.
The process lock is held for the lifetime of a Notebook (single local writer).
"""
import fcntl
import hashlib
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from audit import AuditEvent, hash_event, verify_chain


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


class BindingConflict(RuntimeError):
    pass


class Notebook:
    def __init__(self, vault):
        self.root = Path(vault).resolve() / 'runtime'
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.lock = open(self.root / 'writer.lock', 'a')
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.lock.close()
            raise RuntimeError('HumanOS already has a Notebook writer; close it first.')
        self.db = sqlite3.connect(str(self.root / 'notebook.sqlite3'))
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
          PRAGMA journal_mode=WAL;
          PRAGMA synchronous=FULL;
          PRAGMA foreign_keys=ON;
          CREATE TABLE IF NOT EXISTS identities(
            hcid TEXT PRIMARY KEY, owner TEXT NOT NULL, page TEXT UNIQUE NOT NULL,
            binding TEXT NOT NULL, opening_hash TEXT NOT NULL, created TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS transactions(
            tx TEXT PRIMARY KEY, hcid TEXT NOT NULL REFERENCES identities(hcid),
            input TEXT NOT NULL, status TEXT NOT NULL, created TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS transcript(
            seq INTEGER PRIMARY KEY AUTOINCREMENT, tx TEXT NOT NULL REFERENCES transactions(tx),
            ordinal INTEGER NOT NULL, role TEXT NOT NULL, text TEXT NOT NULL,
            sha256 TEXT NOT NULL, created TEXT NOT NULL, UNIQUE(tx,ordinal));
          CREATE TABLE IF NOT EXISTS tasks(
            tx TEXT PRIMARY KEY REFERENCES transactions(tx), state TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS events(
            seq INTEGER PRIMARY KEY AUTOINCREMENT, tx TEXT, kind TEXT NOT NULL,
            payload TEXT NOT NULL, created TEXT NOT NULL,
            previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS recovery(
            id INTEGER PRIMARY KEY AUTOINCREMENT, tx TEXT, error TEXT NOT NULL,
            closed INTEGER NOT NULL DEFAULT 0, created TEXT NOT NULL);
          CREATE TRIGGER IF NOT EXISTS transcript_no_update BEFORE UPDATE ON transcript
            BEGIN SELECT RAISE(ABORT, 'append-only transcript'); END;
          CREATE TRIGGER IF NOT EXISTS transcript_no_delete BEFORE DELETE ON transcript
            BEGIN SELECT RAISE(ABORT, 'append-only transcript'); END;
          CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events
            BEGIN SELECT RAISE(ABORT, 'append-only events'); END;
          CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
            BEGIN SELECT RAISE(ABORT, 'append-only events'); END;
        ''')

    def close(self):
        self.db.close()
        self.lock.close()

    def event(self, tx, kind, payload):
        previous = self.db.execute('SELECT seq,event_hash FROM events ORDER BY seq DESC LIMIT 1').fetchone()
        seq, prev = (previous['seq'] + 1, previous['event_hash']) if previous else (1, 'GENESIS')
        stamp = now()
        body = {'payload': payload, 'created': stamp}
        with self.db:
            self.db.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?)',
                            (seq, tx, kind, encode(payload), stamp, prev,
                             hash_event(seq, kind, tx or '', body, prev)))

    def problem(self, tx, error, payload=None):
        # Independent fsynced fallback retains the exact input even if SQLite fails.
        record = {'tx': tx, 'error': str(error), 'payload': payload, 'created': now()}
        with open(self.root / 'recovery.jsonl', 'a', encoding='utf-8') as f:
            f.write(encode(record) + '\n')
            f.flush()
            os.fsync(f.fileno())
        with self.db:
            self.db.execute('INSERT INTO recovery(tx,error,created) VALUES(?,?,?)',
                            (tx, str(error), now()))
            self.db.execute("UPDATE transactions SET status='RECOVERY_REQUIRED' WHERE tx=?", (tx,))

    def bind(self, owner, opening, hcid=None, expected_page=None):
        if hcid:
            row = self.db.execute('SELECT * FROM identities WHERE hcid=?', (hcid,)).fetchone()
            if not row or row['owner'] != owner or row['binding'] != 'VERIFIED' or (
                    expected_page and row['page'] != expected_page):
                # Preserve existing pages and record a distinct protected identity.
                protected = self.bind(owner, opening)
                with self.db:
                    self.db.execute("UPDATE identities SET binding='RECONCILIATION_REQUIRED' WHERE hcid=?",
                                    (protected['hcid'],))
                self.event(None, 'BINDING_CONFLICT_DETECTED', {'requested': hcid, 'protected': protected})
                self.problem(None, 'Binding conflict; input retained for protected-page reconciliation',
                             {'role': 'HUMAN', 'text': opening, 'protected_page': protected['page'],
                              'requested_hcid': hcid})
                self.project()
                raise BindingConflict('Binding rejected; protected page ' + protected['page'] +
                                      ' requires explicit reconciliation. No transcript appended.')
            self.verify()
            return dict(row)
        token = uuid.uuid4().hex
        stamp = datetime.now().strftime('%Y%m%d')
        record = {'hcid': 'HCID-' + stamp + '-' + token, 'owner': owner,
                  'page': 'LN-' + stamp + '-' + token, 'binding': 'VERIFIED',
                  'opening_hash': digest(opening), 'created': now()}
        with self.db:
            self.db.execute('INSERT INTO identities VALUES(:hcid,:owner,:page,:binding,:opening_hash,:created)', record)
        self.event(None, 'IDENTITY_AND_BINDING_CREATED', dict(record, evidence='E1: HumanOS-issued identity'))
        self.project()
        return record

    def start(self, hcid, tx, user_input):
        try:
            identity = self.db.execute('SELECT * FROM identities WHERE hcid=?', (hcid,)).fetchone()
            if not identity or identity['binding'] != 'VERIFIED':
                raise BindingConflict('Identity missing or not verified')
            prior = self.db.execute('SELECT * FROM transactions WHERE tx=?', (tx,)).fetchone()
            if prior:
                if prior['hcid'] != hcid or prior['input'] != user_input:
                    raise ValueError('Transaction ID collision: payload or identity differs')
                return dict(prior)
            unfinished = self.db.execute("SELECT tx FROM transactions WHERE hcid=? AND status!='CHECKPOINTED'", (hcid,)).fetchone()
            if unfinished:
                raise RuntimeError('Resume unfinished transaction first: ' + unfinished['tx'])
            self.verify()
            with self.db:
                self.db.execute('INSERT INTO transactions VALUES(?,?,?,?,?)',
                                (tx, hcid, user_input, 'STARTED', now()))
                self.db.execute('INSERT INTO transcript(tx,ordinal,role,text,sha256,created) VALUES(?,?,?,?,?,?)',
                                (tx, 0, 'HUMAN', user_input, digest(user_input), now()))
            self.project()
            self.verify()
            return dict(self.db.execute('SELECT * FROM transactions WHERE tx=?', (tx,)).fetchone())
        except Exception as e:
            existing = self.db.execute('SELECT hcid,input FROM transactions WHERE tx=?', (tx,)).fetchone()
            collision = existing and (existing['hcid'] != hcid or existing['input'] != user_input)
            self.problem(None if collision else tx, e,
                         {'hcid': hcid, 'role': 'HUMAN', 'text': user_input, 'requested_tx': tx})
            raise

    def append(self, tx, ordinal, role, text):
        if role not in ('HUMAN', 'ASSISTANT') or not isinstance(text, str):
            raise ValueError('Only exact visible text belongs in primary transcript')
        prior = self.db.execute('SELECT * FROM transcript WHERE tx=? AND ordinal=?', (tx, ordinal)).fetchone()
        if prior:
            if prior['role'] != role or prior['text'] != text:
                raise ValueError('Duplicate ordinal differs from preserved evidence')
            return
        transaction = self.get_transaction(tx)
        if transaction and transaction['status'] == 'CHECKPOINTED':
            raise ValueError('Completed transaction is immutable; start a new transaction')
        expected = self.db.execute('SELECT COUNT(*) FROM transcript WHERE tx=?', (tx,)).fetchone()[0]
        if ordinal != expected:
            raise ValueError('Transcript ordinal must preserve order')
        with self.db:
            self.db.execute('INSERT INTO transcript(tx,ordinal,role,text,sha256,created) VALUES(?,?,?,?,?,?)',
                            (tx, ordinal, role, text, digest(text), now()))

    def save_task(self, tx, state):
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO tasks VALUES(?,?)', (tx, encode(state)))

    def task(self, tx):
        row = self.db.execute('SELECT state FROM tasks WHERE tx=?', (tx,)).fetchone()
        return json.loads(row[0]) if row else None

    def get_transaction(self, tx):
        row = self.db.execute('SELECT * FROM transactions WHERE tx=?', (tx,)).fetchone()
        return dict(row) if row else None

    def get_identity(self, hcid):
        row = self.db.execute('SELECT * FROM identities WHERE hcid=?', (hcid,)).fetchone()
        return dict(row) if row else None

    def message_count(self, tx):
        return self.db.execute('SELECT COUNT(*) FROM transcript WHERE tx=?', (tx,)).fetchone()[0]

    def status(self):
        return {'transactions': [dict(r) for r in self.db.execute('SELECT * FROM transactions')],
                'identities': [dict(r) for r in self.db.execute('SELECT * FROM identities')],
                'open_recovery': [dict(r) for r in self.db.execute('SELECT * FROM recovery WHERE closed=0')]}

    def projections(self):
        identities = [dict(r) for r in self.db.execute('SELECT * FROM identities ORDER BY hcid')]
        transactions = [dict(r) for r in self.db.execute('SELECT * FROM transactions ORDER BY created,tx')]
        result = {'bindings.json': encode(identities), 'active-index.json': encode(transactions)}
        for ident in identities:
            messages = [dict(r) for r in self.db.execute('''SELECT transcript.* FROM transcript
                JOIN transactions USING(tx) WHERE hcid=? ORDER BY seq''', (ident['hcid'],))]
            result['pages/' + ident['page'] + '.json'] = encode({'metadata': ident, 'transcript': messages})
            result['pages/' + ident['page'] + '.md'] = '# ' + ident['page'] + '\n\n' + ''.join(
                '## ' + r['role'] + ' — ' + r['tx'] + ':' + str(r['ordinal']) + '\n\n' + r['text'] + '\n\n'
                for r in messages)
        return result

    def write_projection(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + '.pending')
        with open(temp, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
        fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def project(self):
        for name, text in self.projections().items():
            self.write_projection(self.root / name, text)

    def verify(self):
        if self.db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise RuntimeError('Notebook database integrity failure')
        chain = [AuditEvent(r['seq'], r['kind'], r['tx'] or '',
                            {'payload': json.loads(r['payload']), 'created': r['created']},
                            r['previous_hash'], r['event_hash'])
                 for r in self.db.execute('SELECT * FROM events ORDER BY seq')]
        if not verify_chain(chain):
            raise RuntimeError('Audit chain verification failed')
        for row in self.db.execute('SELECT text,sha256 FROM transcript'):
            if digest(row['text']) != row['sha256']:
                raise RuntimeError('Transcript hash mismatch')
        for name, expected in self.projections().items():
            if (self.root / name).read_bytes() != expected.encode('utf-8'):
                raise RuntimeError('Notebook readback mismatch: ' + name)
        return True

    def checkpoint(self, tx):
        try:
            state = self.task(tx)
            if not state or state.get('phase') != 'COMPLETE':
                raise RuntimeError('Final response has not been captured')
            final = self.db.execute('SELECT text,role FROM transcript WHERE tx=? AND ordinal=?',
                                   (tx, state['final_ordinal'])).fetchone()
            if not final or final['role'] != 'ASSISTANT' or final['text'] != state['final']:
                raise RuntimeError('Final response readback differs from task checkpoint')
            self.project()
            self.verify()
            with self.db:
                self.db.execute("UPDATE transactions SET status='CHECKPOINTED' WHERE tx=?", (tx,))
            self.project()
            self.verify()
            with self.db:
                self.db.execute('UPDATE recovery SET closed=1 WHERE tx=?', (tx,))
            self.event(tx, 'CHECKPOINT_VERIFIED', {'verification': 'SQLite, hashes, page, index, binding readback',
                                                 'delivery': state.get('delivery', 'NOT_CONFIRMED')})
            self.verify()
        except Exception as e:
            self.problem(tx, e)
            raise

    def recover(self):
        """Repair only derived projections; never rerun a model/tool on startup."""
        pending = [dict(r) for r in self.db.execute("SELECT * FROM transactions WHERE status!='CHECKPOINTED'")]
        try:
            self.verify()
        except Exception as e:
            self.event(None, 'PROJECTION_RECOVERY', {'error': str(e)})
            # Preserve tampered/stale projections before rebuilding them from evidence.
            import shutil
            folder = self.root / 'recovery-copies' / uuid.uuid4().hex
            folder.mkdir(parents=True)
            for name in self.projections():
                source = self.root / name
                if source.exists():
                    target = folder / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, target)
            self.project()
            self.verify()
        for row in pending:
            state = self.task(row['tx'])
            if state and state.get('phase') == 'COMPLETE':
                self.checkpoint(row['tx'])
            else:
                self.event(row['tx'], 'RESUME_REQUIRED', {'status': row['status']})
        fallback = self.root / 'recovery.jsonl'
        if fallback.exists():
            for line in fallback.read_text(encoding='utf-8').splitlines():
                record = json.loads(line)
                payload = record.get('payload')
                tx = record.get('tx')
                if tx and isinstance(payload, dict) and payload.get('role') == 'HUMAN' and not self.get_transaction(tx):
                    self.start(payload['hcid'], tx, payload['text'])
                    self.event(tx, 'FALLBACK_INPUT_RECOVERED', {'source': str(fallback)})
        return [dict(r) for r in self.db.execute("SELECT * FROM transactions WHERE status!='CHECKPOINTED'")]
