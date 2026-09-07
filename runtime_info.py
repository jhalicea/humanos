"""Read-only, session-bound facts. These answers do not depend on model guesses."""
import re
from datetime import datetime
from capabilities import summary


def recent(book, hcid, exclude_tx, limit=12, budget=8000):
    rows = book.db.execute('''SELECT s.seq,s.tx,s.role,s.text,s.sha256
        FROM transcript s JOIN transactions t ON t.tx=s.tx
        WHERE t.hcid=? AND t.tx!=? AND t.status='CHECKPOINTED'
        ORDER BY s.seq DESC LIMIT ?''', (hcid, exclude_tx, limit)).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        state = book.task(item['tx']) or {}
        # Preserve saved-but-undelivered evidence in the Notebook, but never
        # present it as something the human already received in model history.
        if item['role'] == 'ASSISTANT' and state.get('delivery') != 'WRITTEN_TO_OUTPUT_STREAM':
            continue
        raw = item['text'].encode('utf-8')
        if len(raw) > budget:
            break
        budget -= len(raw)
        result.append(item)
    return list(reversed(result))


def intent(text):
    text = text.casefold().strip()
    if re.search(r'\b[\w-]+\.(txt|md|json|py|csv)\b', text):
        return None
    if text == '/time' or re.search(r'\b(what|current|know|tell|show)\b.*\btime\b', text):
        return 'clock'
    if text == '/notebook' or ('notebook' in text and re.search(r'\b(show|what|tell|is|read)\b', text)):
        return 'notebook'
    if text == '/capabilities' or 'search the internet' in text:
        return 'capabilities'


def request_for(text, history):
    kind = intent(text)
    if text.casefold().strip().rstrip('?!.') in ('do it', 'why', 'what do you mean'):
        for item in reversed(history):
            if item['role'] == 'HUMAN':
                kind = intent(item['text'])
                if item['text'].casefold().strip().rstrip('?!.') not in ('do it', 'why', 'what do you mean'):
                    break
    names = {'clock': 'current_time', 'notebook': 'read_notebook', 'capabilities': 'runtime_capabilities'}
    return {'name': names[kind]} if kind else None


def execute(book, identity, tx, name, now=None):
    row = book.get_transaction(tx)
    if not row or row['hcid'] != identity['hcid'] or book.get_identity(row['hcid']) != identity or identity['binding'] != 'VERIFIED':
        raise PermissionError('Runtime query requires the verified transaction identity')
    if name == 'current_time':
        value = (now or datetime.now().astimezone()).isoformat(timespec='seconds')
        result = 'Your Mac’s local date and time is ' + value + '.'
    elif name == 'runtime_capabilities':
        result = summary()
    elif name == 'read_notebook':
        history = recent(book, identity['hcid'], tx)
        book.verify()
        counts = book.db.execute('''SELECT COUNT(DISTINCT t.tx),COUNT(s.seq)
            FROM transactions t LEFT JOIN transcript s ON s.tx=t.tx WHERE t.hcid=?''',
            (identity['hcid'],)).fetchone()
        result = (f'Local Life Notebook page: {identity["page"]}\n'
                  f'This session has {counts[0]} transactions and {counts[1]} saved transcript messages '
                  '(including your current input, before this answer). This conversation is in the local Notebook.\n'
                  'The local ledger and page/index readback verified. Drive synchronization is not connected. '
                  'Saved assistant statements are historical evidence, not proof that their claims are true.\n'
                  'Recent saved transcript excerpt (bounded; not the whole Notebook):\n')
        result += '\n'.join(f'[{item["seq"]}] {item["role"]}: {item["text"][:500]}' +
                            (' [excerpt truncated]' if len(item['text']) > 500 else '') for item in history)
        pending = [entry for entry in book.delivery_pending() if entry['hcid'] == identity['hcid'] and entry['tx'] != tx]
        if pending:
            result += '\nSaved answers with unconfirmed output: ' + ', '.join(entry['tx'] for entry in pending)
    else:
        raise PermissionError('Unknown runtime query')
    return result
