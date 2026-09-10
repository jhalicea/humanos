"""Durable delegated-work controller for the local HumanOS runtime.

Work items are owner-bound coordination records that can continue across HumanOS
sessions. They do not grant new filesystem or model authority: each execution turn
still passes through the normal HumanOS permission scope and tool gateway.
"""
import re
import uuid
from notebook import now


STATUSES = frozenset({'RUNNING', 'REVIEW', 'BLOCKED', 'DONE', 'CANCELLED'})
ACTIVE_STATUSES = frozenset({'RUNNING', 'REVIEW', 'BLOCKED'})


def _normalized(text):
    return re.sub(r'\s+', ' ', (text or '').strip())


def parse_work_command(text):
    """Parse explicit human-readable work-control language.

    Ordinary conversation falls through to Mirror. This avoids treating every
    chat message as a durable job while still letting the human delegate naturally.
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


class WorkContextModel:
    """Model wrapper that injects one bounded, host-verified work briefing.

    The wrapper changes context only. It cannot add permissions or bypass the
    normal HumanOS executor/authorization path.
    """

    def __init__(self, model, briefing):
        self.model = model
        self.name = model.name
        self.briefing = briefing

    def invoke(self, messages, timeout):
        messages = [dict(item) for item in messages]
        if not messages or messages[0].get('role') != 'system':
            raise RuntimeError('Delegated work requires the normal HumanOS system prompt')
        messages[0]['content'] += (
            '\n\nDELEGATED WORK CONTRACT (host-verified context, not extra authority):\n' + self.briefing +
            '\nPursue the stated goal across the available tools. Keep going while useful work can be done. '
            'Do not claim a step succeeded without a tool observation when a tool is required. '
            'If blocked by missing human information, approval, or an unavailable capability, say exactly what is blocking the work. '
            'Do not invent permissions or widen the selected workspace.')
        return self.model.invoke(messages, timeout)


class WorkBoard:
    """Persistent owner-bound job board backed by the authoritative Notebook DB."""

    def __init__(self, book):
        self.book = book
        with self.book.db:
            self.book.db.executescript('''
              CREATE TABLE IF NOT EXISTS work_items(
                work_id TEXT PRIMARY KEY,
                owner TEXT NOT NULL,
                origin_hcid TEXT NOT NULL,
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
                hcid TEXT NOT NULL,
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

    def _assert_owner(self, work_id, owner):
        row = self._row(work_id)
        if not row or row['owner'] != owner:
            raise PermissionError('That work item is not available to this HumanOS owner')
        if row['status'] not in STATUSES or not self.book.digest_matches(row['goal_digest'], row['goal']):
            raise RuntimeError('Delegated work record failed integrity validation')
        return row

    def _state_event(self, work_id, status, current_tx, turns):
        return {'work_id': work_id, 'status': status, 'current_tx': current_tx, 'turns': turns}

    def create(self, owner, hcid, goal, tx, exact_input):
        if not isinstance(goal, str) or not goal.strip() or len(goal.encode('utf-8')) > 16000:
            raise ValueError('Delegated work goal must be nonempty and at most 16 KiB')
        work_id = 'WORK-' + uuid.uuid4().hex[:12].upper()
        stamp = now()
        goal = goal.strip()
        with self.book.db:
            self.book.db.execute('INSERT INTO work_items VALUES(?,?,?,?,?,?,?,?,?,?)',
                (work_id, owner, hcid, goal, self.book.content_digest(goal), 'RUNNING', tx, 1, stamp, stamp))
            self.book.db.execute('INSERT INTO work_turns VALUES(?,?,?,?,?,?,?,?)',
                (work_id, 1, hcid, tx, self.book.content_digest(exact_input), None, None, stamp))
            self.book._append_event(tx, 'WORK_CREATED', {
                'work_id': work_id, 'goal_digest': self.book.content_digest(goal),
                'status': 'RUNNING', 'turns': 1})
        return self._row(work_id)

    def begin_turn(self, work_id, owner, hcid, tx, exact_input):
        row = self._assert_owner(work_id, owner)
        if row['status'] == 'CANCELLED':
            raise ValueError('Cancelled work must be started as a new work item')
        ordinal = row['turns'] + 1
        stamp = now()
        with self.book.db:
            self.book.db.execute('INSERT INTO work_turns VALUES(?,?,?,?,?,?,?,?)',
                (work_id, ordinal, hcid, tx, self.book.content_digest(exact_input), None, None, stamp))
            self.book.db.execute("UPDATE work_items SET status='RUNNING',current_tx=?,turns=?,updated=? WHERE work_id=?",
                                 (tx, ordinal, stamp, work_id))
            self.book._append_event(tx, 'WORK_STATE', self._state_event(work_id, 'RUNNING', tx, ordinal))
        return self._row(work_id)

    def finish_turn(self, work_id, owner, tx, response, failed=False):
        row = self._assert_owner(work_id, owner)
        turn = self.book.db.execute('SELECT * FROM work_turns WHERE work_id=? AND tx=?', (work_id, tx)).fetchone()
        if not turn:
            raise RuntimeError('Delegated work turn is missing')
        status = 'BLOCKED' if failed else 'REVIEW'
        outcome = 'FAILED' if failed else 'TURN_COMPLETE'
        digest = self.book.content_digest(response)
        if turn['response_digest'] is not None:
            if (not self.book.digest_matches(turn['response_digest'], response) or turn['outcome'] != outcome):
                raise RuntimeError('Delegated work turn result differs from preserved result')
            return row
        stamp = now()
        with self.book.db:
            self.book.db.execute('UPDATE work_turns SET response_digest=?,outcome=? WHERE work_id=? AND tx=?',
                                 (digest, outcome, work_id, tx))
            self.book.db.execute('UPDATE work_items SET status=?,updated=? WHERE work_id=?',
                                 (status, stamp, work_id))
            self.book._append_event(tx, 'WORK_STATE', self._state_event(work_id, status, tx, row['turns']))
        return self._row(work_id)

    def set_status(self, work_id, owner, status, tx=None):
        if status not in ('DONE', 'CANCELLED'):
            raise ValueError('Unsupported owner work transition')
        row = self._assert_owner(work_id, owner)
        if row['status'] == status:
            return row
        stamp = now()
        with self.book.db:
            self.book.db.execute('UPDATE work_items SET status=?,updated=? WHERE work_id=?',
                                 (status, stamp, work_id))
            self.book._append_event(tx, 'WORK_STATE', self._state_event(work_id, status, row['current_tx'], row['turns']))
        return self._row(work_id)

    def get(self, work_id, owner):
        return self._assert_owner(work_id, owner)

    def by_tx(self, tx):
        row = self.book.db.execute('''SELECT work_items.* FROM work_turns
            JOIN work_items USING(work_id) WHERE work_turns.tx=?''', (tx,)).fetchone()
        if not row:
            return None
        result = dict(row)
        if result['status'] not in STATUSES or not self.book.digest_matches(result['goal_digest'], result['goal']):
            raise RuntimeError('Delegated work record failed integrity validation')
        return result

    def list(self, owner, active_only=False, limit=20):
        if active_only:
            placeholders = ','.join('?' for _ in ACTIVE_STATUSES)
            rows = self.book.db.execute(
                f'SELECT * FROM work_items WHERE owner=? AND status IN ({placeholders}) ORDER BY updated DESC LIMIT ?',
                (owner, *sorted(ACTIVE_STATUSES), limit)).fetchall()
        else:
            rows = self.book.db.execute(
                'SELECT * FROM work_items WHERE owner=? ORDER BY updated DESC LIMIT ?', (owner, limit)).fetchall()
        result = []
        for item in rows:
            row = dict(item)
            self._assert_owner(row['work_id'], owner)
            result.append(row)
        return result

    def choose_candidates(self, owner):
        return [item['work_id'] for item in self.list(owner, active_only=True)]

    def briefing(self, work_id, owner, budget=6000):
        item = self._assert_owner(work_id, owner)
        lines = [
            'Work ID: ' + item['work_id'],
            'Original goal: ' + item['goal'],
            'Current work-board status: ' + item['status'],
            'The work item does not grant permissions. Current-turn HumanOS scope still controls every tool call.',
        ]
        rows = self.book.db.execute('''SELECT work_turns.ordinal,work_turns.tx FROM work_turns
            WHERE work_id=? ORDER BY ordinal DESC LIMIT 4''', (work_id,)).fetchall()
        excerpts = []
        for row in reversed(rows):
            messages = self.book.db.execute('SELECT role,text FROM transcript WHERE tx=? ORDER BY ordinal',
                                            (row['tx'],)).fetchall()
            block = ['Work turn ' + str(row['ordinal']) + ':']
            for message in messages:
                text = message['text']
                if len(text) > 1200:
                    text = text[:1200] + ' [excerpt truncated]'
                block.append(message['role'] + ': ' + text)
            excerpts.append('\n'.join(block))
        history = '\n'.join(excerpts)
        if len(history.encode('utf-8')) > budget:
            raw = history.encode('utf-8')[-budget:]
            history = raw.decode('utf-8', errors='ignore')
            history = '[older work context omitted]\n' + history
        if history:
            lines.append('Recent work evidence:\n' + history)
        return '\n'.join(lines)

    @staticmethod
    def format_item(item):
        return (item['work_id'] + '  ' + item['status'] + '\n'
                'Goal: ' + item['goal'] + '\n'
                'Turns: ' + str(item['turns']) +
                ('\nCurrent transaction: ' + item['current_tx'] if item.get('current_tx') else ''))

    def format_list(self, owner):
        items = self.list(owner)
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
