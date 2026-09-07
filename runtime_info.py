"""Read-only, session-bound facts. These answers do not depend on model guesses."""
import re
from datetime import datetime


def recent(book, hcid, exclude_tx, limit=12, budget=8000):
    rows = book.db.execute('''SELECT s.seq,s.tx,s.role,s.text,s.sha256
        FROM transcript s JOIN transactions t ON t.tx=s.tx
        WHERE t.hcid=? AND t.tx!=? AND t.status='CHECKPOINTED'
        ORDER BY s.seq DESC LIMIT ?''', (hcid, exclude_tx, limit)).fetchall()
    result = []
    for row in rows:
        item = dict(row)
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


def answer(book, identity, tx, text, history, now=None):
    kind = intent(text)
    if text.casefold().strip().rstrip('?!.') in ('do it', 'why', 'what do you mean'):
        for item in reversed(history):
            if item['role'] == 'HUMAN':
                kind = intent(item['text'])
                if item['text'].casefold().strip().rstrip('?!.') not in ('do it', 'why', 'what do you mean'):
                    break
    if not kind:
        return None
    book.event(tx, 'RUNTIME_QUERY_AUTHORIZATION', {'query': kind, 'hcid': identity['hcid'],
        'allowed': True, 'scope': 'read-only current session or local clock; requested by human'})
    if kind == 'clock':
        value = (now or datetime.now().astimezone()).isoformat(timespec='seconds')
        result = 'Your Mac’s local date and time is ' + value + '.'
    elif kind == 'capabilities':
        result = ('This HumanOS runtime can converse using the configured local model, read the Mac’s clock, '
                  'show this session’s local Life Notebook, and read/list authorized workspace files. '
                  'Creating a new workspace file requires approval. Internet search and Drive synchronization '
                  'are not connected. Use /time, /notebook, or /capabilities for verified runtime information.')
    else:
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
    book.event(tx, 'RUNTIME_QUERY_RESULT', {'query': kind, 'text': result})
    return result
