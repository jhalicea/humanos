"""Dependency-free terminal status view for HumanOS subagents.

The runtime writes a small, privacy-light status snapshot to
``<control_state>/subagents.json``.  It intentionally excludes prompts, model
responses, authorization evidence, tokens, and task contents so an operator can
watch orchestration without duplicating sensitive payloads.
"""
import argparse
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1
FINAL_OVERALL = frozenset({'COMPLETE', 'ROUND_LIMIT', 'ERROR'})
AGENT_STATES = frozenset({'queued', 'working', 'done', 'stopped', 'error'})


def _now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def _clone(value):
    return json.loads(json.dumps(value, ensure_ascii=False))


class SubagentStatusStore:
    """Atomic, content-light status snapshot for one swarm run."""

    def __init__(self, state_dir, run_id, manifests, roles, max_rounds, on_change=None):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.state_dir / 'subagents.json'
        self.on_change = on_change
        created = _now()
        self.state = {
            'schema_version': SCHEMA_VERSION,
            'run_id': str(run_id),
            'overall_status': 'READY',
            'round': 0,
            'max_rounds': int(max_rounds),
            'created_at': created,
            'updated_at': created,
            'agents': [
                {
                    'agent_id': m['agent_id'],
                    'role': roles[m['agent_id']],
                    'model': m.get('model', 'UNKNOWN'),
                    'status': 'queued',
                    'round': 0,
                    'detail': 'waiting',
                }
                for m in manifests
            ],
        }
        self._publish()

    def _publish(self):
        self.state['updated_at'] = _now()
        payload = json.dumps(self.state, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n'
        fd, tmp_name = tempfile.mkstemp(prefix='.subagents.', suffix='.tmp', dir=self.state_dir)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.path)
            try:
                directory_fd = os.open(self.state_dir, os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            except OSError:
                # Directory fsync is not supported uniformly across platforms.
                pass
        finally:
            try:
                os.unlink(tmp_name)
            except FileNotFoundError:
                pass
        if self.on_change is not None:
            self.on_change(_clone(self.state))

    def set_overall(self, status, round_no=None):
        self.state['overall_status'] = str(status)
        if round_no is not None:
            self.state['round'] = int(round_no)
        self._publish()

    def mark(self, agent_id, status, round_no=None, detail=None):
        if status not in AGENT_STATES:
            raise ValueError('Unknown subagent status: ' + str(status))
        for agent in self.state['agents']:
            if agent['agent_id'] == agent_id:
                agent['status'] = status
                if round_no is not None:
                    agent['round'] = int(round_no)
                    self.state['round'] = max(self.state['round'], int(round_no))
                if detail is not None:
                    agent['detail'] = str(detail)
                self._publish()
                return
        raise KeyError('Unknown subagent: ' + str(agent_id))

    def stop_incomplete(self, round_no, detail='round limit'):
        changed = False
        for agent in self.state['agents']:
            if agent['status'] not in ('done', 'error'):
                agent['status'] = 'stopped'
                agent['round'] = int(round_no)
                agent['detail'] = detail
                changed = True
        self.state['round'] = int(round_no)
        if changed:
            self._publish()

    def snapshot(self):
        return _clone(self.state)


def format_subagents(snapshot):
    """Return a stable text rendering suitable for terminals and tests."""
    overall = snapshot.get('overall_status', 'UNKNOWN')
    round_no = snapshot.get('round', 0)
    max_rounds = snapshot.get('max_rounds', '?')
    agents = list(snapshot.get('agents', []))
    lines = [f'HumanOS Subagents — {overall} — round {round_no}/{max_rounds}', '']

    groups = [
        ('Active', ('working',), 'No active subagents'),
        ('Done', ('done',), None),
        ('Queued', ('queued',), None),
        ('Stopped', ('stopped',), None),
        ('Errors', ('error',), None),
    ]
    symbols = {'working': '●', 'done': '✓', 'queued': '○', 'stopped': '■', 'error': '!'}
    for title, states, empty in groups:
        selected = [agent for agent in agents if agent.get('status') in states]
        if not selected and empty is None:
            continue
        suffix = f' · {len(selected)}' if title != 'Active' else ''
        lines.append(title + suffix)
        if not selected:
            lines.append('  ' + empty)
        else:
            for agent in selected:
                status = agent.get('status', 'unknown')
                role = agent.get('role', 'unknown')
                model = agent.get('model', 'UNKNOWN')
                detail = agent.get('detail', '')
                agent_round = agent.get('round', 0)
                tail = f'{role} · {model} · {detail}'
                if agent_round:
                    tail += f' · round {agent_round}'
                lines.append(f"  {symbols.get(status, '?')} {agent.get('agent_id', 'unknown')}  {tail}")
        lines.append('')
    return '\n'.join(lines).rstrip() + '\n'


class TerminalSubagentView:
    """Render status updates in place on a TTY; emit only the final view otherwise."""

    def __init__(self, stream=None):
        self.stream = stream or sys.stderr
        self.tty = bool(getattr(self.stream, 'isatty', lambda: False)())

    def __call__(self, snapshot):
        if not self.tty and snapshot.get('overall_status') not in FINAL_OVERALL:
            return
        if self.tty:
            self.stream.write('\x1b[2J\x1b[H')
        self.stream.write(format_subagents(snapshot))
        self.stream.flush()


def load_snapshot(path):
    value = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(value, dict) or value.get('schema_version') != SCHEMA_VERSION:
        raise ValueError('Unsupported subagent status snapshot')
    return value


def watch(path, stream=None, interval=0.25):
    stream = stream or sys.stdout
    path = Path(path)
    renderer = TerminalSubagentView(stream)
    last = None
    while True:
        try:
            stamp = path.stat().st_mtime_ns
        except FileNotFoundError:
            time.sleep(interval)
            continue
        if stamp != last:
            snapshot = load_snapshot(path)
            renderer(snapshot)
            last = stamp
            if snapshot.get('overall_status') in FINAL_OVERALL:
                return 0
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description='HumanOS terminal subagent view')
    parser.add_argument('--state-dir', required=True, help='Swarm control_state directory')
    parser.add_argument('--watch', action='store_true', help='Refresh until the run finishes')
    parser.add_argument('--interval', type=float, default=0.25)
    args = parser.parse_args()
    path = Path(args.state_dir).expanduser().resolve() / 'subagents.json'
    if args.watch:
        if args.interval < 0.05:
            parser.error('--interval must be at least 0.05 seconds')
        try:
            return watch(path, interval=args.interval)
        except KeyboardInterrupt:
            return 130
    if not path.exists():
        print('No subagent state found: ' + str(path), file=sys.stderr)
        return 1
    sys.stdout.write(format_subagents(load_snapshot(path)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
