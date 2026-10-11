"""Synthetic subprocess journey through the local Notebook command."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from notebook import Notebook


ROOT = Path(__file__).resolve().parents[1]


class NotebookLocalTests(unittest.TestCase):
    def test_capture_reopen_exact_read_and_source_recall(self):
        with tempfile.TemporaryDirectory() as folder:
            vault = Path(folder) / 'vault'

            def run(command, payload):
                argv = [sys.executable, 'notebook_local.py', '--vault', str(vault), command]
                # Sensitive request values are not transmitted through argv.
                self.assertEqual(argv[-1], command)
                return subprocess.run(argv, input=json.dumps(payload, ensure_ascii=False),
                                      cwd=ROOT, text=True, capture_output=True)

            first = run('capture', {
                'owner': 'Synthetic Owner', 'source': 'synthetic-host',
                'conversation_id': 'c1', 'turn_id': 't1',
                'human': 'Original morning summary. 🧭', 'assistant': 'Received original.',
            })
            self.assertEqual(first.returncode, 0, first.stderr)
            receipt = json.loads(first.stdout)
            self.assertEqual(receipt['status'], 'CHECKPOINTED')
            second = run('capture', {
                'owner': 'Synthetic Owner', 'source': 'synthetic-host',
                'conversation_id': 'c1', 'turn_id': 't2', 'hcid': receipt['hcid'],
                'human': 'Correction: detailed morning summary.',
                'assistant': 'Received correction.',
            })
            self.assertEqual(second.returncode, 0, second.stderr)
            corrected = json.loads(second.stdout)
            self.assertNotEqual(receipt['tx'], corrected['tx'])
            for tx, human, assistant in (
                (receipt['tx'], 'Original morning summary. 🧭', 'Received original.'),
                (corrected['tx'], 'Correction: detailed morning summary.', 'Received correction.'),
            ):
                read = run('read', {'owner': 'Synthetic Owner', 'tx': tx})
                self.assertEqual(read.returncode, 0, read.stderr)
                body = json.loads(read.stdout)
                self.assertEqual(body['source'], 'synthetic-host')
                self.assertEqual(body['transcript'], [
                    {'role': 'HUMAN', 'text': human}, {'role': 'ASSISTANT', 'text': assistant}])
            recall = run('recall', {'owner': 'Synthetic Owner', 'query': 'morning summary'})
            self.assertEqual(recall.returncode, 0, recall.stderr)
            results = json.loads(recall.stdout)['results']
            self.assertEqual({row['tx'] for row in results}, {receipt['tx'], corrected['tx']})
            self.assertTrue(all(row['source'] == 'synthetic-host' for row in results))

            absent = run('read', {'owner': 'Synthetic Owner', 'tx': 'absent'})
            other_owner = run('read', {'owner': 'Different Owner', 'tx': receipt['tx']})
            recall_other_owner = run('recall', {'owner': 'Different Owner', 'query': 'morning summary'})
            self.assertEqual(recall_other_owner.returncode, 0, recall_other_owner.stderr)
            self.assertEqual(json.loads(recall_other_owner.stdout)['results'], [])

            book = Notebook(vault)
            try:
                book.set_privacy(receipt['tx'], 0, 'HIDE', confirmation='HIDE')
            finally:
                book.close()
            hidden = run('read', {'owner': 'Synthetic Owner', 'tx': receipt['tx']})
            # Unknown, wrong-owner, and hidden transactions must have identical
            # status, stdout, and stderr: no existence oracle or secret excerpt.
            for denied in (absent, other_owner, hidden):
                self.assertEqual(denied.returncode, 1)
                self.assertEqual(denied.stdout, '')
                self.assertEqual(denied.stderr, 'Notebook operation failed\n')
                self.assertNotIn('Original morning summary', denied.stderr + denied.stdout)

            hidden_recall = run('recall', {'owner': 'Synthetic Owner', 'query': 'Original morning'})
            self.assertEqual(hidden_recall.returncode, 0, hidden_recall.stderr)
            self.assertEqual(json.loads(hidden_recall.stdout)['results'], [])

            wrong_binding = run('capture', {
                'owner': 'Synthetic Owner', 'source': 'synthetic-host',
                'conversation_id': 'c1', 'turn_id': 't3', 'hcid': 'wrong',
                'human': 'Must not append.', 'assistant': 'Must not append.',
            })
            self.assertEqual(wrong_binding.returncode, 1)
            self.assertFalse(wrong_binding.stdout)

    def test_malformed_capture_creates_no_vault(self):
        with tempfile.TemporaryDirectory() as folder:
            vault = Path(folder) / 'vault'
            argv = [sys.executable, 'notebook_local.py', '--vault', str(vault), 'capture']
            base = {
                'owner': 'Synthetic Owner', 'source': 'synthetic-host',
                'conversation_id': 'c1', 'turn_id': 't1',
                'human': 'Would be pending', 'assistant': '  ',
            }
            for malformed in (base, dict(base, assistant=123), ['not-a-request'], {}):
                result = subprocess.run(argv, input=json.dumps(malformed),
                                        cwd=ROOT, text=True, capture_output=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, '')
                self.assertFalse(vault.exists())
            legacy = subprocess.run(argv + ['--human', 'synthetic-private-text'],
                                    input=json.dumps(dict(base, assistant='valid')),
                                    cwd=ROOT, text=True, capture_output=True)
            self.assertNotEqual(legacy.returncode, 0)
            self.assertFalse(vault.exists())


if __name__ == '__main__':
    unittest.main()
