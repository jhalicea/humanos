"""Read-only, session-bound facts. These answers do not depend on model guesses."""
import re
import shlex
import json
from datetime import datetime
from capabilities import summary
from notebook_recall import format_recall, search_notebook
from references import simple_plan_reference_action, simple_reference_read


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
    if (text == '/capabilities' or 'search the internet' in text or
        (re.search(r'\b(can you|are you able|what can you|what do you need|why not)\b', text) and
         re.search(r'\b(file|files|folder|folders|organize|duplicates|do that)\b', text))):
        return 'capabilities'


def request_for(text, history, reference_binding=None):
    try:
        words = shlex.split(text)
    except ValueError:
        words = []
    if reference_binding and reference_binding.get('kind', 'file') == 'file' and simple_reference_read(text):
        return {'name': 'read_file', 'path': reference_binding['path']}
    if reference_binding and reference_binding.get('kind') == 'plan' and simple_plan_reference_action(text):
        lowered = text.casefold()
        name = 'undo_plan' if re.search(r'\b(undo|revert)\b', lowered) else 'apply_plan'
        return {'name': name, 'plan_id': reference_binding['path']}
    if re.match(r'^\s*/recall(?:\s|$)', text):
        if not words or words[0] != '/recall':
            return {'name': 'recall_notebook', 'query': ''}
        return {'name': 'recall_notebook', 'query': ' '.join(words[1:])}
    commands = {'/files': 'scan_files', '/duplicates': 'find_duplicates', '/organize': 'plan_organization',
                '/smart-organize': 'plan_contextual_organization', '/understand': 'understand_file',
                '/organize-inbox': 'plan_inbox_organization', '/read': 'read_file', '/source': 'read_source'}
    if words and words[0] in commands and len(words) <= 3:
        name = commands[words[0]]
        default_path = 'server.py' if name == 'read_source' else 'inbox' if name == 'plan_inbox_organization' else '.'
        result = {'name': name, 'path': words[1] if len(words) > 1 else default_path}
        if len(words) == 3:
            if name not in ('read_file', 'read_source') or not words[2].isdigit():
                return None
            result['offset'] = int(words[2])
        return result
    if words and words[0] in ('/apply', '/undo') and len(words) == 2:
        return {'name': 'apply_plan' if words[0] == '/apply' else 'undo_plan', 'plan_id': words[1]}
    if words and words[0] == '/move' and len(words) == 3:
        return {'name': 'plan_move', 'source': words[1], 'destination': words[2]}
    lowered = text.casefold()
    excluded = bool(re.search(r'\b(not|never|avoid|except|without|exclude|excluding|don.t)\b', lowered))
    bare_server = any(token.strip('.,!?;:`\"\'') == 'server.py' for token in words)
    if not excluded and re.search(r'\b(read|show|inspect)\b', lowered) and (
            bare_server or 'where this instance is running' in lowered or 'your source' in lowered):
        return {'name': 'read_source', 'path': 'server.py'}
    if not excluded:
        # Only complete, unambiguous phrases grant a whole-folder scan. Folder
        # qualifiers and exclusions must never be silently widened to '.'.
        if re.fullmatch(r'(find|check|scan|show)( for)? duplicates?[.! ]*', lowered.strip()):
            return {'name': 'find_duplicates', 'path': '.'}
        if re.fullmatch(r'(organize|sort) (my |these |the )?(files|folders)[.! ]*', lowered.strip()):
            return {'name': 'plan_organization', 'path': '.'}
        if re.fullmatch(r'(mirror )?(organize|sort) (my |these |the )?inbox[.! ]*', lowered.strip()):
            return {'name': 'plan_inbox_organization', 'path': 'inbox'}
    kind = intent(text)
    if text.casefold().strip().rstrip('?!.') in ('do it', 'why', 'what do you mean'):
        for item in reversed(history):
            if item['role'] == 'HUMAN':
                kind = intent(item['text'])
                if item['text'].casefold().strip().rstrip('?!.') not in ('do it', 'why', 'what do you mean'):
                    break
    names = {'clock': 'current_time', 'notebook': 'read_notebook', 'capabilities': 'runtime_capabilities'}
    return {'name': names[kind]} if kind else None


def failure_message(error):
    text = str(error)
    if 'iteration budget' in text or 'time budget' in text:
        return ('I could not complete this request within the task limit. I saved your input and the attempted steps. '
                'This task is closed as unsuccessful, and you can continue chatting. Try /read PATH for a workspace file, '
                '/source server.py for HumanOS code, or /capabilities for available actions.')
    if 'unknown outcome' in text:
        return ('An interrupted file change needs inspection before another attempt. I have preserved its state and closed '
                'this turn without repeating the action. You can continue chatting; the operation remains marked for reconciliation.')
    if 'permission scope' in text or 'no saved permission' in text:
        return ('This older task cannot safely resume with its saved permissions. It is closed without executing tools. '
                'Your original input and history are preserved. Please issue a fresh, specific request.')
    return 'I could not complete this request: ' + text + '. Your input and error were preserved; you can continue chatting.'


def format_plan(report, undo=False):
    lines = ['Folder: ' + report['workspace']['path'], 'Plan: ' + report['plan_id'],
             'Status: ' + report['status'], str(len(report['moves'])) + ' planned move(s):']
    for item in report['moves']:
        left, right = (item['destination'], item['source']) if undo else (item['source'], item['destination'])
        lines.append('  ' + left + ' → ' + right)
        if not undo and item.get('classification'):
            detail = item['classification']
            lines.append('    ' + detail['summary'] + ' — ' + detail['rationale'] +
                         ' (' + str(round(detail['confidence'] * 100)) + '% confidence)')
            if detail.get('rename'):
                lines.append('    Suggested filename: ' + detail['suggested_filename'] +
                             ' (the current name is generic or less searchable)')
    if not undo and report.get('metadata', {}).get('decisions'):
        kept = [item for item in report['metadata']['decisions'] if item['source'] == item['destination']]
        for item in kept:
            detail = item['classification']
            lines.append('  KEEP ' + item['source'])
            lines.append('    ' + detail['summary'] + ' — ' + detail['rationale'] +
                         ' (' + str(round(detail['confidence'] * 100)) + '% confidence)')
            if detail.get('rename'):
                lines.append('    Suggested filename: ' + detail['suggested_filename'] +
                             ' (the current name is generic or less searchable)')
    lines.append('Existing destinations will never be overwritten. Undo restores unchanged items; empty folders created for the plan may remain.')
    return '\n'.join(lines)


def format_observation(request, observation):
    if not observation['ok']:
        error = observation['stderr']
        if observation.get('authorization') == 'DENIED':
            return ('HumanOS did not authorize that exact request in this turn. '
                    'This does not mean the workspace is read-only. Name the file explicitly or choose from the verified candidates.')
        if 'FileNotFoundError' in error:
            return ('I could not find ' + request.get('path', 'that file') + ' in the selected folder. '
                    'Use /files to see its contents. HumanOS source code is separate: use /source server.py.')
        return 'I could not complete that action: ' + error
    name = request['name']
    if name == 'read_source':
        page = json.loads(observation['stdout'])
        answer = 'HumanOS source: ' + page['source'] + '\n\n' + page['text']
        if page['truncated']:
            answer += '\nContinue with /source ' + page['path'] + ' ' + str(page['next_offset'])
        return answer
    if name == 'read_file':
        answer = 'File: ' + request['path'] + '\n\n' + observation['stdout']
        if observation.get('truncated'):
            answer += '\nContinue with /read ' + shlex.quote(request['path']) + ' ' + str(observation['next_offset'])
        return answer
    if name in ('scan_files', 'find_duplicates', 'plan_organization', 'understand_file',
                'plan_contextual_organization', 'plan_inbox_organization', 'plan_move', 'apply_plan', 'undo_plan'):
        report = json.loads(observation['stdout'])
        if name == 'scan_files':
            lines = ['Folder: ' + report['folder'], str(len(report['entries'])) + ' visible entries:']
            lines.extend('  ' + item['path'] + ('/' if item['kind'] == 'folder' else ' (' + str(item['size']) + ' bytes)') for item in report['entries'])
            if report['truncated']: lines.append('Scan limit reached; this list is incomplete. Select a smaller subfolder.')
            if report['skipped']: lines.append(str(len(report['skipped'])) + ' hidden, protected, linked or special entries excluded.')
            return '\n'.join(lines)
        if name == 'find_duplicates':
            lines = [str(len(report['groups'])) + ' duplicate group(s) found using complete content hashes and sizes.']
            for index, group in enumerate(report['groups'], 1):
                lines.append('Group ' + str(index) + ' (' + str(group['size']) + ' bytes per file):')
                lines.extend('  ' + path for path in group['files'])
            if report['incomplete']: lines.append('Scan incomplete; some files could not be checked. Select a smaller subfolder or inspect the recorded errors.')
            if report['skipped']: lines.append(str(len(report['skipped'])) + ' hidden, protected, linked or special entries excluded.')
            lines.append('Nothing deleted or moved.')
            return '\n'.join(lines)
        if name == 'understand_file':
            folder = ('current folder' if report['destination_folder'] == '.' else report['destination_folder'])
            return ('File: ' + report['source'] + '\nSummary: ' + report['summary'] +
                    '\nSuggested folder: ' + folder +
                    '\nWhy: ' + report['rationale'] +
                    '\nConfidence: ' + str(round(report['confidence'] * 100)) +
                    '%\nNothing moved.')
        answer = format_plan(report, undo=name == 'undo_plan')
        plan_id = report.get('plan_id') or report.get('id')
        if plan_id and name in ('plan_organization', 'plan_contextual_organization', 'plan_move'):
            answer += '\nNo files moved. Review this plan, then use /apply ' + plan_id
        if plan_id and name == 'apply_plan':
            answer += '\nTo undo this plan, use /undo ' + plan_id
        return answer
    return observation['stdout']


def execute(book, identity, tx, name, now=None):
    row = book.get_transaction(tx)
    if not row or row['hcid'] != identity['hcid'] or book.get_identity(row['hcid']) != identity or identity['binding'] != 'VERIFIED':
        raise PermissionError('Runtime query requires the verified transaction identity')
    if name == 'current_time':
        value = (now or datetime.now().astimezone()).isoformat(timespec='seconds')
        result = 'Your Mac’s local date and time is ' + value + '.'
    elif name == 'runtime_capabilities':
        result = summary()
    elif name == 'recall_notebook':
        state = book.task(tx) or {}
        request = state.get('permissions', {}).get('recall_request')
        if not isinstance(request, dict) or request.get('name') != 'recall_notebook':
            raise PermissionError('Notebook recall requires the exact human-derived recall scope')
        result = format_recall(search_notebook(book, identity['owner'], tx, request.get('query', '')))
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
