"""Isolated local-model acceptance for contextual organization."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

from server import HumanOSRuntime


def main():
    base = Path(__file__).resolve().parent
    config = json.loads((base / 'config.json').read_text())
    with tempfile.TemporaryDirectory(prefix='humanos-context-live-') as folder:
        root = Path(folder); workspace = root / 'workspace'; workspace.mkdir()
        fixtures = {
            '2026-tax-receipt.txt': b'Paid quarterly business taxes for the Acme consulting project. Receipt 62947.\n',
            'vacation-itinerary.md': b'# Puerto Rico family vacation\nFlights, hotel, and beach plans for June.\n',
            'insurance-policy.pdf': b'%PDF-1.4\x00synthetic metadata-only fixture\xff',
        }
        for name, content in fixtures.items(): (workspace / name).write_bytes(content)
        runtime = HumanOSRuntime(config=dict(config, vault=str(root / 'vault'),
                                            workspace=str(workspace), core=str(base / 'core')))
        book = runtime.book; identity = book.bind('Jon', 'isolated contextual acceptance')

        def turn(tx, text, approval=False):
            runtime.agent.authorize = lambda request: runtime.authorize(tx, request)
            approval_output = io.StringIO()
            with patch('sys.stdin.isatty', return_value=approval), \
                    patch('builtins.input', side_effect=lambda prompt: print(prompt, end='') or 'yes'), \
                    redirect_stdout(approval_output):
                final = runtime.agent.run(tx, identity['hcid'], text)
            output = io.StringIO(); runtime.deliver(tx, final, output)
            transcript = list(book.db.execute('SELECT role,text FROM transcript WHERE tx=? ORDER BY ordinal', (tx,)))
            assert transcript[0]['text'] == text and transcript[-1]['text'] == final
            assert output.getvalue() == final + '\n'
            assert book.get_transaction(tx)['status'] == 'CHECKPOINTED'
            if approval:
                assert [row['role'] for row in transcript] == ['HUMAN', 'ASSISTANT', 'HUMAN', 'ASSISTANT']
                assert transcript[2]['text'] == 'yes'
                assert approval_output.getvalue() == transcript[1]['text'] + '\n'
            book.verify()
            return final

        try:
            understood = turn('understand', '/understand 2026-tax-receipt.txt')
            assert 'Summary:' in understood and 'Suggested folder:' in understood and 'Nothing moved.' in understood
            assert all((workspace / name).read_bytes() == content for name, content in fixtures.items())
            print('understand: PASS', flush=True)

            preview = turn('preview', '/smart-organize')
            row = book.db.execute("SELECT payload FROM events WHERE tx='preview' AND kind='FILE_PLAN_CREATED'").fetchone()
            plan = json.loads(row['payload'])['plan']
            assert plan['metadata']['strategy'] == 'contextual-local-model'
            assert plan['metadata']['analyzed_files'] == 3
            assert all('classification' in item for item in plan['metadata']['decisions'])
            assert all((workspace / name).read_bytes() == content for name, content in fixtures.items())
            assert 'No files moved' in preview
            print('preview: PASS (' + str(len(plan['moves'])) + ' proposed moves)', flush=True)

            applied = turn('apply', '/apply ' + plan['plan_id'], approval=True)
            assert 'Status: APPLIED' in applied
            for item in plan['moves']:
                assert not (workspace / item['source']).exists()
                assert (workspace / item['destination']).read_bytes() == fixtures[item['source']]
            assert sum(path.is_file() for path in workspace.rglob('*')) == len(fixtures)
            print('approved apply: PASS', flush=True)

            undone = turn('undo', '/undo ' + plan['plan_id'], approval=True)
            assert 'Status: UNDONE' in undone
            assert all((workspace / name).read_bytes() == content for name, content in fixtures.items())
            assert sum(path.is_file() for path in workspace.rglob('*')) == len(fixtures)
            print('approved undo: PASS', flush=True)
            print('4/4 contextual live checks passed; local model classification, exact approval capture, '
                  'file preservation, Notebook checkpoint/readback and output verified.', flush=True)
        finally:
            book.close()


if __name__ == '__main__':
    main()
