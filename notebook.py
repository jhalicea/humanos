"""HumanOS local Life Notebook adapter. SQLite evidence, replaceable projections.

Historical daily Markdown files are never imported, rebound or modified implicitly.
The process lock is held for the lifetime of a Notebook (single local writer).
"""
import fcntl
import hashlib
import hmac
import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from audit import AuditEvent, hash_event, verify_chain
from audit_privacy import assert_content_light, request_summary
from integrity_lifecycle import bind_integrity_key, load_or_create_integrity_key
from recovery_ledger import parse_recovery_file, validate_recovery_appendable_bytes
from recovery_continuation import verify_active_recovery_continuation


def now():
    return datetime.now(timezone.utc).isoformat()


DIGEST_PREFIX = 'hmac-sha256:'
RECORD_INTEGRITY_PREFIX = 'hmac-sha256-record-v1:'
RECORD_INTEGRITY_VERSION = 1
RECORD_INTEGRITY_POLICY = 'required-v1'
RECORD_INTEGRITY_DOMAIN = b'HumanOS transcript record envelope v1\x00'
RECORD_POLICY_PREFIX = 'hmac-sha256-policy-v1:'
RECORD_POLICY_DOMAIN = b'HumanOS transcript record policy v1\x00'
REQUIRED_RECORD_TRIGGERS = {
    'transcript_require_record_integrity',
    'transcript_seq_monotonic',
    'transcript_seq_matches_counter',
}


def digest(text):
    """Legacy SHA-256 verifier only. New content must use Notebook.content_digest."""
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
        try:
            self.integrity_key = self._load_integrity_key()
        except BaseException:
            self.lock.close()
            raise
        self.db = sqlite3.connect(str(self.root / 'notebook.sqlite3'))
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
          PRAGMA journal_mode=WAL;
          PRAGMA synchronous=FULL;
          PRAGMA foreign_keys=ON;
          PRAGMA busy_timeout=5000;
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
          CREATE TABLE IF NOT EXISTS privacy_state(
            tx TEXT NOT NULL REFERENCES transactions(tx),
            ordinal INTEGER NOT NULL,
            state TEXT NOT NULL CHECK(state IN ('VISIBLE','HIDDEN')),
            updated TEXT NOT NULL,
            PRIMARY KEY(tx, ordinal));
          CREATE TABLE IF NOT EXISTS privacy_operations(
            op_id TEXT PRIMARY KEY, tx TEXT NOT NULL REFERENCES transactions(tx),
            ordinal INTEGER NOT NULL,
            operation TEXT NOT NULL CHECK(operation IN ('HIDE','UNHIDE')),
            actor TEXT NOT NULL, created TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS privacy_receipts(
            receipt_id TEXT PRIMARY KEY,
            op_id TEXT NOT NULL REFERENCES privacy_operations(op_id),
            operation TEXT NOT NULL, actor TEXT NOT NULL, created TEXT NOT NULL);
          CREATE TRIGGER IF NOT EXISTS privacy_receipts_no_update
            BEFORE UPDATE ON privacy_receipts
            BEGIN SELECT RAISE(ABORT, 'append-only privacy receipt'); END;
          CREATE TRIGGER IF NOT EXISTS privacy_receipts_no_delete
            BEFORE DELETE ON privacy_receipts
            BEGIN SELECT RAISE(ABORT, 'append-only privacy receipt'); END;
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

        try:
            # Reject a replaced key before recover() or any later code can append evidence.
            bind_integrity_key(self.db, self.integrity_key)
            self._migrate_record_integrity()
            self._record_trigger_snapshot_at_start = self._record_trigger_snapshot()
            if self._record_trigger_snapshot_at_start is None:
                raise RuntimeError('Record integrity enforcement trigger set is incomplete after startup')
            verify_active_recovery_continuation(self.root, self.integrity_key)
        except BaseException:
            self.db.close()
            self.lock.close()
            raise

    def _load_integrity_key(self):
        """Load/create the stable vault key under fail-closed lifecycle rules."""
        return load_or_create_integrity_key(self.root)

    def content_digest(self, text):
        mac = hmac.new(self.integrity_key, text.encode('utf-8'), hashlib.sha256).hexdigest()
        return DIGEST_PREFIX + mac

    def digest_matches(self, stored, text):
        if not isinstance(stored, str):
            return False
        if stored.startswith(DIGEST_PREFIX):
            return hmac.compare_digest(stored, self.content_digest(text))
        # Backward compatibility only: old vault rows used naked SHA-256.
        return hmac.compare_digest(stored, digest(text))

    @contextmanager
    def _immediate(self):
        """One SQLite write transaction with the write lock acquired up front."""
        if self.db.in_transaction:
            raise RuntimeError('Nested HumanOS write transaction is not allowed')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
        except BaseException:
            self.db.rollback()
            raise
        else:
            self.db.commit()

    def _meta(self, key):
        row = self.db.execute('SELECT value FROM runtime_meta WHERE key=?', (key,)).fetchone()
        return row[0] if row else None

    def _canonical(self, value):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

    def _record_policy_proof(self, activation_seq, legacy_row_count, integrity_key_id):
        payload = {
            'policy': RECORD_INTEGRITY_POLICY,
            'record_integrity_version': RECORD_INTEGRITY_VERSION,
            'activation_seq': int(activation_seq),
            'legacy_row_count': int(legacy_row_count),
            'integrity_key_id': integrity_key_id,
        }
        mac = hmac.new(
            self.integrity_key,
            RECORD_POLICY_DOMAIN + self._canonical(payload).encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()
        return RECORD_POLICY_PREFIX + mac

    def _record_integrity(self, seq, tx, ordinal, role, content_digest, created):
        envelope = {
            'record_type': 'TRANSCRIPT',
            'record_integrity_version': RECORD_INTEGRITY_VERSION,
            'seq': int(seq),
            'tx': tx,
            'ordinal': int(ordinal),
            'role': role,
            'content_digest': content_digest,
            'created': created,
        }
        mac = hmac.new(
            self.integrity_key,
            RECORD_INTEGRITY_DOMAIN + self._canonical(envelope).encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()
        return RECORD_INTEGRITY_PREFIX + mac

    def _create_record_integrity_triggers(self):
        self.db.execute("""CREATE TRIGGER IF NOT EXISTS transcript_require_record_integrity
            BEFORE INSERT ON transcript
            WHEN (
                 NEW.record_integrity IS NULL
                 OR NEW.record_integrity_version IS NULL
                 OR NEW.record_integrity_version != 1
                 OR length(NEW.record_integrity) != 86
                 OR NEW.record_integrity NOT LIKE 'hmac-sha256-record-v1:%'
             )
            BEGIN
                SELECT RAISE(ABORT, 'HumanOS Security Violation: transcript record envelope required');
            END""")
        self.db.execute("""CREATE TRIGGER IF NOT EXISTS transcript_seq_monotonic
            BEFORE INSERT ON transcript
            WHEN NEW.seq <= (SELECT COALESCE(MAX(seq), 0) FROM transcript)
            BEGIN
                SELECT RAISE(ABORT, 'HumanOS Security Violation: transcript seq not monotonic');
            END""")
        self.db.execute("""CREATE TRIGGER IF NOT EXISTS transcript_seq_matches_counter
            BEFORE INSERT ON transcript
            WHEN (SELECT COUNT(*) FROM transcript_sequence WHERE id=1) != 1
              OR NEW.seq != (SELECT next_seq - 1 FROM transcript_sequence WHERE id=1)
            BEGIN
                SELECT RAISE(ABORT, 'HumanOS Security Violation: transcript seq does not match reserved counter');
            END""")

    def _record_trigger_snapshot(self):
        names = tuple(sorted(REQUIRED_RECORD_TRIGGERS))
        placeholders = ','.join('?' for _ in names)
        rows = list(self.db.execute(
            "SELECT name,sql FROM sqlite_master WHERE type='trigger' AND name IN ("
            + placeholders + ') ORDER BY name', names
        ))
        if len(rows) != len(names):
            return None
        return tuple((row['name'], row['sql']) for row in rows)

    def _verify_policy(self):
        policy = self._meta('record_integrity_policy')
        activation = self._meta('record_integrity_activation_seq')
        legacy_count = self._meta('record_integrity_legacy_row_count')
        proof = self._meta('record_integrity_policy_proof')
        key_identity = self._meta('integrity_key_id')
        if (policy != RECORD_INTEGRITY_POLICY or activation is None or legacy_count is None
                or proof is None or key_identity is None):
            raise RuntimeError('Record integrity policy metadata is missing or downgraded')
        try:
            activation_seq = int(activation)
            legacy_row_count = int(legacy_count)
        except (TypeError, ValueError) as error:
            raise RuntimeError('Record integrity activation boundary or legacy row count is invalid') from error
        if activation_seq < 0 or legacy_row_count < 0 or legacy_row_count > activation_seq:
            raise RuntimeError('Record integrity activation boundary or legacy row count is invalid')
        expected = self._record_policy_proof(activation_seq, legacy_row_count, key_identity)
        if not isinstance(proof, str) or not hmac.compare_digest(proof, expected):
            raise RuntimeError('Record integrity policy authentication failed')
        return activation_seq

    def _verify_record_integrity(self, row, activation_seq):
        stored = row['record_integrity']
        version = row['record_integrity_version']
        required = row['seq'] > activation_seq
        if stored is None and version is None:
            if required:
                raise RuntimeError('Transcript record envelope missing after activation boundary')
            return 'CONTENT_VERIFIED_METADATA_LEGACY'
        if stored is None or version is None:
            raise RuntimeError('Transcript record integrity is partial')
        if version != RECORD_INTEGRITY_VERSION:
            raise RuntimeError('Unsupported transcript record integrity version')
        if (not isinstance(stored, str) or not stored.startswith(RECORD_INTEGRITY_PREFIX)
                or len(stored) != len(RECORD_INTEGRITY_PREFIX) + 64):
            raise RuntimeError('Transcript record integrity encoding is invalid')
        expected = self._record_integrity(
            row['seq'], row['tx'], row['ordinal'], row['role'], row['sha256'], row['created']
        )
        if not hmac.compare_digest(stored, expected):
            raise RuntimeError('Transcript record integrity mismatch')
        return 'ENVELOPE_VERIFIED'

    def _verify_record_state(self, require_triggers=True):
        activation_seq = self._verify_policy()
        tables = {row[0] for row in self.db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
        if 'transcript_sequence' not in tables:
            raise RuntimeError('Transcript sequence counter table is missing')
        counter_rows = list(self.db.execute('SELECT id,next_seq FROM transcript_sequence'))
        if len(counter_rows) != 1 or counter_rows[0]['id'] != 1:
            raise RuntimeError('Transcript sequence counter row is missing or invalid')
        next_seq = counter_rows[0]['next_seq']
        if isinstance(next_seq, bool) or not isinstance(next_seq, int) or next_seq < 1:
            raise RuntimeError('Transcript sequence counter value is invalid')
        max_seq = self.db.execute('SELECT COALESCE(MAX(seq),0) FROM transcript').fetchone()[0]
        if next_seq != max_seq + 1:
            raise RuntimeError('Transcript sequence continuity mismatch')
        if max_seq < activation_seq:
            raise RuntimeError('Transcript sequence is below authenticated activation boundary')
        expected_legacy_count = int(self._meta('record_integrity_legacy_row_count'))
        actual_legacy_count = self.db.execute(
            'SELECT COUNT(*) FROM transcript WHERE seq <= ?', (activation_seq,)
        ).fetchone()[0]
        if actual_legacy_count != expected_legacy_count:
            raise RuntimeError('Legacy transcript row count mismatch')
        post_count = self.db.execute(
            'SELECT COUNT(*) FROM transcript WHERE seq > ?', (activation_seq,)
        ).fetchone()[0]
        if post_count != max_seq - activation_seq:
            raise RuntimeError('Transcript sequence gap detected after activation boundary')
        for row in self.db.execute('SELECT * FROM transcript ORDER BY seq'):
            if not self.digest_matches(row['sha256'], row['text']):
                raise RuntimeError('Transcript hash mismatch')
            self._verify_record_integrity(row, activation_seq)
        if require_triggers:
            triggers = {row[0] for row in self.db.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger'"
            )}
            missing = REQUIRED_RECORD_TRIGGERS - triggers
            if missing:
                raise RuntimeError('Record integrity enforcement trigger missing: ' + ','.join(sorted(missing)))
        return True

    def _migrate_record_integrity(self):
        columns = {row['name'] for row in self.db.execute('PRAGMA table_info(transcript)')}
        have_integrity = 'record_integrity' in columns
        have_version = 'record_integrity_version' in columns
        if have_integrity != have_version:
            raise RuntimeError('Partial record integrity schema detected')

        policy = self._meta('record_integrity_policy')
        if not have_integrity:
            if policy is not None:
                raise RuntimeError('Record integrity policy exists without required schema')
            with self._immediate():
                self.db.execute('ALTER TABLE transcript ADD COLUMN record_integrity TEXT')
                self.db.execute('ALTER TABLE transcript ADD COLUMN record_integrity_version INTEGER')
                self.db.execute("""CREATE TABLE transcript_sequence(
                    id INTEGER PRIMARY KEY CHECK(id=1),
                    next_seq INTEGER NOT NULL CHECK(next_seq >= 1)
                )""")
                activation_seq = self.db.execute(
                    'SELECT COALESCE(MAX(seq),0) FROM transcript'
                ).fetchone()[0]
                legacy_row_count = self.db.execute(
                    'SELECT COUNT(*) FROM transcript WHERE seq <= ?', (activation_seq,)
                ).fetchone()[0]
                self.db.execute(
                    'INSERT INTO transcript_sequence(id,next_seq) VALUES(1,?)',
                    (activation_seq + 1,),
                )
                key_identity = self._meta('integrity_key_id')
                proof = self._record_policy_proof(activation_seq, legacy_row_count, key_identity)
                self.db.execute(
                    'INSERT INTO runtime_meta(key,value) VALUES(?,?)',
                    ('record_integrity_policy', RECORD_INTEGRITY_POLICY),
                )
                self.db.execute(
                    'INSERT INTO runtime_meta(key,value) VALUES(?,?)',
                    ('record_integrity_activation_seq', str(activation_seq)),
                )
                self.db.execute(
                    'INSERT INTO runtime_meta(key,value) VALUES(?,?)',
                    ('record_integrity_legacy_row_count', str(legacy_row_count)),
                )
                self.db.execute(
                    'INSERT INTO runtime_meta(key,value) VALUES(?,?)',
                    ('record_integrity_policy_proof', proof),
                )
                self._create_record_integrity_triggers()
            return

        # Existing upgraded state must be internally valid before canonical
        # enforcement triggers are restored. Replacing same-name/no-op triggers
        # prevents a stale or substituted definition surviving a clean restart.
        self._verify_record_state(require_triggers=False)
        with self._immediate():
            for trigger_name in sorted(REQUIRED_RECORD_TRIGGERS):
                self.db.execute('DROP TRIGGER IF EXISTS ' + trigger_name)
            self._create_record_integrity_triggers()
        self._verify_record_state(require_triggers=True)

    def _assert_record_write_boundary(self):
        """O(1) fail-closed guard for mutable enforcement state before append."""
        if not self.db.in_transaction:
            raise RuntimeError('Record integrity write-boundary check requires an active transaction')
        self._verify_policy()
        expected_triggers = getattr(self, '_record_trigger_snapshot_at_start', None)
        current_triggers = self._record_trigger_snapshot()
        if expected_triggers is None or current_triggers != expected_triggers:
            raise RuntimeError('Record integrity enforcement trigger definition changed after Notebook startup')
        counter_rows = list(self.db.execute('SELECT id,next_seq FROM transcript_sequence'))
        if len(counter_rows) != 1 or counter_rows[0]['id'] != 1:
            raise RuntimeError('Transcript sequence counter row is missing or invalid before write')
        next_seq = counter_rows[0]['next_seq']
        if isinstance(next_seq, bool) or not isinstance(next_seq, int) or next_seq < 1:
            raise RuntimeError('Transcript sequence counter value is invalid before write')
        max_seq = self.db.execute('SELECT COALESCE(MAX(seq),0) FROM transcript').fetchone()[0]
        if next_seq != max_seq + 1:
            raise RuntimeError('Transcript sequence continuity mismatch before write')

    def _reserve_transcript_seq(self):
        if not self.db.in_transaction:
            raise RuntimeError('Transcript sequence allocation requires an active transaction')
        self._assert_record_write_boundary()
        changed = self.db.execute(
            'UPDATE transcript_sequence SET next_seq = next_seq + 1 WHERE id=1'
        ).rowcount
        if changed != 1:
            raise RuntimeError('Transcript sequence counter allocation failed')
        row = self.db.execute(
            'SELECT next_seq - 1 FROM transcript_sequence WHERE id=1'
        ).fetchone()
        if row is None:
            raise RuntimeError('Transcript sequence counter row is missing')
        return row[0]

    def _insert_transcript(self, tx, ordinal, role, text):
        seq = self._reserve_transcript_seq()
        stamp = now()
        content_digest = self.content_digest(text)
        record_integrity = self._record_integrity(
            seq, tx, ordinal, role, content_digest, stamp
        )
        self.db.execute("""INSERT INTO transcript(
            seq,tx,ordinal,role,text,sha256,created,record_integrity,record_integrity_version
        ) VALUES(?,?,?,?,?,?,?,?,?)""", (
            seq, tx, ordinal, role, text, content_digest, stamp,
            record_integrity, RECORD_INTEGRITY_VERSION,
        ))

    def close(self):
        self.db.close()
        self.lock.close()

    def set_privacy(self, tx, ordinal, operation, actor='human:jon',
                    confirmation=None, request_id=None):
        if operation not in ('HIDE', 'UNHIDE'):
            raise ValueError('Unsupported privacy operation')
        if actor != 'human:jon' or confirmation != operation:
            raise PermissionError('Human confirmation required')
        if not self.db.execute(
                'SELECT 1 FROM transcript WHERE tx=? AND ordinal=?',
                (tx, ordinal)).fetchone():
            raise ValueError('Privacy target does not exist')

        op_id = request_id or ('POP-' + uuid.uuid4().hex)
        prior = self.db.execute(
            'SELECT receipt_id FROM privacy_receipts WHERE op_id=?', (op_id,)
        ).fetchone()
        if prior:
            return prior['receipt_id']
        receipt_id = 'PR-' + uuid.uuid4().hex
        state = 'HIDDEN' if operation == 'HIDE' else 'VISIBLE'
        stamp = now()

        with self._immediate():
            self.db.execute(
                'INSERT INTO privacy_operations VALUES(?,?,?,?,?,?)',
                (op_id, tx, ordinal, operation, actor, stamp))
            self.db.execute(
                'INSERT OR REPLACE INTO privacy_state VALUES(?,?,?,?)',
                (tx, ordinal, state, stamp))
            self.db.execute(
                'INSERT INTO privacy_receipts VALUES(?,?,?,?,?)',
                (receipt_id, op_id, operation, actor, stamp))

        try:
            self.project()
            self.verify()
        except BaseException as error:
            self.problem(tx, error, {
                'scope': 'PRIVACY_PROJECTION',
                'operation': operation,
                'op_id': op_id,
            })
            raise
        return receipt_id

    def event(self, tx, kind, payload):
        with self.db:
            self._append_event(tx, kind, payload)

    def _append_event(self, tx, kind, payload):
        """Append content-light evidence inside the caller's state transaction."""
        assert_content_light(payload)
        previous = self.db.execute('SELECT seq,event_hash FROM events ORDER BY seq DESC LIMIT 1').fetchone()
        seq, prev = (previous['seq'] + 1, previous['event_hash']) if previous else (1, 'GENESIS')
        stamp = now()
        body = {'payload': payload, 'created': stamp}
        self.db.execute('INSERT INTO events VALUES(?,?,?,?,?,?,?)',
                        (seq, tx, kind, encode(payload), stamp, prev,
                         hash_event(seq, kind, tx or '', body, prev)))

    def _append_recovery_record(self, record):
        """Append one physical UTF-8 JSON record only after validating existing evidence."""
        path = self.root / 'recovery.jsonl'
        data = (encode(record) + '\n').encode('utf-8')
        flags = os.O_RDWR | os.O_APPEND | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0)
        fd = os.open(str(path), flags, 0o600)
        try:
            size = os.fstat(fd).st_size
            existing = bytearray()
            if size:
                os.lseek(fd, 0, os.SEEK_SET)
                while len(existing) < size:
                    block = os.read(fd, min(1024 * 1024, size - len(existing)))
                    if not block:
                        break
                    existing.extend(block)
                if len(existing) != size:
                    raise OSError('short recovery ledger read during append validation')
                validate_recovery_appendable_bytes(bytes(existing))
                if os.fstat(fd).st_size != size:
                    raise RuntimeError('Recovery ledger changed while validating append boundary')
            offset = 0
            while offset < len(data):
                count = os.write(fd, data[offset:])
                if count <= 0:
                    raise OSError('short recovery ledger write')
                offset += count
            os.fsync(fd)
        finally:
            os.close(fd)

    def problem(self, tx, error, payload=None):
        # Independent fsynced fallback retains the exact input even if SQLite fails.
        record = {'tx': tx, 'error': str(error), 'payload': payload, 'created': now()}
        self._append_recovery_record(record)
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
                  'opening_hash': self.content_digest(opening), 'created': now()}
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
            # An unfinished turn remains independently resumable. It must not
            # silence later human input or block the rest of the Notebook page.
            # Transcript sequence still records the order in which messages are
            # actually captured, including a late response to an older turn.
            self.verify()
            with self._immediate():
                self.db.execute('INSERT INTO transactions VALUES(?,?,?,?,?)',
                                (tx, hcid, user_input, 'STARTED', now()))
                self._insert_transcript(tx, 0, 'HUMAN', user_input)
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
        with self._immediate():
            self._insert_transcript(tx, ordinal, role, text)

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

    def finalize_failure(self, tx, message, reason):
        """Capture a failed task's exact final without treating execution as successful.

        This closes execution, not outstanding reconciliation or output delivery.
        The original task remains in failure_snapshot; a pending mutation is never
        retried here. Transcript, closure, recovery, and audit evidence commit
        together, so retry after a crash either creates one closure or reads it.
        """
        if not isinstance(message, str) or not message:
            raise ValueError('Failure final must be nonempty exact visible text')
        transaction = self.get_transaction(tx)
        if not transaction:
            raise ValueError('Cannot close an unknown transaction')
        identity = self.get_identity(transaction['hcid'])
        if not identity or identity['binding'] != 'VERIFIED':
            raise BindingConflict('Failure closure requires verified identity binding')
        state = self.task(tx)
        if state and state.get('phase') == 'EXTERNAL_CAPTURE_PENDING':
            raise RuntimeError('External transcript capture requires host reconciliation')
        if state and state.get('phase') == 'COMPLETE':
            if not state.get('failure_finalized'):
                raise ValueError('Existing final response is immutable')
            self.checkpoint(tx)
            return state['final']
        if transaction['status'] == 'CHECKPOINTED':
            raise ValueError('Completed transaction is immutable')

        human = self.db.execute('SELECT * FROM transcript WHERE tx=? AND ordinal=0', (tx,)).fetchone()
        if (not human or human['role'] != 'HUMAN' or human['text'] != transaction['input'] or
                not self.digest_matches(human['sha256'], human['text'])):
            raise RuntimeError('Failure closure requires the preserved exact human input')
        original = json.loads(encode(state)) if state else {}
        ordinal = original.get('final_ordinal', self.message_count(tx))
        if isinstance(ordinal, bool) or not isinstance(ordinal, int) or ordinal < 1:
            raise ValueError('Invalid failure final ordinal')
        prior = self.db.execute('SELECT * FROM transcript WHERE tx=? AND ordinal=?', (tx, ordinal)).fetchone()
        if prior:
            if (prior['role'] != 'ASSISTANT' or prior['text'] != message or
                    not self.digest_matches(prior['sha256'], message) or ordinal != self.message_count(tx) - 1):
                raise ValueError('Failure final collides with preserved transcript evidence')
        elif ordinal != self.message_count(tx):
            raise ValueError('Failure final must preserve transcript order')

        # The registry supplies effect metadata, not authority to execute. An
        # unknown interrupted operation is conservatively left for inspection.
        from capabilities import REGISTRY
        pending = original.get('pending') or {}
        effect = REGISTRY.get(pending.get('name'), {}).get('effect') if isinstance(pending, dict) else None
        uncertain = original.get('phase') == 'EXECUTING' and effect not in ('read', 'network_read', 'plan')
        outcome = 'NEEDS_RECONCILIATION' if uncertain else 'FAILED'
        closed = dict(original, phase='COMPLETE', final=message, final_ordinal=ordinal,
                      delivery='PREPARED_NOT_CONFIRMED', outcome=outcome,
                      failure_finalized=True, failure_reason=str(reason), failure_closed_at=now(),
                      failure_snapshot=original, failure_transaction_status=transaction['status'])
        try:
            with self._immediate():
                if not prior:
                    self._insert_transcript(tx, ordinal, 'ASSISTANT', message)
                self.db.execute('INSERT OR REPLACE INTO tasks VALUES(?,?)', (tx, encode(closed)))
                self.db.execute("INSERT INTO recovery(tx,error,created,scope) VALUES(?,?,?,'TASK')",
                                (tx, outcome + ': ' + str(reason), now()))
                self._append_event(tx, 'TASK_FAILURE_FINALIZED', {
                    'outcome': outcome, 'reason': str(reason), 'final_ordinal': ordinal,
                    'final_digest': self.content_digest(message), 'prior_phase': original.get('phase'),
                    'prior_state_digest': self.content_digest(encode(original)),
                    'pending_request': request_summary(self, pending) if pending else None,
                    'execution_closed': True, 'reconciliation_closed': False})
        except Exception as error:
            self.problem(tx, error, {'failure_final': message, 'failure_reason': str(reason)})
            raise
        self.checkpoint(tx)
        return message

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
                not self.digest_matches(final['sha256'], final['text']) or
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
                     delivery_started=now(), delivery_digest=self.content_digest(response))
        state.pop('delivery_sha256', None)
        state.pop('delivery_error', None)
        with self.db:
            self.db.execute('UPDATE tasks SET state=? WHERE tx=?', (encode(state), tx))
            self._append_event(tx, 'DELIVERY_STARTED', {
                'attempt': state['delivery_attempt'], 'content_digest': state['delivery_digest'],
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
        stored_delivery_digest = state.get('delivery_digest', state.get('delivery_sha256'))
        if state.get('delivery') != 'DELIVERING' or not self.digest_matches(stored_delivery_digest, state['final']):
            raise RuntimeError('Output confirmation requires a matching durable delivery attempt')
        state.update(delivery='WRITTEN_TO_OUTPUT_STREAM', delivery_finished=now())
        state.pop('delivery_error', None)
        with self.db:
            self.db.execute('UPDATE tasks SET state=? WHERE tx=?', (encode(state), tx))
            self.db.execute("UPDATE recovery SET closed=1 WHERE tx=? AND scope='DELIVERY' AND closed=0", (tx,))
            self._append_event(tx, 'DELIVERY', {'status': state['delivery'],
                                               'attempt': state['delivery_attempt'],
                                               'content_digest': stored_delivery_digest})
        return True

    def _delivery_recovery(self, tx, error, uncertain=False, fallback_already_recorded=False):
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
        if not fallback_already_recorded:
            self._append_recovery_record(record)
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
            messages = [dict(r) for r in self.db.execute('''SELECT transcript.seq,
                transcript.tx, transcript.ordinal, transcript.role,
                CASE WHEN COALESCE(p.state,'VISIBLE')='HIDDEN'
                     THEN '[HIDDEN — content withheld]'
                     ELSE transcript.text END AS text,
                transcript.sha256, transcript.created,
                transcript.record_integrity, transcript.record_integrity_version
                FROM transcript
                JOIN transactions USING(tx)
                LEFT JOIN privacy_state p
                  ON p.tx=transcript.tx AND p.ordinal=transcript.ordinal
                WHERE hcid=?
                ORDER BY seq''', (ident['hcid'],))]
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
        self._verify_record_state(require_triggers=True)
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
        recovery_ledger_sealed = False
        if fallback.exists():
            parsed = parse_recovery_file(fallback)
            recovery_ledger_sealed = bool(parsed.anomaly or parsed.quarantine)
            for kind, notice in (
                    ('RECOVERY_UNTERMINATED_RECORD', parsed.anomaly),
                    ('RECOVERY_CRASH_TAIL_QUARANTINED', parsed.quarantine)):
                if notice:
                    keys = ('source_path', 'tail_offset_bytes', 'tail_length_bytes',
                            'tail_sha256', 'classification')
                    payload = {key: notice[key] for key in keys if key in notice}
                    encoded_payload = encode(payload)
                    prior_notice = self.db.execute(
                        'SELECT 1 FROM events WHERE kind=? AND payload=? LIMIT 1',
                        (kind, encoded_payload),
                    ).fetchone()
                    if not prior_notice:
                        self.event(None, kind, payload)
            for record in parsed.records:
                payload = record.get('payload')
                tx = record.get('tx')
                if tx and record.get('scope') == 'DELIVERY' and isinstance(payload, dict):
                    delivery_fallback[(tx, payload.get('attempt'))] = record
                if tx and isinstance(payload, dict) and payload.get('role') == 'HUMAN' and not self.get_transaction(tx):
                    self.start(payload['hcid'], tx, payload['text'])
                    self.event(tx, 'FALLBACK_INPUT_RECOVERED', {'source': str(fallback)})
        for delivery in self.delivery_pending():
            attempt = delivery.get('delivery_attempt')
            record = delivery_fallback.get((delivery['tx'], attempt))
            if record:
                # A failed SQLite update must not discard the specific output
                # failure already retained in the independent recovery ledger.
                delivery['delivery_error'] = record['error']
                if record['payload'].get('delivery') == 'OUTPUT_UNCERTAIN':
                    delivery['delivery'] = 'OUTPUT_UNCERTAIN'
            elif recovery_ledger_sealed:
                # The preserved tail seals this fallback file. Without already-recorded
                # matching delivery evidence, leave the pending delivery visible rather
                # than mutating the ledger or failing the whole recovery pass.
                continue
            uncertain = delivery['delivery'] in ('DELIVERING', 'OUTPUT_UNCERTAIN')
            error = delivery.get('delivery_error') or (
                'Process ended during output; terminal delivery is uncertain' if uncertain else
                'Final answer saved and checkpointed; output has not been confirmed')
            self._delivery_recovery(
                delivery['tx'], error, uncertain=uncertain,
                fallback_already_recorded=record is not None,
            )
        return ([dict(r) for r in self.db.execute("SELECT * FROM transactions WHERE status!='CHECKPOINTED'")]
                + self.delivery_pending())
