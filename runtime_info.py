"""Read-only, session-bound facts. These answers do not depend on model guesses."""
import re
import shlex
import json
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
    if re.search(r'\b(what|which)\b.*\b(model|llm)\b', text):
        return 'capabilities'
    if re.search(r'\b(system|runtime|humanos)\b.*\b(specifications?|details|policy|rules|capabilities)\b', text):
        return 'capabilities'
    if re.search(r'\b(what|which)\b.*\b(files|source|code)\b.*\b(can|able|see|read|access)\b', text):
        return 'capabilities'
    if text == '/time' or re.search(r'\b(what|current|know|tell|show)\b.*\btime\b', text):
        return 'clock'
    if text == '/notebook' or ('notebook' in text and re.search(r'\b(show|what|tell|is|read)\b', text)):
        return 'notebook'
    if (text == '/capabilities' or 'search the internet' in text or
        (re.search(r'\b(can you|are you able|what can you|what do you need|why not)\b', text) and
         re.search(r'\b(file|files|folder|folders|organize|duplicates|do that)\b', text))):
        return 'capabilities'


def request_for(text, history):
    try:
        words = shlex.split(text)
    except ValueError:
        words = []
    commands = {'/files': 'scan_files', '/duplicates': 'find_duplicates', '/organize': 'plan_organization',
                '/smart-organize': 'plan_contextual_organization', '/understand': 'understand_file',
                '/organize-inbox': 'plan_inbox_organization', '/read': 'read_file', '/source': 'read_source'}
    if words and words[0] in ('/provenance', '/debug-trace', '/trace', '/why') and len(words) <= 3:
        full = len(words) == 3 and words[2] == '--full'
        if len(words) == 3 and not full:
            return None
        return {'name': 'debug_trace', 'tx': words[1] if len(words) >= 2 else '', 'full': full}
    if words and words[0] in commands and len(words) <= 3:
        name = commands[words[0]]
        default_path = 'server.py' if name == 'read_source' else 'inbox' if name == 'plan_inbox_organization' else '.'
        result = {'name': name, 'path': words[1] if len(words) > 1 else default_path}
        if len(words) == 3:
            if name not in ('read_file', 'read_source') or not words[2].isdigit():
                return None
            result['offset'] = int(words[2])
        return result
    normalized = text.casefold().replace('runtiem-check.txt', 'runtime-check.txt')
    if re.search(r'\b(read|show|open|inspect|what|tell)\b', normalized) and 'runtime-check.txt' in normalized:
        return {'name': 'read_file', 'path': 'runtime-check.txt'}
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


def execute(book, identity, tx, request, now=None, model_name=None, workspace=None):
    name = request.get('name') if isinstance(request, dict) else request
    row = book.get_transaction(tx)
    if not row or row['hcid'] != identity['hcid'] or book.get_identity(row['hcid']) != identity or identity['binding'] != 'VERIFIED':
        raise PermissionError('Runtime query requires the verified transaction identity')
    if name == 'current_time':
        value = (now or datetime.now().astimezone()).isoformat(timespec='seconds')
        result = 'Your Mac’s local date and time is ' + value + '.'
    elif name == 'runtime_capabilities':
        details = []
        if model_name:
            details.append('Configured local model: ' + model_name + '.')
        if workspace:
            details.append('Selected workspace folder: ' + str(workspace) + '.')
        result = ('\n'.join(details) + '\n' if details else '') + summary()
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
    elif name == 'debug_trace':
        result = debug_trace(book, identity, tx, request.get('tx') or tx, request.get('full', False))
    else:
        raise PermissionError('Unknown runtime query')
    return result


def debug_trace(book, identity, current_tx, target_tx, full=False):
    row = book.get_transaction(target_tx)
    if not row or row['hcid'] != identity['hcid']:
        raise PermissionError('Debug trace is limited to this verified session')
    state = book.task(target_tx) or {}
    events = [dict(r) for r in book.db.execute(
        "SELECT seq,kind,payload,created FROM events WHERE tx=? ORDER BY seq", (target_tx,))]
    lines = [
        ('Full debug trace for ' if full else 'Provenance summary for ') + target_tx,
        'Hidden chain-of-thought captured: no.',
        ('Full trace includes owner-visible prompts, exposed model outputs, tool events, permissions, hashes, and summaries.'
         if full else 'Summary trace avoids replaying prompts, model packets, and tool output. Use /debug-trace ' + target_tx + ' --full to explicitly display them.'),
        'Input SHA-256: ' + state.get('permissions', {}).get('input_sha256', digest_or_unknown(row['input'])),
        'Model: ' + str(state.get('model', 'not recorded')),
        'Phase: ' + str(state.get('phase', 'not recorded')),
    ]
    provenance = []
    for event in events:
        if event['kind'] == 'REASONING_PROVENANCE':
            try:
                provenance.append(json.loads(event['payload']))
            except json.JSONDecodeError:
                provenance.append({'summary': 'Unreadable provenance event payload'})
    if provenance:
        lines.append('Reasoning provenance:')
        for item in provenance:
            lines.append('  ' + item.get('summary', 'No summary recorded.'))
            lines.append('  model=' + str(item.get('model', 'not recorded')) +
                         ' steps=' + str(item.get('steps', 'not recorded')) +
                         ' direct_response=' + str(item.get('direct_response', False)))
            attempted = item.get('attempted_reads') or []
            if attempted:
                lines.append('  attempted_reads=' + ', '.join(attempted))
    if not full:
        lines.append('Audit event kinds: ' + ', '.join(event['kind'] for event in events))
        return '\n'.join(lines)
    context = state.get('context') or {}
    if context.get('records'):
        lines.append('Context records:')
        for record in context['records']:
            lines.append('  ' + record.get('source', 'unknown') + ' sha256=' + record.get('sha256', 'unknown'))
    if state.get('messages'):
        lines.append('Visible model message packet:')
        for index, message in enumerate(state['messages']):
            content = message.get('content', '')
            if len(content.encode('utf-8')) > 2000:
                content = content[:2000] + ' [excerpt truncated]'
            lines.append('  [' + str(index) + '] ' + message.get('role', 'unknown') + ': ' + content)
    if events:
        lines.append('Audit events:')
        for event in events:
            payload = event['payload']
            if len(payload.encode('utf-8')) > 2000:
                payload = payload[:2000] + ' [excerpt truncated]'
            lines.append('  #' + str(event['seq']) + ' ' + event['kind'] + ' ' + payload)
    return '\n'.join(lines)


def digest_or_unknown(text):
    try:
        from notebook import digest
        return digest(text)
    except Exception:
        return 'unknown'
