import tempfile
import unittest
from pathlib import Path

from capture_fabric import CaptureGateway, SQLiteRelay
from capture_importer import CaptureImporter
from capture_mcp_gateway import HumanOSCaptureMCP
from notebook import Notebook
from notebook_recall import search_notebook


class CaptureMCPRecoveryTests(unittest.TestCase):
    """Prove the transport-neutral MCP writer survives local restart and recall."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.relay = SQLiteRelay(self.root / 'relay' / 'capture.sqlite3')
        self.mcp = HumanOSCaptureMCP(CaptureGateway(self.relay.append))
        self.book = Notebook(self.root / 'vault')
        self.book.recover()
        self.importer = CaptureImporter(self.book, self.root / 'import-state')

    def tearDown(self):
        self.importer.close()
        self.book.close()
        self.relay.close()
        self.tmp.cleanup()

    def event(self, *, role, text, event_type, turn_id='turn-proof'):
        return {
            'version': 1,
            'source': 'chatgpt',
            'conversation_id': 'conversation-proof',
            'turn_id': turn_id,
            'event_type': event_type,
            'role': role,
            'text': text,
            'idempotency_key': f'chatgpt/conversation-proof/{turn_id}/{role}/primary',
            'variant_id': 'primary',
            'source_created_at': '2026-09-15T12:00:00Z',
        }

    def test_save_receipt_restart_and_exact_recall(self):
        human = '  human durable proof 🧭\\nwith exact spacing  '
        assistant = 'assistant durable proof 🧭\\nwith exact spacing '
        human_event = self.event(role='human', text=human, event_type='human_message')
        assistant_event = self.event(role='assistant', text=assistant, event_type='assistant_message')

        human_receipt = self.mcp.call_tool('humanos_append_capture_event', {'event': human_event})
        self.assertEqual(human_receipt['state'], 'REMOTE_CAPTURED')
        self.assertEqual(
            self.mcp.call_tool('humanos_append_capture_event', {'event': human_event}),
            human_receipt,
        )
        assistant_receipt = self.mcp.call_tool('humanos_append_capture_event', {'event': assistant_event})
        self.assertEqual(assistant_receipt['state'], 'REMOTE_CAPTURED')
        self.assertEqual(self.relay.db.execute('SELECT COUNT(*) FROM capture_events').fetchone()[0], 2)

        self.assertEqual(self.importer.stage(self.relay.after), 2)
        self.assertEqual(self.importer.drain()['acknowledged_seq'], 2)
        self.assertTrue(self.book.verify())

        self.importer.close()
        self.book.close()
        self.relay.close()
        self.relay = SQLiteRelay(self.root / 'relay' / 'capture.sqlite3')
        self.book = Notebook(self.root / 'vault')
        self.book.recover()
        self.importer = CaptureImporter(self.book, self.root / 'import-state')

        self.assertEqual(self.importer.stage(self.relay.after), 0)
        self.assertEqual(self.importer.drain()['imported'], 0)
        report = search_notebook(self.book, 'Jon', 'recall-request', 'assistant durable proof')
        recalled = next(item for item in report['results'] if item['role'] == 'ASSISTANT')
        self.assertEqual(recalled['excerpt'], assistant)
        self.assertTrue(self.book.verify())


if __name__ == '__main__':
    unittest.main()
