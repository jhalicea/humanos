import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from engine import Agent, Tools
from notebook import Notebook
from server_core import HumanOSRuntime
from terminal_delivery import POLICY, POLICY_ID, TerminalDeliveryError, validate_terminal_delivery
from work_mode import WorkContextModel


GOOD = '''Run this from any directory:

```bash
set -e
test -f /Users/jhalicea/Developer/10_Repos/humanos/scripts/smoke_codex_import.py
/usr/bin/env python3 /Users/jhalicea/Developer/10_Repos/humanos/scripts/smoke_codex_import.py
```'''


class ScriptedModel:
    name = 'synthetic'

    def __init__(self, final):
        self.final = final
        self.messages = None

    def invoke(self, messages, timeout):
        self.messages = messages
        return {'final': self.final}


class TerminalDeliveryTests(unittest.TestCase):
    def test_external_packet_and_filter_are_machine_consumable(self):
        module = str(Path(__file__).resolve().parents[1] / 'terminal_delivery.py')
        packet = subprocess.run([sys.executable, module, '--packet'], capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(packet.stdout)['rule'], POLICY)
        self.assertEqual(json.loads(packet.stdout)['policy_id'], POLICY_ID)
        rejected = subprocess.run([sys.executable, module], input='Run python3 scripts/smoke_codex_import.py',
                                  capture_output=True, text=True)
        self.assertEqual(rejected.returncode, 2)
        self.assertEqual(rejected.stdout, '')
    def test_compliant_smoke_and_nonterminal_text(self):
        self.assertEqual(validate_terminal_delivery(GOOD), GOOD)
        self.assertEqual(validate_terminal_delivery('Hello, Jon.'), 'Hello, Jon.')
        for action in ('/bin/ls /Users/jhalicea/Developer/10_Repos/humanos',
                       '/usr/bin/git -C /Users/jhalicea/Developer/10_Repos/humanos status --short'):
            message = ('```bash\nset -e\n'
                       'test -d /Users/jhalicea/Developer/10_Repos/humanos\n'
                       + action + '\n```')
            self.assertEqual(validate_terminal_delivery(message), message)

    def test_adversarial_commands_rejected(self):
        bad = [
            'Run `python3 scripts/smoke_codex_import.py`.',
            'Run python3 scripts/smoke_codex_import.py',
            'Run this: ```text\npython3 scripts/smoke_codex_import.py\n```',
            '```text\nls scripts\n```',
            'Run /tmp/foo.sh',
            'Run ~/script.sh',
            'pwd',
            GOOD.replace('/Users/jhalicea/Developer/10_Repos/humanos/scripts/smoke_codex_import.py',
                         'scripts/smoke_codex_import.py'),
            GOOD.replace('set -e\n', ''),
            GOOD.replace('test -f /Users/jhalicea/Developer/10_Repos/humanos/scripts/smoke_codex_import.py\n', ''),
            GOOD.replace('/usr/bin/env python3', 'git checkout main && /usr/bin/env python3'),
            GOOD.replace('/usr/bin/env python3', 'rm -rf /tmp/x\n/usr/bin/env python3'),
            GOOD + '\nThen run `git push --force`.',
            GOOD.replace('scripts/smoke_codex_import.py', 'scripts/<script>.py'),
            GOOD.replace('/Users/jhalicea/Developer/10_Repos/humanos/scripts/smoke_codex_import.py', '/tmp/delete_everything.py'),
            GOOD.replace('```bash', '```sh'),
            GOOD + '\n```bash\nrm -rf /tmp/x\n```',
        ]
        for candidate in bad:
            with self.subTest(candidate=candidate):
                with self.assertRaises(TerminalDeliveryError):
                    validate_terminal_delivery(candidate)

    def test_agent_compiles_policy_and_blocks_invalid_final_before_checkpoint(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            book = Notebook(root / 'vault')
            book.recover()
            binding = book.bind('Jon', 'test')
            model = ScriptedModel('Run `python3 scripts/smoke_codex_import.py`.')
            agent = Agent(book, model, Tools(root / 'workspace'), root / 'core', max_steps=1)
            (root / 'core').mkdir()
            result = agent.run('bad', binding['hcid'], 'Please show the smoke command')
            self.assertNotIn('python3 scripts/', result)
            self.assertIn('Terminal', result)
            self.assertIn('Terminal instructions for Jon', model.messages[0]['content'])
            self.assertEqual(book.get_transaction('bad')['status'], 'CHECKPOINTED')
            book.close()

    def test_saved_task_missing_policy_fails_closed_on_resume(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            book = Notebook(root / 'vault')
            book.recover()
            binding = book.bind('Jon', 'test')
            (root / 'core').mkdir()
            model = ScriptedModel('Hello, Jon.')
            agent = Agent(book, model, Tools(root / 'workspace'), root / 'core')
            self.assertEqual(agent.run('tx', binding['hcid'], 'hello'), 'Hello, Jon.')
            state = book.task('tx')
            state.pop('terminal_delivery_policy')
            book.save_task('tx', state)
            with self.assertRaisesRegex(PermissionError, 'terminal delivery policy'):
                agent.run('tx')
            book.close()

    def test_delegated_consumer_rejects_missing_packet_rule(self):
        wrapped = WorkContextModel(ScriptedModel('hello'),
            'Work ID: WORK-1\nOriginal goal: answer a question\nVerified progress JSON: {}')
        with self.assertRaisesRegex(PermissionError, 'terminal delivery policy'):
            wrapped.invoke([{'role': 'system', 'content': 'other policy'}], 7)
        with self.assertRaisesRegex(RuntimeError, 'normal HumanOS system prompt'):
            wrapped.invoke([{'role': 'user', 'content': 'other policy'}], 7)

    def test_delivery_sink_rejects_tampered_saved_answer_without_writing(self):
        runtime = object.__new__(HumanOSRuntime)
        stream = io.StringIO()
        with self.assertRaises(TerminalDeliveryError):
            runtime.deliver('tx', 'Run `python3 scripts/smoke_codex_import.py`.', stream)
        self.assertEqual(stream.getvalue(), '')


if __name__ == '__main__':
    unittest.main()
