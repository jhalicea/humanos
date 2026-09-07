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
            closed INTEGER NOT NULL DEFAULT 0, created TEXT NOT NULL,
            scope TEXT NOT NULL DEFAULT 'NOTEBOOK');
          CREATE TRIGGER IF NOT EXISTS transcript_no_update BEFORE UPDATE ON transcript
            BEGIN SELECT RAISE(ABORT, 'append-only transcript'); END;
          CREATE TRIGGER IF NOT EXISTS transcript_no_delete BEFORE DELETE ON transcript
            BEGIN SELECT RAISE(ABORT, 'append-only transcript'); END;
          CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events
            BEGIN SELECT RAISE(ABORT, 'append-only events'); END;
          CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
            BEGIN SELECT RAISE(ABORT, 'append-only events'); END;
        ''')
        # Existing vaults retain their rows and original recovery semantics.
        if 'scope' not in {row['name'] for row in self.db.execute('PRAGMA table_info(recovery)')}:
            with self.db:
                self.db.execute("ALTER TABLE recovery ADD COLUMN scope TEXT NOT NULL DEFAULT 'NOTEBOOK'")

    def close(self):
        self.db.close()
        self.lock.close()

    def event(self, tx, kind, payload):
        with self.db:
            self._append_event(tx, kind, payload)

    def _append_event(self, tx, kind, payload):
        """Append inside the caller's transaction when state and evidence must agree."""
        previous = self.db.execute('SELECT seq,event_hash FROM events ORDER BY seq DESC LIMIT 1').fetchone()
        seq, prev = (previous['seq'] + 1, previous['event_hash']) if previous else (1, 'GENESIS')
        stamp = now()
        body = {'payload': payload, 'created': stamp}
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

    def save_task_event(self, tx, state, kind, payload):
        """Commit execution authority and its audit evidence in one transaction."""
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO tasks VALUES(?,?)', (tx, encode(state)))
            self._append_event(tx, kind, payload)

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
                'open_recovery': [dict(r) for r in self.db.execute('SELECT * FROM recovery WHERE closed=0')],
                'pending_delivery': self.delivery_pending()}

    def delivery_pending(self):
        """Saved finals awaiting output, including legacy tasks without delivery metadata."""
        pending = []
        for row in self.db.execute('''SELECT transactions.*,tasks.state FROM transactions
                JOIN tasks USING(tx) ORDER BY transactions.created,transactions.tx'''):
            state = json.loads(row['state'])
            if state.get('phase') != 'COMPLETE' or state.get('delivery') == 'WRITTEN_TO_OUTPUT_STREAM':
                continue
            record = {key: row[key] for key in row.keys() if key != 'state'}
            record.update(recovery_kind='DELIVERY', delivery=state.get('delivery', 'NOT_CONFIRMED'),
                          delivery_attempt=state.get('delivery_attempt'),
                          delivery_error=state.get('delivery_error'))
            pending.append(record)
        return pending

    def _verified_final(self, tx, response=None):
        state = self.task(tx)
        transaction = self.get_transaction(tx)
        if not state or state.get('phase') != 'COMPLETE':
            raise RuntimeError('Cannot deliver before final transcript capture is complete')
        if not transaction or transaction['status'] != 'CHECKPOINTED':
            raise RuntimeError('Cannot deliver before Notebook checkpoint readback')
        final = self.db.execute('SELECT text,role,sha256 FROM transcript WHERE tx=? AND ordinal=?',
                                (tx, state.get('final_ordinal'))).fetchone()
        if (not final or final['role'] != 'ASSISTANT' or final['text'] != state.get('final') or
                digest(final['text']) != final['sha256'] or
                (response is not None and response != final['text'])):
            raise RuntimeError('Delivery response differs from preserved final transcript')
        self.verify()
        return state

    def prepare_delivery(self, tx, response):
        """Durably record an output attempt before the caller writes any characters.

        Returns False for a previously confirmed output. Retrying an uncertain
        attempt may repeat terminal output, but never appends transcript again.
        """
        state = self._verified_final(tx, response)
        if state.get('delivery') == 'WRITTEN_TO_OUTPUT_STREAM':
            return False
        state.update(delivery='DELIVERING', delivery_attempt=uuid.uuid4().hex,
                     delivery_attempts=state.get('delivery_attempts', 0) + 1,
                     delivery_started=now(), delivery_sha256=digest(response))
        state.pop('delivery_error', None)
        with self.db:
            self.db.execute('UPDATE tasks SET state=? WHERE tx=?', (encode(state), tx))
            self._append_event(tx, 'DELIVERY_STARTED', {
                'attempt': state['delivery_attempt'], 'sha256': state['delivery_sha256'],
                'characters_with_terminal_newline': len(response) + 1})
        return True

    def finish_delivery(self, tx):
        """Called only after the full output write and flush both succeed.

        This confirms the output stream, never a claim that a human read it.
        A crash between flush and this commit remains an uncertain outcome.
        """
        state = self._verified_final(tx)
        if state.get('delivery') == 'WRITTEN_TO_OUTPUT_STREAM':
            return False
        if state.get('delivery') != 'DELIVERING' or state.get('delivery_sha256') != digest(state['final']):
            raise RuntimeError('Output confirmation requires a matching durable delivery attempt')
        state.update(delivery='WRITTEN_TO_OUTPUT_STREAM', delivery_finished=now())
        state.pop('delivery_error', None)
        with self.db:
            self.db.execute('UPDATE tasks SET state=? WHERE tx=?', (encode(state), tx))
            self.db.execute("UPDATE recovery SET closed=1 WHERE tx=? AND scope='DELIVERY' AND closed=0", (tx,))
            self._append_event(tx, 'DELIVERY', {'status': state['delivery'],
                                               'attempt': state['delivery_attempt'],
                                               'sha256': state['delivery_sha256']})
        return True

    def _delivery_recovery(self, tx, error, uncertain=False):
        state = self.task(tx)
        if not state or state.get('phase') != 'COMPLETE':
            raise RuntimeError('Delivery recovery requires a saved final response')
        if state.get('delivery') == 'WRITTEN_TO_OUTPUT_STREAM':
            return False
        delivery = 'OUTPUT_UNCERTAIN' if uncertain else state.get('delivery', 'NOT_CONFIRMED')
        existing = self.db.execute("SELECT id FROM recovery WHERE tx=? AND scope='DELIVERY' AND closed=0",
                                   (tx,)).fetchone()
        changed = state.get('delivery') != delivery or state.get('delivery_error') != str(error)
        if existing and not changed:
            return False
        # The fallback survives a failure while updating SQLite task/recovery state.
        record = {'tx': tx, 'scope': 'DELIVERY', 'error': str(error),
                  'payload': {'delivery': delivery, 'attempt': state.get('delivery_attempt')}, 'created': now()}
        with open(self.root / 'recovery.jsonl', 'a', encoding='utf-8') as f:
            f.write(encode(record) + '\n')
            f.flush()
            os.fsync(f.fileno())
        state.update(delivery=delivery, delivery_error=str(error))
        with self.db:
            self.db.execute('UPDATE tasks SET state=? WHERE tx=?', (encode(state), tx))
            if not existing:
                self.db.execute("INSERT INTO recovery(tx,error,created,scope) VALUES(?,?,?,'DELIVERY')",
                                (tx, str(error), now()))
            self._append_event(tx, 'DELIVERY_RECOVERY_REQUIRED', {
                'delivery': delivery, 'error': str(error), 'attempt': state.get('delivery_attempt')})
        return True

    def fail_delivery(self, tx, error):
        """Output may have been partial or flushed; preserve this uncertainty."""
        return self._delivery_recovery(tx, error, uncertain=True)

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
            if self.get_transaction(tx)['status'] == 'CHECKPOINTED':
                self.verify()
                return
            self.project()
            self.verify()
            with self.db:
                self.db.execute("UPDATE transactions SET status='CHECKPOINTED' WHERE tx=?", (tx,))
            self.project()
            self.verify()
            with self.db:
                self.db.execute("UPDATE recovery SET closed=1 WHERE tx=? AND scope='NOTEBOOK'", (tx,))
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
                payload = {'status': row['status']}
                previous = self.db.execute("SELECT payload FROM events WHERE tx=? AND kind='RESUME_REQUIRED' ORDER BY seq DESC LIMIT 1",
                                           (row['tx'],)).fetchone()
                if not previous or json.loads(previous['payload']) != payload:
                    self.event(row['tx'], 'RESUME_REQUIRED', payload)
        fallback = self.root / 'recovery.jsonl'
        delivery_fallback = {}
        if fallback.exists():
            for line in fallback.read_text(encoding='utf-8').splitlines():
                record = json.loads(line)
                payload = record.get('payload')
                tx = record.get('tx')
                if tx and record.get('scope') == 'DELIVERY' and isinstance(payload, dict):
                    delivery_fallback[tx] = record
                if tx and isinstance(payload, dict) and payload.get('role') == 'HUMAN' and not self.get_transaction(tx):
                    self.start(payload['hcid'], tx, payload['text'])
                    self.event(tx, 'FALLBACK_INPUT_RECOVERED', {'source': str(fallback)})
        for delivery in self.delivery_pending():
            record = delivery_fallback.get(delivery['tx'])
            if record and record['payload'].get('attempt') == delivery.get('delivery_attempt'):
                # A failed SQLite update must not discard the specific output
                # failure already retained in the independent recovery ledger.
                delivery['delivery_error'] = record['error']
                if record['payload'].get('delivery') == 'OUTPUT_UNCERTAIN':
                    delivery['delivery'] = 'OUTPUT_UNCERTAIN'
            uncertain = delivery['delivery'] in ('DELIVERING', 'OUTPUT_UNCERTAIN')
            error = delivery.get('delivery_error') or (
                'Process ended during output; terminal delivery is uncertain' if uncertain else
                'Final answer saved and checkpointed; output has not been confirmed')
            self._delivery_recovery(delivery['tx'], error, uncertain=uncertain)
        return ([dict(r) for r in self.db.execute("SELECT * FROM transactions WHERE status!='CHECKPOINTED'")]
                + self.delivery_pending())
