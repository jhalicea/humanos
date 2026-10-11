"""Explicit local command for original turn capture and evidence readback.

All request values arrive as one JSON object on standard input. Do not put
private transcript text, search queries, or owner identifiers in process argv.
"""
import argparse
import json
import sys
from pathlib import Path

from conversation_capture import UniversalConversationCapture
from notebook import Notebook
from notebook_recall import search_notebook

MAX_REQUEST_CHARS = 1024 * 1024
REQUIRED_FIELDS = {
    'capture': frozenset(('owner', 'source', 'conversation_id', 'turn_id', 'human', 'assistant')),
    'read': frozenset(('owner', 'tx')),
    'recall': frozenset(('owner', 'query')),
}


def _request_from_stdin(command):
    """Validate a bounded JSON request before opening or creating any vault."""
    try:
        raw = sys.stdin.read(MAX_REQUEST_CHARS + 1)
    except UnicodeError as error:
        raise ValueError('request must be valid UTF-8 text') from error
    if len(raw) > MAX_REQUEST_CHARS:
        raise ValueError('request exceeds maximum length')
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, UnicodeError) as error:
        raise ValueError('request must be a JSON object') from error
    if not isinstance(data, dict):
        raise ValueError('request must be a JSON object')
    required = REQUIRED_FIELDS[command]
    permitted = required | ({'hcid'} if command == 'capture' else set())
    if not required.issubset(data) or set(data) - permitted:
        raise ValueError('request fields do not match the command')
    for field in required:
        value = data[field]
        if not isinstance(value, str) or not value.strip():
            raise ValueError('required request values must be nonempty strings')
    if command == 'capture':
        for field, limit in (('source', 64), ('conversation_id', 512), ('turn_id', 512)):
            if len(data[field]) > limit:
                raise ValueError('capture identifier exceeds maximum length')
        if 'hcid' in data and (not isinstance(data['hcid'], str) or not data['hcid'].strip()):
            raise ValueError('hcid must be a nonempty string')
    return data


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vault', required=True, type=Path, help='Explicit local Notebook vault directory')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('capture', help='Capture already-observed turn from JSON stdin')
    sub.add_parser('read', help='Read original transcript using JSON stdin with owner and tx')
    sub.add_parser('recall', help='Bounded original-evidence search using JSON stdin with owner and query')
    args = parser.parse_args(argv)
    if not args.vault.is_absolute():
        parser.error('--vault must be an absolute path')
    try:
        request = _request_from_stdin(args.command)
    except ValueError as error:
        parser.error(str(error))
    if args.command != 'capture' and not (args.vault / 'runtime' / 'notebook.sqlite3').is_file():
        parser.error('Notebook vault does not exist')
    if args.command == 'capture' and request.get('hcid') and not (args.vault / 'runtime' / 'notebook.sqlite3').is_file():
        parser.error('hcid requires an existing Notebook vault')

    book = None
    try:
        book = Notebook(args.vault)
        book.recover()
        book.verify()
        if args.command == 'capture':
            capture = UniversalConversationCapture(book, request['source'])
            # Resolve the exact vault-keyed source-turn identity BEFORE book.bind:
            # an ordinary retry without --hcid must not create another page,
            # and a conflicting retry must not trigger Notebook.start's
            # content-preserving recovery/failure journal as a side effect.
            host_key = capture._host_key(request['conversation_id'], request['turn_id'])
            existing_tx = capture._tx(host_key)
            prior = book.get_transaction(existing_tx)
            hcid = request.get('hcid')
            if prior is not None:
                identity = book.get_identity(prior['hcid'])
                state = book.task(existing_tx) or {}
                if (identity is None or identity['owner'] != request['owner']
                        or identity['binding'] != 'VERIFIED'
                        or (hcid is not None and hcid != identity['hcid'])
                        or prior['input'] != request['human']
                        or state.get('capture_version') != 1
                        or state.get('source') != request['source']
                        or state.get('external_key_digest') != host_key
                        or (state.get('phase') == 'COMPLETE'
                            and state.get('final') != request['assistant'])):
                    raise ValueError('Conversation capture retry differs from preserved evidence')
            else:
                if hcid:
                    row = book.db.execute('SELECT owner,binding FROM identities WHERE hcid=?',
                                          (hcid,)).fetchone()
                    if row is None or row['owner'] != request['owner'] or row['binding'] != 'VERIFIED':
                        raise ValueError('Existing binding does not match owner')
                identity = book.bind(request['owner'], request['human'], hcid=hcid)
            tx = capture.capture_turn(
                identity['hcid'], request['conversation_id'], request['turn_id'],
                request['human'], request['assistant'])
            result = {'tx': tx, 'hcid': identity['hcid'], 'page': identity['page'],
                      'source': request['source'], 'status': book.get_transaction(tx)['status']}
        elif args.command == 'read':
            transaction = book.get_transaction(request['tx'])
            if transaction is None:
                raise ValueError('Transaction unavailable')
            identity = book.get_identity(transaction['hcid'])
            if identity is None or identity['owner'] != request['owner'] or identity['binding'] != 'VERIFIED':
                raise ValueError('Transaction unavailable')
            # Notebook projections apply the existing HIDE/UNHIDE privacy rule.
            page = json.loads(book.projections()['pages/' + identity['page'] + '.json'])
            rows = [row for row in page['transcript'] if row['tx'] == request['tx']]
            if not rows or any(row['text'] == '[HIDDEN — content withheld]' for row in rows):
                raise ValueError('Transaction unavailable')
            result = {'tx': request['tx'], 'status': transaction['status'],
                      'source': (book.task(request['tx']) or {}).get('source'),
                      'transcript': [{'role': row['role'], 'text': row['text']} for row in rows]}
        else:
            report = search_notebook(book, request['owner'], 'LOCAL-RECALL', request['query'])
            for item in report['results']:
                item['source'] = (book.task(item['tx']) or {}).get('source')
            result = report
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, ValueError, RuntimeError):
        # Do not echo exception values, which may contain paths or source data.
        print('Notebook operation failed', file=sys.stderr)
        return 1
    finally:
        if book is not None:
            book.close()


if __name__ == '__main__':
    raise SystemExit(main())
