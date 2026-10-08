"""Explicit local command for original turn capture and evidence readback."""

import argparse
import json
import sys
from pathlib import Path

from conversation_capture import UniversalConversationCapture
from notebook import Notebook
from notebook_recall import search_notebook


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--vault', required=True, type=Path, help='Explicit local Notebook vault directory')
    sub = parser.add_subparsers(dest='command', required=True)
    capture = sub.add_parser('capture', help='Save one already-observed complete turn')
    for flag in ('owner', 'source', 'conversation-id', 'turn-id', 'human', 'assistant'):
        capture.add_argument('--' + flag, required=True)
    capture.add_argument('--hcid', help='Binding returned by an earlier capture')
    read = sub.add_parser('read', help='Read exact original transcript and source by transaction ID')
    read.add_argument('--tx', required=True)
    recall = sub.add_parser('recall', help='Bounded lexical search of original evidence')
    recall.add_argument('--owner', required=True)
    recall.add_argument('--query', required=True)
    args = parser.parse_args(argv)
    if not args.vault.is_absolute():
        parser.error('--vault must be an absolute path')
    if args.command != 'capture' and not (args.vault / 'runtime' / 'notebook.sqlite3').is_file():
        parser.error('Notebook vault does not exist')
    if args.command == 'capture':
        for flag in ('owner', 'source', 'conversation_id', 'turn_id'):
            if not getattr(args, flag).strip():
                parser.error('--' + flag.replace('_', '-') + ' must be nonempty')
        for flag, limit in (('source', 64), ('conversation_id', 512), ('turn_id', 512)):
            if len(getattr(args, flag)) > limit:
                parser.error('--' + flag.replace('_', '-') + ' is too long')
        if args.hcid and not (args.vault / 'runtime' / 'notebook.sqlite3').is_file():
            parser.error('--hcid requires an existing Notebook vault')
    book = None
    try:
        book = Notebook(args.vault)
        book.recover()
        book.verify()
        if args.command == 'capture':
            if args.hcid:
                row = book.db.execute('SELECT owner,binding FROM identities WHERE hcid=?',
                                      (args.hcid,)).fetchone()
                if row is None or row['owner'] != args.owner or row['binding'] != 'VERIFIED':
                    raise ValueError('Existing binding does not match owner')
            identity = book.bind(args.owner, args.human, hcid=args.hcid)
            tx = UniversalConversationCapture(book, args.source).capture_turn(
                identity['hcid'], args.conversation_id, args.turn_id, args.human, args.assistant)
            result = {'tx': tx, 'hcid': identity['hcid'], 'page': identity['page'],
                      'source': args.source, 'status': book.get_transaction(tx)['status']}
        elif args.command == 'read':
            transaction = book.get_transaction(args.tx)
            if transaction is None:
                raise ValueError('Unknown transaction ID')
            rows = list(book.db.execute(
                'SELECT role,text FROM transcript WHERE tx=? ORDER BY ordinal', (args.tx,)))
            result = {'tx': args.tx, 'status': transaction['status'],
                      'source': (book.task(args.tx) or {}).get('source'),
                      'transcript': [dict(row) for row in rows]}
        else:
            report = search_notebook(book, args.owner, 'LOCAL-RECALL', args.query)
            for item in report['results']:
                item['source'] = (book.task(item['tx']) or {}).get('source')
            result = report
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print('Notebook operation failed: ' + str(error), file=sys.stderr)
        return 1
    finally:
        if book is not None:
            book.close()


if __name__ == '__main__':
    raise SystemExit(main())
