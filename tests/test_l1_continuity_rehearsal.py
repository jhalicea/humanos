"""One synthetic user journey across capture, restart, and encrypted restore."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conversation_capture import UniversalConversationCapture
from notebook import Notebook
from vault_encryption import (EncryptedBackupError, create_encrypted_backup,
                              restore_encrypted_backup)


class L1ContinuityRehearsal(unittest.TestCase):
    def test_source_turns_survive_restart_and_encrypted_restore(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / 'source'
            passphrase = 'synthetic rehearsal passphrase only'
            original = 'I prefer concise morning summaries. 🧭'
            correction = 'Correction: I prefer detailed morning summaries.'
            replies = ('I heard the concise preference.', 'I heard the correction.')

            book = Notebook(source)
            try:
                owner = book.bind('Synthetic Owner', 'synthetic opening')['hcid']
                capture = UniversalConversationCapture(book, 'synthetic-host')
                first = capture.capture_turn(owner, 'conversation-1', 'turn-1', original, replies[0])
                second = capture.capture_turn(owner, 'conversation-1', 'turn-2', correction, replies[1])
                self.assertTrue(book.verify())
            finally:
                book.close()

            # A new interpreter opens the vault, checks source evidence and exact
            # rows, and performs bounded historical recall. No model runs.
            probe = '''
import json, sys
from notebook import Notebook
from notebook_recall import search_notebook
vault, first, second = sys.argv[1:]
book = Notebook(vault)
try:
    book.recover()
    assert book.verify()
    expected = json.loads(sys.stdin.read())
    for tx, pair in zip((first, second), expected):
        assert book.get_transaction(tx)['status'] == 'CHECKPOINTED'
        assert book.task(tx)['source'] == 'synthetic-host'
        rows = [(r['role'], r['text']) for r in book.db.execute(
            'SELECT role,text FROM transcript WHERE tx=? ORDER BY ordinal', (tx,))]
        assert rows == [('HUMAN', pair[0]), ('ASSISTANT', pair[1])]
    report = search_notebook(book, 'Synthetic Owner', 'current', 'morning summaries')
    assert report['provenance'] == 'LOCAL_AUTHORITATIVE_NOTEBOOK_TRANSCRIPT'
    assert {r['tx'] for r in report['results']} == {first, second}
    assert all(len(r['excerpt']) <= 400 for r in report['results'])
finally:
    book.close()
'''

            def check(vault):
                result = subprocess.run(
                    [sys.executable, '-c', probe, str(vault), first, second],
                    input=json.dumps([[original, replies[0]], [correction, replies[1]]]),
                    text=True, capture_output=True, cwd=Path(__file__).resolve().parents[1])
                self.assertEqual(result.returncode, 0, result.stderr)

            check(source)
            encrypted = root / 'notebook.hosenc'
            receipt = create_encrypted_backup(source, encrypted, passphrase)
            self.assertTrue(receipt['staged_restore_verified'])
            self.assertNotIn(original.encode(), encrypted.read_bytes())
            self.assertNotIn(correction.encode(), encrypted.read_bytes())

            rejected = root / 'rejected'
            with self.assertRaises(EncryptedBackupError):
                restore_encrypted_backup(encrypted, rejected, 'wrong passphrase')
            self.assertFalse(rejected.exists())

            restored = root / 'restored'
            self.assertTrue(restore_encrypted_backup(encrypted, restored, passphrase)['restored'])
            check(restored)


if __name__ == '__main__':
    unittest.main()
