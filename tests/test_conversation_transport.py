import tempfile
import unittest
from pathlib import Path

from conversation_transport import CaptureDaemon, CaptureSpool, CaptureIngestor, try_ingest
from notebook import Notebook


class ConversationTransportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.vault = self.root / 'vault'
        self.spool = CaptureSpool(self.vault)

    def tearDown(self):
        self.spool.close()
        self.tmp.cleanup()

    def test_spool_preserves_exact_text_and_retry_is_idempotent(self):
        text = '  exact visible text 🧭\nline two  '
        first = self.spool.append('chatgpt', 'conversation-1', 'turn-1', 'human', text)
        second = self.spool.append('chatgpt', 'conversation-1', 'turn-1', 'human', text)
        self.assertEqual(first['event_id'], second['event_id'])
        self.assertEqual(first['seq'], second['seq'])
        row = self.spool.db.execute('SELECT text FROM events WHERE event_id=?',
                                    (first['event_id'],)).fetchone()
        self.assertEqual(row['text'], text)
        self.assertEqual(self.spool.db.execute('SELECT COUNT(*) FROM events').fetchone()[0], 1)

    def test_conflicting_retry_fails_closed(self):
        self.spool.append('chatgpt', 'conversation-1', 'turn-1', 'human', 'first')
        with self.assertRaises(ValueError):
            self.spool.append('chatgpt', 'conversation-1', 'turn-1', 'human', 'changed')

    def test_ingestor_moves_complete_turn_into_life_notebook(self):
        human = self.spool.append('chatgpt', 'conversation-1', 'turn-1', 'human', ' hello ')
        assistant = self.spool.append('chatgpt', 'conversation-1', 'turn-1', 'assistant', ' world\n')
        book = Notebook(self.vault)
        try:
            book.recover()
            ingested = CaptureIngestor(book, self.spool, 'Jon').ingest_pending()
            self.assertEqual(ingested, [human['event_id'], assistant['event_id']])
            human_receipt = self.spool.receipt(human['event_id'])
            assistant_receipt = self.spool.receipt(assistant['event_id'])
            self.assertEqual(human_receipt['tx'], assistant_receipt['tx'])
            rows = list(book.db.execute(
                'SELECT role,text FROM transcript WHERE tx=? ORDER BY ordinal',
                (human_receipt['tx'],)))
            self.assertEqual([(row['role'], row['text']) for row in rows],
                             [('HUMAN', ' hello '), ('ASSISTANT', ' world\n')])
            self.assertEqual(book.get_transaction(human_receipt['tx'])['status'], 'CHECKPOINTED')
            self.assertTrue(book.verify())
        finally:
            book.close()

    def test_spool_remains_available_while_notebook_writer_is_locked(self):
        book = Notebook(self.vault)
        try:
            event = self.spool.append('chatgpt', 'conversation-1', 'turn-1', 'human', 'queued')
            self.assertFalse(try_ingest(self.vault, self.spool, 'Jon'))
            self.assertIsNone(self.spool.receipt(event['event_id']))
            self.assertEqual(len(self.spool.pending()), 1)
        finally:
            book.close()
        self.assertTrue(try_ingest(self.vault, self.spool, 'Jon'))
        self.assertIsNotNone(self.spool.receipt(event['event_id']))

    def test_daemon_authentication_rejects_unsigned_payload(self):
        daemon = CaptureDaemon(self.vault, self.root / 'capture.sock')
        try:
            with self.assertRaises(PermissionError):
                daemon._authenticate({'request': {
                    'version': 1, 'source': 'chatgpt', 'conversation_id': 'c',
                    'turn_id': 't', 'role': 'human', 'text': 'hello'}, 'mac': 'bad'})
        finally:
            daemon.spool.close()


if __name__ == '__main__':
    unittest.main()
