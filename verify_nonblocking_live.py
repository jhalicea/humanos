"""Real local-model acceptance for continuing beside unfinished turns.

Uses only a temporary Notebook and workspace. It never opens the owner's vault.
"""
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
    with tempfile.TemporaryDirectory(prefix='humanos-nonblocking-live-') as folder:
        root = Path(folder)
        book = Notebook(root / 'vault')
        try:
            book.recover()
            identity = book.bind('Jon', 'isolated non-blocking recovery acceptance')
            book.start(identity['hcid'], 'old-unfinished', 'older unfinished input')
            tools = Tools(root / 'workspace')
            model = OllamaModel(config['model'], config['endpoint'])

            agent = Agent(book, model, tools, base / 'core', finalize_on_error=True)
            final = agent.run('current', identity['hcid'], 'Say hello in one short sentence.')
            runtime = object.__new__(HumanOSRuntime)
            runtime.book = book
            output = io.StringIO()
            runtime.deliver('current', final, output)
            assert output.getvalue() == final + '\n'
            assert book.get_transaction('current')['status'] == 'CHECKPOINTED'
            assert book.get_transaction('old-unfinished')['status'] == 'STARTED'

            rejected = '  exact input retained from a blocked turn 🧭\n'
            book.problem('recovered-input', 'simulated earlier turn blocker', {
                'hcid': identity['hcid'], 'requested_tx': 'recovered-input',
                'role': 'HUMAN', 'text': rejected})
            pending = book.recover()
            assert book.get_transaction('recovered-input')['input'] == rejected
            assert book.message_count('recovered-input') == 1
            assert {'old-unfinished', 'recovered-input'} <= {row['tx'] for row in pending}

            direct = Agent(book, model, tools, base / 'core', finalize_on_error=True)
            capabilities = direct.run('next', identity['hcid'], '/capabilities')
            output = io.StringIO()
            runtime.deliver('next', capabilities, output)
            assert 'organize files using a reviewed plan' in capabilities
            assert book.get_transaction('next')['status'] == 'CHECKPOINTED'
            assert book.message_count('next') == 2
            book.verify()
            print('2/2 live turns passed; unfinished and recovered inputs remained pending, '
                  'new final output and Notebook readback verified.')
        finally:
            book.close()


if __name__ == '__main__':
    main()
