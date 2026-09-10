"""Persistent Work Executor v3 plan and subtask state machine.

This module is intentionally model-neutral. It turns an already owner-bound work
item into a deterministic execution plan, persists step state, and decides whether
required evidence/deliverables are complete. It never grants tool authority.
"""
import json
import re
from notebook import encode, now


PLAN_VERSION = 1
STEP_STATUSES = frozenset({'TODO', 'WORKING', 'VERIFIED', 'BLOCKED'})
TEXT_EXTENSIONS = ('.txt', '.md', '.json', '.csv', '.py', '.yaml', '.yml', '.toml', '.log')


def _normalized(text):
    return re.sub(r'\s+', ' ', (text or '').strip())


def requested_deliverable(goal, work_id):
    """Return a bounded workspace output path only when the owner asked for one."""
    text = _normalized(goal)
    if not re.search(r'\b(create|write|save|produce|generate|make)\b', text, re.I):
        return None
    if not re.search(r'\b(report|summary|brief|notes?|document|deliverable|recommendations?)\b', text, re.I):
        return None
    explicit = re.search(
        r'\b(?:create|write|save|produce|generate|make)\b[^\n]{0,100}?'
        r'([A-Za-z0-9_-]+(?:/[A-Za-z0-9_.-]+)*\.(?:md|txt))\b', text, re.I)
    if explicit:
        path = explicit.group(1)
        parts = path.split('/')
        if path.startswith('/') or any(part in ('', '.', '..') or part.startswith('.') for part in parts):
            raise PermissionError('Requested work deliverable path is outside the selected workspace')
        return path
    suffix = work_id.removeprefix('WORK-').lower()
    return 'work-report-' + suffix + '.md'


def build_plan(work_id, goal, contract):
    """Build the initial immutable plan for a work item."""
    deliverable = requested_deliverable(goal, work_id)
    kind = contract.get('kind', 'general')
    steps = []

    def add(step_kind, title, depends=(), target=None):
        ordinal = len(steps) + 1
        step = {'step_id': f'STEP-{ordinal:02d}-{step_kind}', 'ordinal': ordinal,
                'kind': step_kind, 'title': title, 'depends_on': list(depends),
                'required': True}
        if target:
            step['target'] = target
        steps.append(step)
        return step['step_id']

    if kind == 'workspace_review':
        a = add('DISCOVER', 'Scan the selected workspace and establish the real file set')
        b = add('INSPECT', 'Inspect the discovered readable text files', (a,))
        c = add('SYNTHESIZE', 'Synthesize findings from verified observations', (b,))
    elif kind == 'file_review':
        a = add('INSPECT', 'Inspect every owner-named file required by the assignment')
        c = add('SYNTHESIZE', 'Synthesize findings from verified observations', (a,))
    elif kind == 'web_research':
        a = add('DISCOVER_WEB', 'Collect current public-web evidence')
        b = add('VERIFY_SOURCES', 'Verify and reconcile collected sources', (a,))
        c = add('SYNTHESIZE', 'Synthesize the verified research', (b,))
    else:
        a = add('EXECUTE', 'Perform the delegated assignment within connected capabilities')
        c = add('SYNTHESIZE', 'Produce the work result', (a,))

    previous = c
    if deliverable:
        previous = add('DELIVER', 'Create the requested workspace deliverable', (c,), deliverable)
    add('VERIFY', 'Verify all required work steps before owner completion', (previous,))
    return {'version': PLAN_VERSION, 'work_id': work_id, 'kind': kind,
            'deliverable': deliverable, 'steps': steps}


class WorkExecutor:
    """Durable step controller backed by the authoritative Notebook database."""

    def __init__(self, book):
        self.book = book
        with self.book.db:
            self.book.db.executescript('''
              CREATE TABLE IF NOT EXISTS work_plans(
                work_id TEXT PRIMARY KEY,
                owner TEXT NOT NULL,
                plan TEXT NOT NULL,
                plan_digest TEXT NOT NULL,
                created TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS work_steps(
                work_id TEXT NOT NULL,
                step_id TEXT NOT NULL,
                ordinal INTEGER NOT NULL,
                kind TEXT NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                depends_on TEXT NOT NULL,
                required INTEGER NOT NULL,
                target TEXT,
                evidence_digest TEXT,
                updated TEXT NOT NULL,
                PRIMARY KEY(work_id, step_id));
              CREATE TRIGGER IF NOT EXISTS work_plans_no_update BEFORE UPDATE ON work_plans
                BEGIN SELECT RAISE(ABORT, 'immutable work plan'); END;
              CREATE TRIGGER IF NOT EXISTS work_plans_no_delete BEFORE DELETE ON work_plans
                BEGIN SELECT RAISE(ABORT, 'immutable work plan'); END;
            ''')

    def ensure(self, item, contract):
        """Lazily create a v3 plan; existing pre-v3 work migrates without rewriting history."""
        row = self.book.db.execute('SELECT * FROM work_plans WHERE work_id=?', (item['work_id'],)).fetchone()
        if row:
            if row['owner'] != item['owner'] or not self.book.digest_matches(row['plan_digest'], row['plan']):
                raise RuntimeError('Work execution plan failed integrity validation')
            plan = json.loads(row['plan'])
            if plan.get('version') != PLAN_VERSION or plan.get('work_id') != item['work_id']:
                raise RuntimeError('Unsupported or mismatched work execution plan')
            self._validate_step_rows(plan)
            return plan

        plan = build_plan(item['work_id'], item['goal'], contract)
        encoded = encode(plan)
        stamp = now()
        with self.book.db:
            self.book.db.execute('INSERT INTO work_plans VALUES(?,?,?,?,?)',
                                 (item['work_id'], item['owner'], encoded,
                                  self.book.content_digest(encoded), stamp))
            for step in plan['steps']:
                self.book.db.execute('INSERT INTO work_steps VALUES(?,?,?,?,?,?,?,?,?,?,?)',
                    (item['work_id'], step['step_id'], step['ordinal'], step['kind'], step['title'],
                     'TODO', encode(step['depends_on']), 1 if step['required'] else 0,
                     step.get('target'), None, stamp))
            self.book._append_event(item.get('current_tx'), 'WORK_PLAN_CREATED', {
                'work_id': item['work_id'], 'version': PLAN_VERSION,
                'step_count': len(plan['steps']),
                'plan_digest': self.book.content_digest(encoded)})
        return plan

    def _validate_step_rows(self, plan):
        rows = self.book.db.execute(
            'SELECT * FROM work_steps WHERE work_id=? ORDER BY ordinal', (plan['work_id'],)).fetchall()
        if len(rows) != len(plan['steps']):
            raise RuntimeError('Work execution step set differs from immutable plan')
        for row, step in zip(rows, plan['steps']):
            if (row['step_id'] != step['step_id'] or row['ordinal'] != step['ordinal'] or
                    row['kind'] != step['kind'] or row['title'] != step['title'] or
                    json.loads(row['depends_on']) != step['depends_on'] or
                    bool(row['required']) != bool(step['required']) or row['target'] != step.get('target') or
                    row['status'] not in STEP_STATUSES):
                raise RuntimeError('Work execution step failed integrity validation')

    def steps(self, item, contract):
        plan = self.ensure(item, contract)
        self._validate_step_rows(plan)
        return [dict(row) for row in self.book.db.execute(
            'SELECT * FROM work_steps WHERE work_id=? ORDER BY ordinal', (item['work_id'],)).fetchall()]

    @staticmethod
    def _desired_statuses(plan, progress, failed=False, response_present=False):
        statuses = {step['step_id']: 'TODO' for step in plan['steps']}
        kind = plan['kind']
        inspected = set(progress.get('inspected_paths', []))
        discovered = set(progress.get('discovered_paths', []))
        artifacts = {item.get('path') for item in progress.get('artifacts', []) if isinstance(item, dict)}
        scan_complete = bool(progress.get('scan_complete'))
        scan_truncated = bool(progress.get('scan_truncated'))

        by_kind = {step['kind']: step for step in plan['steps']}
        if kind == 'workspace_review':
            discover = by_kind['DISCOVER']['step_id']
            if scan_truncated:
                statuses[discover] = 'BLOCKED'
            elif scan_complete:
                statuses[discover] = 'VERIFIED'
            else:
                statuses[discover] = 'WORKING' if progress.get('tools') else 'TODO'

            inspect = by_kind['INSPECT']['step_id']
            eligible = {p for p in discovered if p.casefold().endswith(TEXT_EXTENSIONS)}
            if statuses[discover] == 'VERIFIED':
                if eligible.issubset(inspected):
                    statuses[inspect] = 'VERIFIED'
                elif inspected:
                    statuses[inspect] = 'WORKING'
                else:
                    statuses[inspect] = 'TODO'
            elif statuses[discover] == 'BLOCKED':
                statuses[inspect] = 'BLOCKED'

            synth = by_kind['SYNTHESIZE']['step_id']
            if statuses[inspect] == 'VERIFIED' and response_present and not failed:
                statuses[synth] = 'VERIFIED'
            elif statuses[inspect] == 'BLOCKED':
                statuses[synth] = 'BLOCKED'

        elif kind == 'file_review':
            inspect = by_kind['INSPECT']['step_id']
            required = set(progress.get('required_paths', []))
            if required and required.issubset(inspected):
                statuses[inspect] = 'VERIFIED'
            elif inspected:
                statuses[inspect] = 'WORKING'
            synth = by_kind['SYNTHESIZE']['step_id']
            if statuses[inspect] == 'VERIFIED' and response_present and not failed:
                statuses[synth] = 'VERIFIED'

        elif kind == 'web_research':
            first = by_kind['DISCOVER_WEB']['step_id']
            if failed:
                statuses[first] = 'BLOCKED'
            elif 'internet_search' in set(progress.get('tools', [])):
                statuses[first] = 'VERIFIED'
            verify_sources = by_kind['VERIFY_SOURCES']['step_id']
            if statuses[first] == 'VERIFIED':
                statuses[verify_sources] = 'VERIFIED' if response_present and not failed else 'WORKING'
            elif statuses[first] == 'BLOCKED':
                statuses[verify_sources] = 'BLOCKED'
            synth = by_kind['SYNTHESIZE']['step_id']
            if statuses[verify_sources] == 'VERIFIED' and response_present and not failed:
                statuses[synth] = 'VERIFIED'

        else:
            execute = by_kind['EXECUTE']['step_id']
            synth = by_kind['SYNTHESIZE']['step_id']
            if failed:
                statuses[execute] = 'BLOCKED'
            elif response_present:
                statuses[execute] = 'VERIFIED'
                statuses[synth] = 'VERIFIED'
            else:
                statuses[execute] = 'WORKING'

        deliver = by_kind.get('DELIVER')
        if deliver:
            synth_status = statuses[by_kind['SYNTHESIZE']['step_id']]
            if deliver.get('target') in artifacts:
                statuses[deliver['step_id']] = 'VERIFIED'
            elif failed and synth_status == 'VERIFIED':
                statuses[deliver['step_id']] = 'BLOCKED'
            elif synth_status == 'VERIFIED':
                statuses[deliver['step_id']] = 'WORKING'

        verify = by_kind['VERIFY']
        deps = verify['depends_on']
        if all(statuses.get(dep) == 'VERIFIED' for dep in deps):
            statuses[verify['step_id']] = 'VERIFIED'
        elif any(statuses.get(dep) == 'BLOCKED' for dep in deps):
            statuses[verify['step_id']] = 'BLOCKED'
        return statuses

    def sync(self, item, contract, progress, failed=False, response_present=False, tx=None):
        plan = self.ensure(item, contract)
        desired = self._desired_statuses(plan, progress, failed=failed, response_present=response_present)
        rows = {row['step_id']: dict(row) for row in self.book.db.execute(
            'SELECT * FROM work_steps WHERE work_id=?', (item['work_id'],)).fetchall()}
        changes = []
        stamp = now()
        with self.book.db:
            for step in plan['steps']:
                old = rows[step['step_id']]['status']
                new = desired[step['step_id']]
                if old == new:
                    continue
                evidence = {'progress_phase': progress.get('phase'),
                            'inspected_count': len(progress.get('inspected_paths', [])),
                            'artifact_count': len(progress.get('artifacts', []))}
                evidence_text = encode(evidence)
                self.book.db.execute(
                    'UPDATE work_steps SET status=?,evidence_digest=?,updated=? WHERE work_id=? AND step_id=?',
                    (new, self.book.content_digest(evidence_text), stamp, item['work_id'], step['step_id']))
                self.book._append_event(tx, 'WORK_STEP_STATE', {
                    'work_id': item['work_id'], 'step_id': step['step_id'],
                    'from': old, 'to': new,
                    'evidence_digest': self.book.content_digest(evidence_text)})
                changes.append((step['step_id'], old, new))
        return changes

    def require_done(self, item, contract, progress):
        self.sync(item, contract, progress, response_present=bool(progress.get('has_response')),
                  failed=False, tx=item.get('current_tx'))
        pending = [row for row in self.steps(item, contract)
                   if row['required'] and row['status'] != 'VERIFIED']
        if pending:
            first = pending[0]
            raise ValueError('Work cannot be marked done yet. Next required step: '
                             + first['step_id'] + ' ' + first['title'] + ' [' + first['status'] + ']')
        return True

    def next_step(self, item, contract):
        for row in self.steps(item, contract):
            if row['required'] and row['status'] != 'VERIFIED':
                return row
        return None

    def format_steps(self, item, contract):
        rows = self.steps(item, contract)
        lines = []
        for row in rows:
            target = ' -> ' + row['target'] if row.get('target') else ''
            lines.append('  ' + row['step_id'] + '  ' + row['status'] + '  ' + row['title'] + target)
        return '\n'.join(lines)
