"""HumanOS Runtime 0.1 — extends the original local Mirror entry point."""
import argparse
import json
import os
import sys
import uuid
from pathlib import Path
from notebook import Notebook
from engine import Agent, OllamaModel, Tools, load_context

BASE = Path(__file__).resolve().parent


class HumanOSRuntime:
    def __init__(self, vault_base=None, core_path=None, model=None, config=None):
        config = config or {}
        self.vault_base = Path(vault_base or config.get('vault', BASE / 'HumanOS_Vault'))
        self.core_path = Path(core_path or config.get('core', BASE / 'core'))
        self.model = model or os.environ.get('HUMANOS_MODEL', config.get('model', 'llama3:latest'))
        self.ollama_url = os.environ.get('HUMANOS_ENDPOINT', config.get('endpoint', 'http://127.0.0.1:11434'))
        self.book = Notebook(self.vault_base)
        self.pending = self.book.recover()
        self.tools = Tools(config.get('workspace', BASE / 'workspace'))
        self.adapter = OllamaModel(self.model, self.ollama_url)
        self.agent = Agent(self.book, self.adapter, self.tools, self.core_path,
                           max_steps=config.get('max_steps', 6), max_seconds=config.get('max_seconds', 180))

    def load_system_context(self):
        return load_context(self.core_path, [])

    def deliver(self, tx, response, stream=None):
        stream = stream or sys.stdout
        # Capture final once before delivery. Unknown terminal delivery is never called proven.
        stream.write(response + '\n')
        stream.flush()
        state = self.book.task(tx)
        state['delivery'] = 'WRITTEN_TO_OUTPUT_STREAM'
        self.book.save_task(tx, state)
        self.book.event(tx, 'DELIVERY', {'status': state['delivery'], 'text_sha256': __import__('notebook').digest(response)})
        self.book.verify()
        return response

    def run(self, args):
        if args.status:
            self.book.verify()
            print(json.dumps(dict(self.book.status(), pending=self.pending), indent=2))
            return
        if args.resume:
            response = self.agent.run(args.resume)
            self.deliver(args.resume, response)
            return
        if any((self.book.task(t['tx']) or {}).get('phase') != 'EXTERNAL_CAPTURE_PENDING' for t in self.pending):
            print('Unfinished transactions exist; use --status and --resume TX-ID.', file=sys.stderr)
        binding = None
        while True:
            try:
                text = args.message if args.message is not None else input('HUMAN: ')
                if text.lower() in ('exit', 'quit') and args.message is None:
                    return
                # Do not strip whitespace from visible input.
                if binding is None:
                    binding = self.book.bind('Jon', text, hcid=args.session)
                    print('HumanOS session: ' + binding['hcid'], file=sys.stderr)
                    print('Life Notebook page: ' + binding['page'], file=sys.stderr)
                tx = args.tx or 'TX-' + uuid.uuid4().hex
                print('Transaction: ' + tx, file=sys.stderr)
                def authorize(request):
                    if request.get('name') in ('read_file', 'list_files'):
                        return True  # Owner-granted read scope, limited to configured workspace.
                    if request.get('name') != 'create_file' or not sys.stdin.isatty():
                        return False
                    prompt = 'Approve creating this workspace file? ' + json.dumps(request, ensure_ascii=False) + ' [yes/no]'
                    n = self.book.message_count(tx)
                    self.book.append(tx, n, 'ASSISTANT', prompt)
                    self.book.project()
                    self.book.verify()
                    answer = input(prompt + '\n')
                    self.book.append(tx, n + 1, 'HUMAN', answer)
                    self.book.project()
                    self.book.verify()
                    return answer == 'yes'
                self.agent.authorize = authorize
                response = self.agent.run(tx, binding['hcid'], text, args.context)
                self.deliver(tx, response)
                if args.message is not None:
                    return
            except (KeyboardInterrupt, EOFError):
                print('\nStopped. Any unfinished transaction remains recoverable.', file=sys.stderr)
                return


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description='HumanOS Runtime 0.1 / Mirror')
    parser.add_argument('--config', default=str(BASE / 'config.json'))
    parser.add_argument('--session', help='Exact HCID printed by an earlier session')
    parser.add_argument('--tx', help='Caller-owned idempotent transaction ID')
    parser.add_argument('--message', help='Run one turn')
    parser.add_argument('--resume', help='Resume an exact transaction ID')
    parser.add_argument('--context', action='append', default=[], help='Relevant filename in core, e.g. runtime.md')
    parser.add_argument('--status', action='store_true')
    args = parser.parse_args()
    runtime = None
    try:
        config = json.loads(Path(args.config).read_text()) if Path(args.config).exists() else {}
        # Relative configured locations are relative to config, never current shell directory.
        for key in ('vault', 'core', 'workspace'):
            if key in config:
                config[key] = str((Path(args.config).resolve().parent / config[key]).resolve())
        runtime = HumanOSRuntime(config=config)
        runtime.run(args)
        return 0
    except Exception as error:
        print('HumanOS RECOVERY REQUIRED: ' + str(error), file=sys.stderr)
        return 1
    finally:
        if runtime:
            runtime.book.close()


if __name__ == '__main__':
    raise SystemExit(main())
