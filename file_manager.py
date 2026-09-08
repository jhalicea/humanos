"""Scoped scans and journaled, non-overwriting moves; never deletes duplicates.

Move primitives: Darwin renameatx_np(RENAME_EXCL), Linux renameat2(RENAME_NOREPLACE).
Plans and progress live in the existing private Notebook database.
"""
import ctypes
import hashlib
import json
import os
import re
from pathlib import Path
import stat
import sys
import time
import uuid
from notebook import encode, digest

MAX_ENTRIES = 2000
MAX_BYTES = 512 * 1024 * 1024
MAX_SECONDS = 20
SKIP_NAMES = {'HumanOS_Vault', 'backups', 'node_modules', '__pycache__'}


def parts(path):
    if path == '.': return []
    if not isinstance(path, str) or not path or path.startswith('/'):
        raise PermissionError('Use a relative path inside the selected folder')
    values = path.split('/')
    if any(not p or p in ('.', '..') or p.startswith('.') or p in SKIP_NAMES for p in values):
        raise PermissionError('Hidden, protected, or parent paths are outside file-manager scope')
    return values


def rename_exclusive(src_fd, src, dst_fd, dst):
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == 'darwin':
        function, flag = getattr(libc, 'renameatx_np', None), 4
    elif sys.platform.startswith('linux'):
        function, flag = getattr(libc, 'renameat2', None), 1
    else:
        function, flag = None, 0
    if function is None:
        raise RuntimeError('Non-overwriting atomic moves are unavailable on this platform')
    function.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    function.restype = ctypes.c_int
    if function(src_fd, os.fsencode(src), dst_fd, os.fsencode(dst), flag):
        value = ctypes.get_errno()
        raise OSError(value, os.strerror(value), dst)
    os.fsync(src_fd)
    os.fsync(dst_fd)


class FileManager:
    def __init__(self, workspace, notebook):
        self.workspace = Path(workspace).resolve()
        self.book = notebook
        self.identity = None
        self.identity = self._identity()
        with self.book.db:
            self.book.db.execute('CREATE TABLE IF NOT EXISTS file_plans(plan_id TEXT PRIMARY KEY, plan TEXT NOT NULL, state TEXT NOT NULL)')

    def _root(self):
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        fd = os.open(self.workspace.anchor, flags)
        try:
            for name in self.workspace.parts[1:]:
                nxt = os.open(name, flags, dir_fd=fd)
                os.close(fd); fd = nxt
            if self.identity:
                info = os.fstat(fd)
                if (info.st_dev, info.st_ino) != (self.identity['device'], self.identity['inode']):
                    raise PermissionError('Selected folder identity changed; restart and review a new plan')
            return fd
        except BaseException:
            os.close(fd); raise

    def _dir(self, names, create=False):
        fd = self._root()
        try:
            for name in names:
                if create:
                    try:
                        os.mkdir(name, 0o700, dir_fd=fd)
                        os.fsync(fd)
                    except FileExistsError: pass
                nxt = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd); fd = nxt
            return fd
        except BaseException:
            os.close(fd); raise

    def _identity(self):
        fd = self._root()
        try:
            info = os.fstat(fd)
            return {'path': str(self.workspace), 'device': info.st_dev, 'inode': info.st_ino}
        finally: os.close(fd)

    def _read(self, path, budget):
        names = parts(path)
        if not names: raise PermissionError('An ordinary file is required')
        parent = self._dir(names[:-1])
        try: fd = os.open(names[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        finally: os.close(parent)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                raise PermissionError('Symlinks, hardlinks and special files are excluded')
            if before.st_size > budget['bytes']:
                raise ValueError('Scan hash-byte limit reached')
            sha = hashlib.sha256()
            total = 0
            while True:
                if time.monotonic() > budget['until']: raise TimeoutError('Scan time limit reached')
                block = os.read(fd, 65536)
                if not block: break
                total += len(block); budget['bytes'] -= len(block)
                if budget['bytes'] < 0: raise ValueError('Scan hash-byte limit reached')
                sha.update(block)
            after = os.fstat(fd)
            key = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
            if key(before) != key(after) or total != after.st_size:
                raise RuntimeError('File changed during inspection: ' + path)
            return {'size': total, 'sha256': sha.hexdigest(), 'device': after.st_dev, 'inode': after.st_ino,
                    'modified_ns': after.st_mtime_ns}
        finally: os.close(fd)

    def scan(self, path='.'):
        start = parts(path)
        entries, skipped = [], []
        until = time.monotonic() + MAX_SECONDS
        truncated = False
        def visit(names, depth=0):
            nonlocal truncated
            if depth > 20: truncated = True; return
            fd = self._dir(names)
            try:
                # Bound directory enumeration itself, including excluded entries.
                names_here = []
                with os.scandir(fd) as iterator:
                    for entry in iterator:
                        if len(names_here) + len(entries) + len(skipped) >= MAX_ENTRIES or time.monotonic() > until:
                            truncated = True; break
                        names_here.append(entry.name)
                for name in sorted(names_here):
                    if len(entries) + len(skipped) >= MAX_ENTRIES or time.monotonic() > until:
                        truncated = True; return
                    rel = '/'.join(names + [name])
                    if name.startswith('.') or name in SKIP_NAMES:
                        skipped.append({'path': rel, 'reason': 'hidden or protected'}); continue
                    info = os.stat(name, dir_fd=fd, follow_symlinks=False)
                    if stat.S_ISLNK(info.st_mode) or not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode)) or (stat.S_ISREG(info.st_mode) and info.st_nlink != 1):
                        skipped.append({'path': rel, 'reason': 'link or special file'}); continue
                    kind = 'folder' if stat.S_ISDIR(info.st_mode) else 'file'
                    entries.append({'path': rel, 'kind': kind, 'size': info.st_size if kind == 'file' else None})
                    if kind == 'folder': visit(names + [name], depth + 1)
            finally: os.close(fd)
        visit(start)
        return {'folder': path, 'entries': entries, 'skipped': skipped, 'truncated': truncated}

    def duplicates(self, path='.'):
        report = self.scan(path)
        budget = {'bytes': MAX_BYTES, 'until': time.monotonic() + MAX_SECONDS}
        groups, by_size, errors = {}, {}, []
        for item in report['entries']:
            if item['kind'] == 'file': by_size.setdefault(item['size'], []).append(item['path'])
        for size, files in by_size.items():
            if len(files) < 2: continue
            for path in files:
                try:
                    proof = self._read(path, budget)
                    groups.setdefault((proof['size'], proof['sha256']), []).append(path)
                except Exception as error:
                    errors.append({'path': path, 'error': str(error)})
        return {'groups': [{'size': size, 'sha256': sha, 'files': files} for (size, sha), files in groups.items() if len(files) > 1],
                'comparison': 'complete SHA-256 content hashes and byte counts; filenames are not used',
                'files_scanned': sum(len(files) for files in by_size.values()),
                'incomplete': report['truncated'] or bool(errors), 'errors': errors, 'skipped': report['skipped'],
                'action': 'report only; nothing deleted'}

    def _snapshot(self, path, budget=None):
        names = parts(path)
        if not names: raise PermissionError('The workspace root cannot be moved')
        parent = self._dir(names[:-1])
        try: info = os.stat(names[-1], dir_fd=parent, follow_symlinks=False)
        finally: os.close(parent)
        budget = budget or {'bytes': MAX_BYTES, 'until': time.monotonic() + MAX_SECONDS}
        if stat.S_ISREG(info.st_mode):
            return {'kind': 'file', **self._read(path, budget)}
        if not stat.S_ISDIR(info.st_mode): raise PermissionError('Only ordinary files and folders can be moved')
        report = self.scan(path)
        if report['truncated'] or report['skipped']:
            raise PermissionError('Folder contains excluded entries or exceeds the scan limit; select a smaller ordinary folder')
        tree = []
        for item in report['entries']:
            entry = {'path': item['path'][len(path)+1:], 'kind': item['kind']}
            if item['kind'] == 'file': entry.update(self._read(item['path'], budget))
            tree.append(entry)
        return {'kind': 'folder', 'device': info.st_dev, 'inode': info.st_ino, 'tree': tree}

    def _plan_id(self, idempotency_key):
        return ('PLAN-' + hashlib.sha256(idempotency_key.encode()).hexdigest()[:32]
                if idempotency_key else 'PLAN-' + uuid.uuid4().hex)

    def plan_for_key(self, idempotency_key):
        if not idempotency_key:
            return None
        plan_id = self._plan_id(idempotency_key)
        row = self.book.db.execute('SELECT 1 FROM file_plans WHERE plan_id=?', (plan_id,)).fetchone()
        return self.get_plan(plan_id) if row else None

    def _new_plan(self, moves, idempotency_key=None, tx=None, metadata=None):
        if len(moves) > 100: raise ValueError('Plan exceeds 100 moves; select a smaller folder')
        plan_id = self._plan_id(idempotency_key)
        plan = {'plan_id': plan_id, 'workspace': self._identity(), 'moves': moves}
        if metadata: plan['metadata'] = metadata
        state = {'status': 'PREVIEW', 'completed': [], 'undone': [], 'inflight': None}
        with self.book.db:
            prior = self.book.db.execute('SELECT plan FROM file_plans WHERE plan_id=?', (plan_id,)).fetchone()
            if prior:
                if prior['plan'] != encode(plan):
                    raise RuntimeError('Idempotent plan differs from preserved evidence')
            else:
                self.book.db.execute('INSERT INTO file_plans VALUES(?,?,?)', (plan_id, encode(plan), encode(state)))
                self.book._append_event(tx, 'FILE_PLAN_CREATED', {'plan': plan, 'sha256': digest(encode(plan))})
        return self.get_plan(plan_id)

    def _load(self, plan_id):
        if not isinstance(plan_id, str) or not re.fullmatch(r'PLAN-[0-9a-f]{32}', plan_id):
            raise ValueError('Invalid plan ID; copy the ID from a preview')
        row = self.book.db.execute('SELECT plan,state FROM file_plans WHERE plan_id=?', (plan_id,)).fetchone()
        if not row: raise ValueError('Unknown file plan')
        plan, state = json.loads(row[0]), json.loads(row[1])
        if plan['workspace'] != self._identity(): raise PermissionError('Plan belongs to a different workspace identity')
        event = self.book.db.execute("SELECT payload FROM events WHERE kind='FILE_PLAN_CREATED' AND payload LIKE ?", ('%'+plan_id+'%',)).fetchone()
        if not event or json.loads(event[0])['sha256'] != digest(encode(plan)):
            raise RuntimeError('Saved plan differs from its audit evidence')
        events = self.book.db.execute("SELECT payload FROM events WHERE kind LIKE 'FILE_%' AND payload LIKE ? ORDER BY seq DESC", ('%'+plan_id+'%',))
        for event in events:
            payload = json.loads(event[0])
            if payload.get('plan_id') == plan_id and 'state' in payload:
                if payload['state'] != state:
                    raise RuntimeError('Saved plan progress differs from its audit evidence')
                break
        else:
            if state != {'status': 'PREVIEW', 'completed': [], 'undone': [], 'inflight': None}:
                raise RuntimeError('Saved plan progress has no audit evidence')
        return plan, state

    def get_plan(self, plan_id):
        plan, state = self._load(plan_id)
        return {**plan, **state}

    def pending(self):
        """Startup/status inspection is read-only; no move is ever replayed here."""
        result = []
        for row in self.book.db.execute('SELECT plan_id,plan,state FROM file_plans'):
            plan, state = json.loads(row['plan']), json.loads(row['state'])
            if state['status'] in ('APPLYING', 'UNDOING', 'NEEDS_RECONCILIATION'):
                result.append({'plan_id': row['plan_id'], 'workspace': plan['workspace']['path'],
                               'status': state['status'], 'error': state.get('error'),
                               'completed_moves': len(state['completed']), 'undone_moves': len(state['undone'])})
        return result

    def plan_move(self, source, destination, idempotency_key=None, tx=None):
        existing = self.plan_for_key(idempotency_key)
        if existing: return existing
        parts(source); parts(destination)
        if source == destination or destination.startswith(source + '/') or destination == '.':
            raise ValueError('Destination must be a different path outside the source folder')
        proof = self._snapshot(source)
        return self._new_plan([{'source': source, 'destination': destination, 'proof': proof}], idempotency_key, tx)

    def plan_organize(self, path='.', idempotency_key=None, tx=None):
        existing = self.plan_for_key(idempotency_key)
        if existing: return existing
        prefix = parts(path)
        report = self.scan(path)
        if report['truncated']: raise ValueError('Scan is incomplete; choose a smaller folder')
        categories = {'Images': {'png','jpg','jpeg','gif','webp','heic','svg'}, 'Documents': {'txt','md','pdf','doc','docx','rtf','odt'},
                      'Spreadsheets': {'csv','xlsx','xls','ods'}, 'Audio': {'mp3','wav','m4a','flac'},
                      'Video': {'mp4','mov','mkv'}, 'Archives': {'zip','gz','tar','7z'}, 'Code': {'py','js','ts','html','css','json'}}
        moves = []
        budget = {'bytes': MAX_BYTES, 'until': time.monotonic() + MAX_SECONDS}
        for item in report['entries']:
            if item['kind'] != 'file' or len(parts(item['path'])) != len(prefix)+1: continue
            extension = Path(item['path']).suffix.lower().lstrip('.')
            category = next((name for name, types in categories.items() if extension in types), 'Other')
            destination = '/'.join(prefix + [category, Path(item['path']).name])
            if len(moves) >= 100: raise ValueError('Plan exceeds 100 moves; select a smaller folder')
            moves.append({'source': item['path'], 'destination': destination, 'proof': self._snapshot(item['path'], budget)})
        return self._new_plan(moves, idempotency_key, tx)

    def _save(self, plan, state, event):
        with self.book.db:
            self.book.db.execute('UPDATE file_plans SET state=? WHERE plan_id=?', (encode(state), plan['plan_id']))
            self.book._append_event(None, event, {'plan_id': plan['plan_id'], 'state': state})

    def _matches(self, path, proof, budget=None):
        try: return self._snapshot(path, budget) == proof
        except FileNotFoundError: return False

    def _exists(self, path):
        names = parts(path)
        try:
            fd = self._dir(names[:-1])
            try: os.stat(names[-1], dir_fd=fd, follow_symlinks=False); return True
            finally: os.close(fd)
        except FileNotFoundError: return False

    def _move(self, source, destination, proof):
        left, right = parts(source), parts(destination)
        src = self._dir(left[:-1])
        try:
            dst = self._dir(right[:-1], create=True)
            try:
                # Recheck the pinned parent just before the OS rename. A process
                # concurrently editing this tree is outside an atomic multi-file
                # transaction; post-verification preserves uncertain outcomes.
                info = os.stat(left[-1], dir_fd=src, follow_symlinks=False)
                if (info.st_dev, info.st_ino) != (proof['device'], proof['inode']):
                    raise RuntimeError('Source identity changed before move')
                if proof['kind'] == 'file' and (info.st_size, info.st_mtime_ns, info.st_nlink) != (proof['size'], proof['modified_ns'], 1):
                    raise RuntimeError('Source changed before move')
                rename_exclusive(src, left[-1], dst, right[-1])
            finally: os.close(dst)
        finally: os.close(src)

    def _run(self, plan_id, undo, authorized):
        if authorized is not True: raise PermissionError('Exact plan approval is required')
        plan, state = self._load(plan_id)
        budget = {'bytes': MAX_BYTES, 'until': time.monotonic() + MAX_SECONDS}
        # Resolve a durable in-flight marker before selecting apply/undo steps.
        # This also lets undo recover an apply interrupted after its rename.
        marker = state['inflight']
        if marker:
            item = plan['moves'][marker['index']]
            source, destination = (item['destination'], item['source']) if marker['undo'] else (item['source'], item['destination'])
            if not self._exists(source) and self._matches(destination, item['proof'], budget):
                completed = state['undone'] if marker['undo'] else state['completed']
                if marker['index'] not in completed: completed.append(marker['index'])
            elif not self._matches(source, item['proof'], budget):
                raise RuntimeError('Interrupted move has an uncertain result; inspect both paths before continuing')
            # Matching source proves rename did not complete; do not overwrite a
            # destination another program may have created during interruption.
            state['inflight'] = None
            self._save(plan, state, 'FILE_MOVE_RECONCILED')
        done = state['undone'] if undo else state['completed']
        if not undo and state['status'] == 'UNDONE': raise ValueError('Undone plans cannot be reapplied; make a new preview')
        indices = list(reversed(state['completed'])) if undo else list(range(len(plan['moves'])))
        try:
            for index in indices:
                if index in done: continue
                item = plan['moves'][index]
                source, destination = (item['destination'], item['source']) if undo else (item['source'], item['destination'])
                marker = {'index': index, 'undo': undo}
                if time.monotonic() > budget['until']: raise TimeoutError('File-plan time limit reached; progress saved')
                if not self._matches(source, item['proof'], budget): raise RuntimeError('Source changed since preview: ' + source)
                if self._exists(destination): raise FileExistsError('Destination already exists: ' + destination)
                state.update(status='UNDOING' if undo else 'APPLYING', inflight=marker)
                self._save(plan, state, 'FILE_MOVE_STARTED')
                self._move(source, destination, item['proof'])
                if not self._matches(destination, item['proof'], budget): raise RuntimeError('Moved entry differs from the approved snapshot; inspect plan')
                done.append(index); state['inflight'] = None
                self._save(plan, state, 'FILE_MOVE_FINISHED')
            state['status'] = 'UNDONE' if undo else 'APPLIED'
            state.pop('error', None)
            self._save(plan, state, 'FILE_PLAN_FINISHED')
            return self.get_plan(plan_id)
        except Exception as error:
            state.update(status='NEEDS_RECONCILIATION', error=str(error))
            self._save(plan, state, 'FILE_PLAN_RECOVERY_REQUIRED')
            raise

    def apply(self, plan_id, authorized=False): return self._run(plan_id, False, authorized)
    def undo(self, plan_id, authorized=False): return self._run(plan_id, True, authorized)
