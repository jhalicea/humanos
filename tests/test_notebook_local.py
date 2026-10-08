"""Synthetic subprocess journey through the local Notebook command."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class NotebookLocalTests(unittest.TestCase):
    def test_capture_reopen_exact_read_and_source_recall(self):
        with tempfile.TemporaryDirectory() as folder:
            vault = Path(folder) / 'vault'

            def run(*args):
                return subprocess.run([sys.executable, 'notebook_local.py', '--vault', str(vault), *args],
                                      cwd=ROOT, text=True, capture_output=True)

            first = run('capture', '--owner', 'Synthetic Owner', '--source', 'synthetic-host',
                        '--conversation-id', 'c1', '--turn-id', 't1',
                        '--human', 'Original morning summary. 🧭', '--assistant', 'Received original.')
            self.assertEqual(first.returncode, 0, first.stderr)
            receipt = json.loads(first.stdout)
            self.assertEqual(receipt['status'], 'CHECKPOINTED')
            second = run('capture', '--owner', 'Synthetic Owner', '--source', 'synthetic-host',
                         '--conversation-id', 'c1', '--turn-id', 't2', '--hcid', receipt['hcid'],
                         '--human', 'Correction: detailed morning summary.',
                         '--assistant', 'Received correction.')
            self.assertEqual(second.returncode, 0, second.stderr)
            corrected = json.loads(second.stdout)
            self.assertNotEqual(receipt['tx'], corrected['tx'])
            for tx, human, assistant in (
                (receipt['tx'], 'Original morning summary. 🧭', 'Received original.'),
                (corrected['tx'], 'Correction: detailed morning summary.', 'Received correction.'),
            ):
                read = run('read', '--tx', tx)
                self.assertEqual(read.returncode, 0, read.stderr)
                body = json.loads(read.stdout)
                self.assertEqual(body['source'], 'synthetic-host')
                self.assertEqual(body['transcript'], [
                    {'role': 'HUMAN', 'text': human}, {'role': 'ASSISTANT', 'text': assistant}])
            recall = run('recall', '--owner', 'Synthetic Owner', '--query', 'morning summary')
            self.assertEqual(recall.returncode, 0, recall.stderr)
            results = json.loads(recall.stdout)['results']
            self.assertEqual({row['tx'] for row in results}, {receipt['tx'], corrected['tx']})
            self.assertTrue(all(row['source'] == 'synthetic-host' for row in results))
            absent = run('read', '--tx', 'absent')
            self.assertEqual(absent.returncode, 1)
            self.assertFalse(absent.stdout)
            wrong_binding = run('capture', '--owner', 'Synthetic Owner', '--source', 'synthetic-host',
                                '--conversation-id', 'c1', '--turn-id', 't3', '--hcid', 'wrong',
                                '--human', 'Must not append.', '--assistant', 'Must not append.')
            self.assertEqual(wrong_binding.returncode, 1)
            self.assertFalse(wrong_binding.stdout)


if __name__ == '__main__':
    unittest.main()
