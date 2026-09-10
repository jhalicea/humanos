"""Durable delegated-work controller for the local HumanOS runtime.

Work items are owner/session-bound coordination records. They do not grant new
filesystem or model authority: each execution turn still passes through the normal
HumanOS permission scope and tool gateway.
"""
import re
import uuid
from notebook import now


STATUSES = frozenset({'RUNNING', 'REVIEW', 'BLOCKED', 'DONE', 'CANCELLED'})
ACTIVE_STATUSES = frozenset({'RUNNING', 'REVIEW', 'BLOCKED'})


def _normalized(text):
    return re.sub(r'\s+', ' ', (text or '').strip())


def parse_work_command(text):
    """Parse only explicit, human-readable work-control language.

    Ordinary conversation falls through to Mirror. This deliberately avoids a
    broad semantic guess until the model-neutral intent router exists.
    """
    raw = _normalized(text)
    lowered = raw.casefold().rstrip('?!.,')
    if not raw:
        return None

    if lowered in ('/jobs', '/work', 'show work', 'show my work', 'list work',
                   'list my work', 'what are you working on', 'what work do you have'):
        return {'action': 'list'}

    m = re.fullmatch(r'(?:/job|/work status|work status)\s+(WORK-[A-Za-z0-9]+)', raw, re.I)
    if m:
        return {'action': 'status', 'work_id': m.group(1).upper()}

    m = re.fullmatch(r'(?:/cancel|cancel work|cancel job)\s+(WORK-[A-Za-z0-9]+)', raw, re.I)
    if m:
        return {'action': 'cancel', 'work_id': m.group(1).upper()}
    if lowered in ('cancel that work', 'cancel that job', 'cancel it'):
        return {'action': 'cancel', 'work_id': None}

    m = re.fullmatch(r'(?:/done|finish work|finish job|mark work done)\s+(WORK-[A-Za-z0-9]+)', raw, re.I)
    if m:
        return {'action': 'done', 'work_id': m.group(1).upper()}
    if lowered in ('that work is done', 'that job is done', 'mark that work done', 'mark it done'):
        return {'action': 'done', 'work_id': None}

    m = re.fullmatch(r'/continue(?:\s+(WORK-[A-Za-z0-9]+))?(?:\s+(.+))?', raw, re.I)
    if m:
        return {'action': 'continue', 'work_id': m.group(1).upper() if m.group(1) else None,
                'instruction': (m.group(2) or '').strip()}
    m = re.fullmatch(r'continue\s+(WORK-[A-Za-z0-9]+)(?:\s+(.+))?', raw, re.I)
    if m:
        return {'action': 'continue', 'work_id': m.group(1).upper(),
                'instruction': (m.group(2) or '').strip()}
    if lowered in ('continue that work', 'continue that job', 'keep working on it', 'continue the work'):
        return {'action': 'continue', 'work_id': None, 'instruction': ''}

    start_patterns = (
        r'/work\s+(.+)',
        r'work on\s+(.+)',
        r'start work(?: on)?[: ]+(.+)',
        r'start a job(?: on)?[: ]+(.+)',
        r'task:\s*(.+)',
        r'i want you to work on\s+(.+)',
        r'i need you to work on\s+(.+)',
    )
    for pattern in start_patterns:
        match = re.fullmatch(pattern, raw, re.I)
        if match and match.group(1).strip():
            return {'action': 'start', 'goal': match.group(1).strip()}
    return None


class WorkBoard:
    """Small persistent job board backed by the authoritative Notebook SQLite DB."""

    def __init__(self, book):
        self.book = book
        with self.book.db:
            self.book.db.executescript('''
              CREATE TABLE IF NOT EXISTS work_items(
                work_id TEXT PRIMARY KEY,
                hcid TEXT NOT NULL,
                goal TEXT NOT NULL,
                goal_digest TEXT NOT NULL,
                status TEXT NOT NULL,
                current_tx TEXT,
                turns INTEGER NOT NULL DEFAULT 0,
                created TEXT NOT NULL,
                updated TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS work_turns(
                work_id TEXT NOT NULL,
                ordinal INTEGER NOT NULL,
                tx TEXT NOT NULL UNIQUE,
                input_digest TEXT NOT NULL,
                response_digest TEXT,
                outcome TEXT,
                created TEXT NOT NULL,
                PRIMARY KEY(work_id, ordinal));
            ''')

    def _row(self, work_id):
        row = self.book.db.execute('SELECT * FROM work_items WHERE work_id=?', (work_id,)).fetchone()
        return dict(row) if row else None

    def _assert_owner(self, work_id, hcid):
        row = self._row(work_id)
        if not row or row['hcid'] != hcid:
            raise PermissionError('That work item is not available in this HumanOS session')
        if row['status'] not in STATUSES or not self.book.digest_matches(row['goal_digest'], row['goal']):
            raise RuntimeError('Delegated work record failed integrity validation')
        return row

    def _state_event(self, work_id, status, current_tx, turns):
        return {'work_id': work_id, 'status': status, 'current_tx': current_tx, 'turns': turns}

    def create(self, hcid, goal, tx, exact_input):
        if not isinstance(goal, str) or not goal.strip() or len(goal.encode('utf-8')) > 16000:
            raise ValueError('Delegated work goal must be nonempty and at most 16 KiB')
        work_id = 'WORK-' + uuid.uuid4().hex[:12].upper()
        stamp = now()
        goal = goal.strip()
        with self.book.db:
            self.book.db.execute('INSERT INTO work_items VALUES(?,?,?,?,?,?,?,?,?)',
                (work_id, hcid, goal, self.book.content_digest(goal), 'RUNNING', tx, 1, stamp, stamp))
            self.book.db.execute('INSERT INTO work_turns VALUES(?,?,?,?,?,?,?)',
                (work_id, 1, tx, self.book.content_digest(exact_input), None, None, stamp))
            self.book._append_event(tx, 'WORK_CREATED', {
                'work_id': work_id, 'goal_digest': self.book.content_digest(goal),
                'status': 'RUNNING', 'turns': 1})
        return self._row(work_id)

    def begin_turn(self, work_id, hcid, tx, exact_input):
        row = self._assert_owner(work_id, hcid)
        if row['status'] == 'CANCELLED':
            raise ValueError('Cancelled work must be started as a new work item')
        ordinal = row['turns'] + 1
        stamp = now()
        with self.book.db:
            self.book.db.execute('INSERT INTO work_turns VALUES(?,?,?,?,?,?,?)',
                (work_id, ordinal, tx, self.book.content_digest(exact_input), None, None, stamp))
            self.book.db.execute("UPDATE work_items SET status='RUNNING',current_tx=?,turns=?,updated=? WHERE work_id=?",
                                 (tx, ordinal, stamp, work_id))
            self.book._append_event(tx, 'WORK_STATE', self._state_event(work_id, 'RUNNING', tx, ordinal))
        return self._row(work_id)

    def finish_turn(self, work_id, hcid, tx, response, failed=False):
        row = self._assert_owner(work_id, hcid)
        turn = self.book.db.execute('SELECT * FROM work_turns WHERE work_id=? AND tx=?', (work_id, tx)).fetchone()
        if not turn:
            raise RuntimeError('Delegated work turn is missing')
        status = 'BLOCKED' if failed else 'REVIEW'
        outcome = 'FAILED' if failed else 'TURN_COMPLETE'
        stamp = now()
        digest = self.book.content_digest(response)
        with self.book.db:
            self.book.db.execute('UPDATE work_turns SET response_digest=?,outcome=? WHERE work_id=? AND tx=?',
                                 (digest, outcome, work_id, tx))
            self.book.db.execute('UPDATE work_items SET status=?,updated=? WHERE work_id=?',
                                 (status, stamp, work_id))
            self.book._append_event(tx, 'WORK_STATE', self._state_event(work_id, status, tx, row['turns']))
        return self._row(work_id)

    def set_status(self, work_id, hcid, status, tx=None):
        if status not in ('DONE', 'CANCELLED'):
            raise ValueError('Unsupported owner work transition')
        row = self._assert_owner(work_id, hcid)
        if row['status'] == status:
            return row
        stamp = now()
        with self.book.db:
            self.book.db.execute('UPDATE work_items SET status=?,updated=? WHERE work_id=?',
                                 (status, stamp, work_id))
            self.book._append_event(tx, 'WORK_STATE', self._state_event(work_id, status, row['current_tx'], row['turns']))
        return self._row(work_id)

    def get(self, work_id, hcid):
        return self._assert_owner(work_id, hcid)

    def list(self, hcid, active_only=False, limit=20):
        if active_only:
            placeholders = ','.join('?' for _ in ACTIVE_STATUSES)
            rows = self.book.db.execute(
                f'SELECT * FROM work_items WHERE hcid=? AND status IN ({placeholders}) ORDER BY updated DESC LIMIT ?',
                (hcid, *sorted(ACTIVE_STATUSES), limit)).fetchall()
        else:
            rows = self.book.db.execute(
                'SELECT * FROM work_items WHERE hcid=? ORDER BY updated DESC LIMIT ?', (hcid, limit)).fetchall()
        result = []
        for item in rows:
            row = dict(item)
            self._assert_owner(row['work_id'], hcid)
            result.append(row)
        return result

    def choose_candidates(self, hcid):
        return [item['work_id'] for item in self.list(hcid, active_only=True)]

    @staticmethod
    def format_item(item):
        return (item['work_id'] + '  ' + item['status'] + '\n'
                'Goal: ' + item['goal'] + '\n'
                'Turns: ' + str(item['turns']) +
                ('\nCurrent transaction: ' + item['current_tx'] if item.get('current_tx') else ''))

    def format_list(self, hcid):
        items = self.list(hcid)
        if not items:
            return 'No delegated work items yet. Give me work with: work on <goal>'
        lines = ['Delegated work:']
        for item in items:
            goal = item['goal'].replace('\n', ' ')
            if len(goal) > 90:
                goal = goal[:87] + '...'
            lines.append('  ' + item['work_id'] + '  ' + item['status'] + '  — ' + goal)
        lines.append('Use /job WORK-ID, /continue WORK-ID, /done WORK-ID, or /cancel WORK-ID.')
        return '\n'.join(lines)
