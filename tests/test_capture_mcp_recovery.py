import os
import subprocess
import sys
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

    def reopen(self):
        self.relay = SQLiteRelay(self.root / 'relay' / 'capture.sqlite3')
        self.book = Notebook(self.root / 'vault')
        self.book.recover()
        self.importer = CaptureImporter(self.book, self.root / 'import-state')

    def crash_child(self, script, exit_code):
        environment = dict(os.environ)
        environment['PYTHONPATH'] = str(Path(__file__).resolve().parents[1])
        result = subprocess.run(
            [sys.executable, '-c', script, str(self.root)],
            env=environment, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, exit_code, result.stderr)

    def test_save_receipt_restart_and_exact_recall(self):
        human = '  human durable proof 🧭\nwith exact spacing  '
        assistant = 'assistant durable proof 🧭\nwith exact spacing '
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
        self.reopen()

        self.assertEqual(self.importer.stage(self.relay.after), 0)
        self.assertEqual(self.importer.drain()['imported'], 0)
        report = search_notebook(self.book, 'Jon', 'recall-request', 'assistant durable proof')
        recalled = next(item for item in report['results'] if item['role'] == 'ASSISTANT')
        self.assertEqual(recalled['excerpt'], assistant)
        self.assertTrue(self.book.verify())

    def test_process_crash_after_staging_recovers_from_durable_inbox(self):
        human = 'human after staged crash'
        assistant = 'assistant after staged crash'
        self.mcp.call_tool('humanos_append_capture_event', {
            'event': self.event(role='human', text=human, event_type='human_message')})
        self.mcp.call_tool('humanos_append_capture_event', {
            'event': self.event(role='assistant', text=assistant, event_type='assistant_message')})
        self.importer.close()
        self.book.close()
        self.relay.close()
        self.crash_child('''
import os, sys
from pathlib import Path
from capture_fabric import SQLiteRelay
from capture_importer import CaptureImporter
from notebook import Notebook
root = Path(sys.argv[1])
relay = SQLiteRelay(root / 'relay' / 'capture.sqlite3')
book = Notebook(root / 'vault')
book.recover()
importer = CaptureImporter(book, root / 'import-state')
assert importer.stage(relay.after) == 2
os._exit(91)
''', 91)
        self.reopen()
        self.assertEqual(self.importer.stage(self.relay.after), 0)
        self.assertEqual(self.importer.drain()['acknowledged_seq'], 2)
        self.assertEqual([(row['role'], row['text']) for row in self.book.db.execute(
            'SELECT role,text FROM transcript ORDER BY seq'
        )], [('HUMAN', human), ('ASSISTANT', assistant)])

    def test_process_crash_after_remote_receipt_before_staging_recovers_exactly(self):
        self.importer.close()
        self.book.close()
        self.relay.close()
        self.crash_child('''
import os, sys
from pathlib import Path
from capture_fabric import CaptureGateway, SQLiteRelay
from capture_mcp_gateway import HumanOSCaptureMCP
root = Path(sys.argv[1])
relay = SQLiteRelay(root / 'relay' / 'capture.sqlite3')
mcp = HumanOSCaptureMCP(CaptureGateway(relay.append))
human = {'version': 1, 'source': 'chatgpt', 'conversation_id': 'receipt-crash', 'turn_id': 'turn-1', 'event_type': 'human_message', 'role': 'human', 'text': 'human after receipt crash', 'idempotency_key': 'receipt-crash/human', 'variant_id': 'primary', 'source_created_at': None}
assistant = dict(human, event_type='assistant_message', role='assistant', text='assistant after receipt crash', idempotency_key='receipt-crash/assistant')
assert mcp.call_tool('humanos_append_capture_event', {'event': human})['state'] == 'REMOTE_CAPTURED'
assert mcp.call_tool('humanos_append_capture_event', {'event': assistant})['state'] == 'REMOTE_CAPTURED'
os._exit(93)
''', 93)
        self.reopen()
        self.assertEqual(self.importer.stage(self.relay.after), 2)
        self.assertEqual(self.importer.drain()['acknowledged_seq'], 2)
        self.assertEqual([(row['role'], row['text']) for row in self.book.db.execute(
            'SELECT role,text FROM transcript ORDER BY seq'
        )], [('HUMAN', 'human after receipt crash'), ('ASSISTANT', 'assistant after receipt crash')])

    def test_process_crash_during_uncommitted_staging_write_leaves_no_false_cursor(self):
        human = 'human after uncommitted stage crash'
        assistant = 'assistant after uncommitted stage crash'
        self.mcp.call_tool('humanos_append_capture_event', {
            'event': self.event(role='human', text=human, event_type='human_message')})
        self.mcp.call_tool('humanos_append_capture_event', {
            'event': self.event(role='assistant', text=assistant, event_type='assistant_message')})
        self.importer.close()
        self.book.close()
        self.relay.close()
        self.crash_child('''
import os, sys
from pathlib import Path
from capture_fabric import SQLiteRelay
from capture_importer import CaptureImporter
from notebook import Notebook
root = Path(sys.argv[1])
relay = SQLiteRelay(root / 'relay' / 'capture.sqlite3')
book = Notebook(root / 'vault')
book.recover()
importer = CaptureImporter(book, root / 'import-state')
importer.db.create_function('crash_after_insert', 0, lambda: os._exit(94))
importer.db.execute('CREATE TEMP TRIGGER crash_uncommitted_stage AFTER INSERT ON inbox BEGIN SELECT crash_after_insert(); END')
importer.stage(relay.after)
''', 94)
        self.reopen()
        self.assertEqual(self.importer.stage(self.relay.after), 2)
        self.assertEqual(self.importer.drain()['acknowledged_seq'], 2)
        self.assertEqual([(row['role'], row['text']) for row in self.book.db.execute(
            'SELECT role,text FROM transcript ORDER BY seq'
        )], [('HUMAN', human), ('ASSISTANT', assistant)])

    def test_process_crash_after_notebook_write_before_acknowledgment_is_idempotent(self):
        human = 'human before acknowledgment crash'
        assistant = 'assistant before acknowledgment crash'
        self.mcp.call_tool('humanos_append_capture_event', {
            'event': self.event(role='human', text=human, event_type='human_message')})
        self.mcp.call_tool('humanos_append_capture_event', {
            'event': self.event(role='assistant', text=assistant, event_type='assistant_message')})
        self.importer.close()
        self.book.close()
        self.relay.close()
        self.crash_child('''
import os, sys
from pathlib import Path
from capture_fabric import SQLiteRelay
from capture_importer import CaptureImporter
from notebook import Notebook
root = Path(sys.argv[1])
relay = SQLiteRelay(root / 'relay' / 'capture.sqlite3')
book = Notebook(root / 'vault')
book.recover()
importer = CaptureImporter(book, root / 'import-state')
assert importer.stage(relay.after) == 2
original = importer._import_event
def crash_after_notebook_write(event):
    transaction = original(event)
    if event.role == 'assistant':
        os._exit(92)
    return transaction
importer._import_event = crash_after_notebook_write
importer.drain()
''', 92)
        self.reopen()
        self.assertEqual(self.importer.stage(self.relay.after), 0)
        self.assertEqual(self.importer.drain()['acknowledged_seq'], 2)
        self.assertEqual([(row['role'], row['text']) for row in self.book.db.execute(
            'SELECT role,text FROM transcript ORDER BY seq'
        )], [('HUMAN', human), ('ASSISTANT', assistant)])

    def test_process_crash_after_partial_notebook_turn_recovers_exactly_once(self):
        human = 'human partial notebook crash'
        assistant = 'assistant partial notebook crash'
        self.mcp.call_tool('humanos_append_capture_event', {
            'event': self.event(role='human', text=human, event_type='human_message')})
        self.mcp.call_tool('humanos_append_capture_event', {
            'event': self.event(role='assistant', text=assistant, event_type='assistant_message')})
        self.importer.close()
        self.book.close()
        self.relay.close()
        self.crash_child('''
import os, sys
from pathlib import Path
from capture_fabric import SQLiteRelay
from capture_importer import CaptureImporter
from notebook import Notebook
root = Path(sys.argv[1])
relay = SQLiteRelay(root / 'relay' / 'capture.sqlite3')
book = Notebook(root / 'vault')
book.recover()
importer = CaptureImporter(book, root / 'import-state')
assert importer.stage(relay.after) == 2
original = importer._import_event
def crash_after_human_write(event):
    transaction = original(event)
    if event.role == 'human':
        os._exit(95)
    return transaction
importer._import_event = crash_after_human_write
importer.drain()
''', 95)
        self.reopen()
        self.assertEqual(self.importer.stage(self.relay.after), 0)
        self.assertEqual(self.importer.drain()['acknowledged_seq'], 2)
        self.assertEqual([(row['role'], row['text']) for row in self.book.db.execute(
            'SELECT role,text FROM transcript ORDER BY seq'
        )], [('HUMAN', human), ('ASSISTANT', assistant)])

    def test_process_restart_after_locked_storage_retries_staged_capture(self):
        human = 'human after locked storage restart'
        assistant = 'assistant after locked storage restart'
        self.mcp.call_tool('humanos_append_capture_event', {
            'event': self.event(role='human', text=human, event_type='human_message')})
        self.mcp.call_tool('humanos_append_capture_event', {
            'event': self.event(role='assistant', text=assistant, event_type='assistant_message')})
        self.importer.close()
        self.book.close()
        self.relay.close()
        self.crash_child('''
import os, sqlite3, sys
from pathlib import Path
from capture_fabric import SQLiteRelay
from capture_importer import CaptureImporter
from notebook import Notebook
root = Path(sys.argv[1])
relay = SQLiteRelay(root / 'relay' / 'capture.sqlite3')
book = Notebook(root / 'vault')
book.recover()
book.db.execute('PRAGMA busy_timeout=1')
importer = CaptureImporter(book, root / 'import-state')
assert importer.stage(relay.after) == 2
blocker = sqlite3.connect(str(book.root / 'notebook.sqlite3'), timeout=0)
blocker.execute('BEGIN EXCLUSIVE')
result = importer.drain()
assert result['retryable_errors'] == 1
os._exit(96)
''', 96)
        self.reopen()
        self.assertEqual(self.importer.stage(self.relay.after), 0)
        self.assertEqual(self.importer.drain()['acknowledged_seq'], 2)
        self.assertEqual([(row['role'], row['text']) for row in self.book.db.execute(
            'SELECT role,text FROM transcript ORDER BY seq'
        )], [('HUMAN', human), ('ASSISTANT', assistant)])


if __name__ == '__main__':
    unittest.main()
