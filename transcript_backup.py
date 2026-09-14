"""Verified local transcript batching for off-device backup.

This module is deliberately transport-independent. Universal Conversation Capture
writes exact visible messages into the Life Notebook first. TranscriptBatchOutbox
then packages already-verified transcript rows into immutable local batch files.
A Google Drive (or other) transport may upload those files later and must read
back/verify their bytes before calling ``confirm_upload``.

The backup cursor advances only after every artifact in a batch has been verified
against the local SHA-256 recorded in the manifest. Therefore a network failure,
connector outage, or process crash never makes HumanOS believe unsent transcript
rows were backed up.
"""

import hashlib
import json
import os
import shutil
from pathlib import Path

from notebook import now


FORMAT = 'humanos-transcript-batch'
VERSION = 1
CURSOR_FORMAT = 'humanos-transcript-backup-cursor'
CURSOR_VERSION = 1
ARTIFACT_JSONL = 'transcript.jsonl'
ARTIFACT_MARKDOWN = 'transcript.md'
MANIFEST = 'manifest.json'


class TranscriptBackupError(RuntimeError):
    pass


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _fsync_dir(path):
    if os.name != 'posix':
        return
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _write_atomic(path, data, mode=0o600):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp = path.with_name('.' + path.name + '.pending')
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(str(temp), flags, mode)
    try:
        offset = 0
        while offset < len(data):
            count = os.write(fd, data[offset:])
            if count <= 0:
                raise OSError('short transcript backup write')
            offset += count
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(temp, path)
    _fsync_dir(path.parent)


def _append_fsynced(path, data, mode=0o600):
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(str(path), flags, mode)
    try:
        offset = 0
        while offset < len(data):
            count = os.write(fd, data[offset:])
            if count <= 0:
                raise OSError('short transcript backup receipt write')
            offset += count
        os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_dir(Path(path).parent)


class TranscriptBatchOutbox:
    """Prepare immutable transcript batches and track verified remote delivery.

    ``book`` is the already-open local ``Notebook``. ``outbox`` defaults to a
    private directory under the Notebook runtime. No network access occurs here.
    """

    def __init__(self, book, outbox=None):
        self.book = book
        self.root = Path(outbox or (book.root / 'transcript-backup')).resolve()
        self.pending = self.root / 'pending'
        self.confirmed = self.root / 'confirmed'
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.pending.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.confirmed.mkdir(parents=True, exist_ok=True, mode=0o700)
        if os.name == 'posix':
            for path in (self.root, self.pending, self.confirmed):
                os.chmod(path, 0o700)

    @property
    def cursor_path(self):
        return self.root / 'cursor.json'

    @property
    def receipts_path(self):
        return self.root / 'receipts.jsonl'

    def _cursor_payload(self, last_confirmed_seq, updated=None):
        payload = {
            'format': CURSOR_FORMAT,
            'version': CURSOR_VERSION,
            'last_confirmed_seq': int(last_confirmed_seq),
            'updated': updated or now(),
        }
        payload['proof'] = self.book.content_digest(_canonical(payload))
        return payload

    def _read_cursor(self):
        if not self.cursor_path.exists():
            return 0
        try:
            value = json.loads(self.cursor_path.read_text(encoding='utf-8'))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise TranscriptBackupError('Transcript backup cursor is unreadable') from error
        required = {'format', 'version', 'last_confirmed_seq', 'updated', 'proof'}
        if not isinstance(value, dict) or set(value) != required:
            raise TranscriptBackupError('Transcript backup cursor is malformed')
        if value['format'] != CURSOR_FORMAT or value['version'] != CURSOR_VERSION:
            raise TranscriptBackupError('Unsupported transcript backup cursor')
        seq = value['last_confirmed_seq']
        if isinstance(seq, bool) or not isinstance(seq, int) or seq < 0:
            raise TranscriptBackupError('Transcript backup cursor sequence is invalid')
        unsigned = {key: value[key] for key in value if key != 'proof'}
        expected = self.book.content_digest(_canonical(unsigned))
        if value['proof'] != expected:
            raise TranscriptBackupError('Transcript backup cursor authentication failed')
        return seq

    def last_confirmed_seq(self):
        return self._read_cursor()

    def _write_cursor(self, seq):
        payload = self._cursor_payload(seq)
        _write_atomic(self.cursor_path, (_canonical(payload) + '\n').encode('utf-8'))
        check = self._read_cursor()
        if check != seq:
            raise TranscriptBackupError('Transcript backup cursor readback mismatch')

    def _pending_manifests(self):
        manifests = []
        for path in sorted(self.pending.glob('TB-*/' + MANIFEST)):
            manifests.append(self._load_manifest(path.parent))
        return manifests

    def _load_manifest(self, batch_dir):
        batch_dir = Path(batch_dir)
        path = batch_dir / MANIFEST
        try:
            manifest = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise TranscriptBackupError('Transcript batch manifest is unreadable') from error
        required = {
            'format', 'version', 'batch_id', 'created', 'first_seq', 'last_seq',
            'record_count', 'files', 'manifest_proof'
        }
        if not isinstance(manifest, dict) or set(manifest) != required:
            raise TranscriptBackupError('Transcript batch manifest is malformed')
        if manifest['format'] != FORMAT or manifest['version'] != VERSION:
            raise TranscriptBackupError('Unsupported transcript batch format')
        unsigned = {key: manifest[key] for key in manifest if key != 'manifest_proof'}
        expected_proof = self.book.content_digest(_canonical(unsigned))
        if manifest['manifest_proof'] != expected_proof:
            raise TranscriptBackupError('Transcript batch manifest authentication failed')
        if manifest['record_count'] <= 0 or manifest['first_seq'] <= 0 or manifest['last_seq'] < manifest['first_seq']:
            raise TranscriptBackupError('Transcript batch sequence range is invalid')
        if set(manifest['files']) != {ARTIFACT_JSONL, ARTIFACT_MARKDOWN}:
            raise TranscriptBackupError('Transcript batch artifact set is invalid')
        for name, record in manifest['files'].items():
            if not isinstance(record, dict) or set(record) != {'bytes', 'sha256'}:
                raise TranscriptBackupError('Transcript batch artifact metadata is malformed')
            data = (batch_dir / name).read_bytes()
            if record['bytes'] != len(data) or record['sha256'] != _sha256(data):
                raise TranscriptBackupError('Transcript batch artifact readback mismatch: ' + name)
        return manifest

    def _reconcile_committed_pending(self, cursor):
        """Finish local housekeeping after a crash following cursor commit.

        The authenticated cursor is written only after remote readback verification.
        If the process died before moving the local batch from pending to confirmed,
        this safely completes that move on the next pass.
        """
        for manifest in sorted(self._pending_manifests(), key=lambda value: value['first_seq']):
            if manifest['last_seq'] > cursor:
                continue
            source = self.pending / manifest['batch_id']
            destination = self.confirmed / manifest['batch_id']
            if destination.exists():
                raise TranscriptBackupError('Transcript batch exists in pending and confirmed locations')
            os.replace(source, destination)
            _fsync_dir(self.pending)
            _fsync_dir(self.confirmed)

    def _select_rows(self, after_seq, max_records):
        if isinstance(max_records, bool) or not isinstance(max_records, int) or max_records < 1:
            raise ValueError('max_records must be a positive integer')
        rows = self.book.db.execute('''
            SELECT transcript.seq, transcript.tx, transcript.ordinal, transcript.role,
                   transcript.text, transcript.sha256 AS content_digest,
                   transcript.created, identities.page
              FROM transcript
              JOIN transactions ON transactions.tx = transcript.tx
              JOIN identities ON identities.hcid = transactions.hcid
             WHERE transcript.seq > ?
             ORDER BY transcript.seq
             LIMIT ?
        ''', (after_seq, max_records)).fetchall()
        return [dict(row) for row in rows]

    def _jsonl(self, rows):
        lines = []
        for row in rows:
            record = {
                'seq': row['seq'],
                'page': row['page'],
                'tx': row['tx'],
                'ordinal': row['ordinal'],
                'role': row['role'],
                # The JSON string preserves the exact visible text after UTF-8
                # decode/encode. It is never summarized or normalized.
                'text': row['text'],
                'content_digest': row['content_digest'],
                'created': row['created'],
            }
            lines.append(_canonical(record))
        return ('\n'.join(lines) + '\n').encode('utf-8')

    def _markdown(self, rows, batch_id):
        # Markdown is a readable projection only. JSONL is the exact machine
        # backup and SQLite remains the local source of truth.
        parts = ['# HumanOS Transcript Batch ' + batch_id + '\n\n']
        for row in rows:
            parts.append('## ' + row['role'] + ' — seq ' + str(row['seq']) +
                         ' — ' + row['tx'] + ':' + str(row['ordinal']) + '\n\n')
            parts.append(row['text'])
            parts.append('\n\n')
        return ''.join(parts).encode('utf-8')

    def prepare_batch(self, max_records=100):
        """Prepare the next immutable local batch without advancing the cursor.

        If a batch is already pending at the current cursor boundary, return that
        same batch so retries cannot create overlapping backup ranges.
        """
        self.book.verify()
        cursor = self._read_cursor()
        self._reconcile_committed_pending(cursor)
        pending = self._pending_manifests()
        if pending:
            pending.sort(key=lambda value: value['first_seq'])
            first = pending[0]
            if first['first_seq'] != cursor + 1:
                raise TranscriptBackupError('Pending transcript batch does not match backup cursor')
            if len(pending) > 1:
                raise TranscriptBackupError('Multiple pending transcript batches require reconciliation')
            return first

        rows = self._select_rows(cursor, max_records)
        if not rows:
            return None
        if rows[0]['seq'] != cursor + 1:
            raise TranscriptBackupError('Transcript sequence is not contiguous at backup boundary')
        for previous, current in zip(rows, rows[1:]):
            if current['seq'] != previous['seq'] + 1:
                raise TranscriptBackupError('Transcript sequence gap detected while preparing backup')

        first_seq, last_seq = rows[0]['seq'], rows[-1]['seq']
        seed = str(first_seq) + ':' + str(last_seq) + ':' + rows[-1]['content_digest']
        short = self.book.content_digest(seed).rsplit(':', 1)[-1][:12]
        batch_id = 'TB-' + str(first_seq).zfill(12) + '-' + str(last_seq).zfill(12) + '-' + short
        batch_dir = self.pending / batch_id
        if batch_dir.exists():
            return self._load_manifest(batch_dir)
        batch_dir.mkdir(mode=0o700)
        if os.name == 'posix':
            os.chmod(batch_dir, 0o700)

        try:
            jsonl = self._jsonl(rows)
            markdown = self._markdown(rows, batch_id)
            _write_atomic(batch_dir / ARTIFACT_JSONL, jsonl)
            _write_atomic(batch_dir / ARTIFACT_MARKDOWN, markdown)
            unsigned = {
                'format': FORMAT,
                'version': VERSION,
                'batch_id': batch_id,
                'created': now(),
                'first_seq': first_seq,
                'last_seq': last_seq,
                'record_count': len(rows),
                'files': {
                    ARTIFACT_JSONL: {'bytes': len(jsonl), 'sha256': _sha256(jsonl)},
                    ARTIFACT_MARKDOWN: {'bytes': len(markdown), 'sha256': _sha256(markdown)},
                },
            }
            manifest = dict(unsigned)
            manifest['manifest_proof'] = self.book.content_digest(_canonical(unsigned))
            _write_atomic(batch_dir / MANIFEST, (_canonical(manifest) + '\n').encode('utf-8'))
            _fsync_dir(batch_dir)
            verified = self._load_manifest(batch_dir)
            if verified['first_seq'] != cursor + 1:
                raise TranscriptBackupError('Prepared transcript batch boundary changed during readback')
            return verified
        except BaseException:
            shutil.rmtree(batch_dir, ignore_errors=True)
            raise

    def artifact_paths(self, batch_id):
        if not isinstance(batch_id, str) or not batch_id.startswith('TB-'):
            raise ValueError('Invalid transcript batch id')
        batch_dir = self.pending / batch_id
        manifest = self._load_manifest(batch_dir)
        return {name: batch_dir / name for name in sorted(manifest['files'])}

    def confirm_upload(self, batch_id, remote_files):
        """Advance the cursor only after transport-level remote readback proof.

        ``remote_files`` must map each artifact name to a dictionary containing
        ``id`` and ``sha256``. The SHA-256 must have been calculated from bytes
        read back from the remote destination, not merely from the upload request.
        """
        batch_dir = self.pending / batch_id
        manifest = self._load_manifest(batch_dir)
        cursor = self._read_cursor()
        if manifest['first_seq'] != cursor + 1:
            raise TranscriptBackupError('Cannot confirm a noncontiguous transcript batch')
        if not isinstance(remote_files, dict) or set(remote_files) != set(manifest['files']):
            raise TranscriptBackupError('Remote transcript artifact set is incomplete')
        clean_remote = {}
        for name, local in manifest['files'].items():
            remote = remote_files[name]
            if not isinstance(remote, dict) or not remote.get('id') or not remote.get('sha256'):
                raise TranscriptBackupError('Remote transcript receipt is incomplete: ' + name)
            if remote['sha256'] != local['sha256']:
                raise TranscriptBackupError('Remote transcript readback hash mismatch: ' + name)
            clean_remote[name] = {'id': str(remote['id']), 'sha256': str(remote['sha256'])}

        receipt = {
            'batch_id': batch_id,
            'first_seq': manifest['first_seq'],
            'last_seq': manifest['last_seq'],
            'remote_files': clean_remote,
            'verified_at': now(),
        }
        receipt['proof'] = self.book.content_digest(_canonical(receipt))
        _append_fsynced(self.receipts_path, (_canonical(receipt) + '\n').encode('utf-8'))

        # Cursor commit occurs only after the durable remote-verification receipt.
        # If the process dies after this point but before the directory move, the
        # next prepare_batch() call reconciles the already-committed pending batch.
        self._write_cursor(manifest['last_seq'])
        destination = self.confirmed / batch_id
        if destination.exists():
            raise TranscriptBackupError('Confirmed transcript batch already exists')
        os.replace(batch_dir, destination)
        _fsync_dir(self.pending)
        _fsync_dir(self.confirmed)
        return receipt
