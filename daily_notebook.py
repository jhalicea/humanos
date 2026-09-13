#!/usr/bin/env python3
"""Project exact local Mirror transcripts into one daily Life Notebook page."""
import argparse
import json
import os
from datetime import date, datetime, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from notebook import Notebook


DEFAULT_TIMEZONE = 'America/New_York'


def _bounds(day, timezone_name):
    zone = ZoneInfo(timezone_name)
    start = datetime.combine(day, time.min, zone)
    end = datetime.combine(day.fromordinal(day.toordinal() + 1), time.min, zone)
    return start.astimezone(timezone.utc).isoformat(), end.astimezone(timezone.utc).isoformat()


def _round_tokens(characters):
    return int(characters / 4.0 + 0.5)


def render_day(book, day, timezone_name=DEFAULT_TIMEZONE):
    """Return an exact, privacy-filtered Markdown projection, or None when empty."""
    book.verify()
    start, end = _bounds(day, timezone_name)
    rows = list(book.db.execute('''
        SELECT s.seq,s.tx,s.ordinal,s.role,s.text,s.created,i.page,
               COALESCE(p.state,'VISIBLE') AS privacy_state
          FROM transcript s
          JOIN transactions t ON t.tx=s.tx
          JOIN identities i ON i.hcid=t.hcid
          LEFT JOIN privacy_state p ON p.tx=s.tx AND p.ordinal=s.ordinal
         WHERE s.created>=? AND s.created<?
         ORDER BY s.seq
    ''', (start, end)))
    if not rows:
        return None

    groups = []
    by_page = {}
    user_chars = assistant_chars = 0
    for row in rows:
        page = row['page']
        if page not in by_page:
            group = {'page': page, 'rows': []}
            by_page[page] = group
            groups.append(group)
        text = row['text'] if row['privacy_state'] != 'HIDDEN' else '[HIDDEN — content withheld]'
        by_page[page]['rows'].append((row['role'], text))
        if row['privacy_state'] != 'HIDDEN':
            if row['role'] == 'HUMAN':
                user_chars += len(row['text'])
            elif row['role'] == 'ASSISTANT':
                assistant_chars += len(row['text'])

    parts = [f'# Life Notebook — {day.isoformat()}', '', 'Status: COMPLETE', '']
    for group in groups:
        parts.extend([f'## Chat — {group["page"]}', ''])
        for role, text in group['rows']:
            label = 'USER' if role == 'HUMAN' else 'ASSISTANT'
            parts.extend([f'### {label}', '', text, ''])

    transcript_chars = user_chars + assistant_chars
    transcript_text = '\n'.join(
        text for group in groups for _, text in group['rows']
        if text != '[HIDDEN — content withheld]'
    )
    parts.extend([
        '## Derived Notes', '',
        '- Exact local Mirror transcript projected; no additional analysis.', '',
        '## Usage', '',
        f'- Chats captured: {len(groups)}',
        f'- Messages captured: {len(rows)}',
        f'- User-input characters: {user_chars}',
        f'- Assistant-output characters: {assistant_chars}',
        f'- Total transcript characters: {transcript_chars}',
        f'- Transcript words: {len(transcript_text.split())}',
        f'- Estimated user-input tokens (ESTIMATED): {_round_tokens(user_chars)}',
        f'- Estimated assistant-output tokens (ESTIMATED): {_round_tokens(assistant_chars)}',
        f'- Estimated total transcript tokens (ESTIMATED): {_round_tokens(transcript_chars)}',
        '',
    ])
    return '\n'.join(parts)


def project_day(book, day, timezone_name=DEFAULT_TIMEZONE, output_dir=None):
    text = render_day(book, day, timezone_name)
    if text is None:
        return None
    target_dir = Path(output_dir) if output_dir else book.root / 'daily-pages'
    target_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = target_dir / f'Life Notebook — {day.isoformat()}.md'
    pending = target.with_suffix(target.suffix + '.pending')
    with open(pending, 'w', encoding='utf-8', newline='') as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(pending, target)
    fd = os.open(str(target_dir), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    if target.read_text(encoding='utf-8') != text:
        raise RuntimeError('Daily Life Notebook projection readback mismatch')
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description='Project exact local Mirror turns by day')
    parser.add_argument('day', type=date.fromisoformat)
    parser.add_argument('--vault', default='HumanOS_Vault')
    parser.add_argument('--timezone', default=DEFAULT_TIMEZONE)
    parser.add_argument('--output-dir')
    args = parser.parse_args(argv)
    book = Notebook(args.vault)
    try:
        target = project_day(book, args.day, args.timezone, args.output_dir)
        print(json.dumps({'status': 'NO_TRANSCRIPT' if target is None else 'PROJECTED',
                          'path': str(target) if target else None}, sort_keys=True))
    finally:
        book.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
