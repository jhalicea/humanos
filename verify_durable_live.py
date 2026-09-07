"""Opt-in local Ollama acceptance, always isolated from the owner's Notebook."""
import io
import json
from pathlib import Path
import tempfile
from engine import Agent, OllamaModel, Tools
from notebook import Notebook
from server import HumanOSRuntime


def main():
    base = Path(__file__).resolve().parent
    config = json.loads((base / 'config.json').read_text())
    with tempfile.TemporaryDirectory(prefix='humanos-live-') as folder:
        root = Path(folder)
        book = Notebook(root / 'vault')
        try:
            book.recover()
            tools = Tools(root / 'workspace')
            (tools.workspace / 'runtime-check.txt').write_text(
                'Verification phrase: continuity belongs to Jon.\nVerification code: HOS-LOCAL-62947.\n')
            identity = book.bind('Jon', 'isolated live acceptance')
            adapter = OllamaModel(config['model'], config['endpoint'])
            agent = Agent(book, adapter, tools, base / 'core')
            runtime = object.__new__(HumanOSRuntime)
            runtime.book = book
            cases = [('remember', 'Remember this word for my next question: turquoise.'),
                     ('recall', 'What word did I ask you to remember?'),
                     ('clock', '/time'), ('notebook', '/notebook'),
                     ('file', 'Read runtime-check.txt and tell me its verification phrase and code.')]
            for tx, text in cases:
                try:
                    final = agent.run(tx, identity['hcid'], text)
                except Exception:
                    # Only synthetic fixture data exists in this isolated vault.
                    events = [dict(row) for row in book.db.execute(
                        "SELECT kind,payload FROM events WHERE tx=? AND kind IN ('MODEL_RESPONSE','MODEL_RESPONSE_REJECTED','TOOL_RESULT')", (tx,))]
                    print(json.dumps({'failed_case': tx, 'events': events}, indent=2), flush=True)
                    raise
                stream = io.StringIO()
                runtime.deliver(tx, final, stream)
                saved = book.db.execute('SELECT text FROM transcript WHERE tx=? AND ordinal=?',
                                       (tx, book.task(tx)['final_ordinal'])).fetchone()[0]
                assert stream.getvalue() == saved + '\n'
                assert book.get_transaction(tx)['status'] == 'CHECKPOINTED'
                assert book.task(tx)['delivery'] == 'WRITTEN_TO_OUTPUT_STREAM'
                if tx == 'recall': assert 'turquoise' in final.lower(), final
                if tx == 'clock': assert 'local date and time' in final, final
                if tx == 'notebook': assert '4 transactions and 7 saved transcript messages' in final, final
                if tx == 'file': assert 'continuity belongs to Jon' in final and 'HOS-LOCAL-62947' in final, final
                print(tx + ': PASS (' + str(book.task(tx)['steps']) + ' model calls)', flush=True)
            book.verify()
            assert book.delivery_pending() == []
            print('5/5 live turns passed; exact output, Notebook readback, and delivery verified.')
        finally:
            book.close()


if __name__ == '__main__':
    main()
