import tempfile
import unittest
from pathlib import Path

from capture_fabric import CaptureEvent, CaptureReceipt, SQLiteRelay
from capture_remote_sync import RemoteCaptureMirror, RemoteSyncError, sync_remote_once
from conversation_transport import CaptureSpool
from notebook import Notebook


class RemoteCaptureSyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.vault = self.root / 'vault'
        self.relay = SQLiteRelay(self.root / 'remote.sqlite3')

    def tearDown(self):
        self.relay.close()
        self.tmp.cleanup()

    def event(self, *, turn='turn-1', event_type='human_message', role='human',
              text='  exact remote text 🧭\nline two  ', variant='primary'):
        return CaptureEvent(
            source='chatgpt',
            conversation_id='conversation-1',
            turn_id=turn,
            event_type=event_type,
            role=role,
            text=text,
            idempotency_key=f'chatgpt/conversation-1/{turn}/{event_type}/{variant}',
            variant_id=variant,
        )

    def test_remote_turn_reaches_canonical_notebook_exactly_once(self):
        self.relay.append(self.event())
        self.relay.append(self.event(
            event_type='assistant_message', role='assistant', text=' assistant exact\n'))

        first = sync_remote_once(self.vault, self.relay.after, 'Jon')
        self.assertEqual(first['pulled_remote_seq'], [1, 2])
        self.assertEqual(first['spooled_remote_seq'], [1, 2])
        self.assertTrue(first['notebook_available'])
        self.assertEqual(first['pending_local_spool'], 0)

        second = sync_remote_once(self.vault, self.relay.after, 'Jon')
        self.assertEqual(second['pulled_remote_seq'], [])
        self.assertEqual(second['spooled_remote_seq'], [])

        book = Notebook(self.vault)
        try:
            rows = list(book.db.execute(
                "SELECT role,text FROM transcript ORDER BY seq"
            ))
            self.assertEqual([(r['role'], r['text']) for r in rows], [
                ('HUMAN', '  exact remote text 🧭\nline two  '),
                ('ASSISTANT', ' assistant exact\n'),
            ])
            self.assertTrue(book.verify())
        finally:
            book.close()

    def test_regeneration_becomes_immutable_variant_turn(self):
        self.relay.append(self.event(text='original prompt'))
        self.relay.append(self.event(
            event_type='assistant_message', role='assistant', text='first answer'))
        self.relay.append(self.event(
            event_type='assistant_regeneration', role='assistant',
            text='alternate answer', variant='alt-2'))

        result = sync_remote_once(self.vault, self.relay.after, 'Jon')
        self.assertEqual(result['pulled_remote_seq'], [1, 2, 3])
        self.assertEqual(result['spooled_remote_seq'], [1, 2, 3])

        book = Notebook(self.vault)
        try:
            rows = list(book.db.execute(
                "SELECT role,text FROM transcript ORDER BY seq"
            ))
            self.assertEqual([(r['role'], r['text']) for r in rows], [
                ('HUMAN', 'original prompt'),
                ('ASSISTANT', 'first answer'),
                ('HUMAN', 'original prompt'),
                ('ASSISTANT', 'alternate answer'),
            ])
            self.assertTrue(book.verify())
        finally:
            book.close()

    def test_human_edit_is_preserved_as_new_half_turn(self):
        self.relay.append(self.event(text='first prompt'))
        self.relay.append(self.event(
            event_type='human_edit', role='human', text='edited prompt', variant='edit-2'))
        result = sync_remote_once(self.vault, self.relay.after, 'Jon')
        self.assertEqual(result['spooled_remote_seq'], [1, 2])

        book = Notebook(self.vault)
        try:
            rows = list(book.db.execute('SELECT role,text FROM transcript ORDER BY seq'))
            self.assertEqual([(r['role'], r['text']) for r in rows], [
                ('HUMAN', 'first prompt'), ('HUMAN', 'edited prompt')
            ])
            self.assertTrue(book.verify())
        finally:
            book.close()

    def test_remote_gap_fails_before_local_commit(self):
        mirror = RemoteCaptureMirror(self.vault)
        event = self.event()
        fake = CaptureReceipt(2, 'event-2', 'a' * 64,
                              '2026-09-14T00:00:00+00:00')
        try:
            with self.assertRaisesRegex(RemoteSyncError, 'gap'):
                mirror.pull(lambda after, limit: [(fake, event)])
            self.assertEqual(mirror.last_remote_seq(), 0)
        finally:
            mirror.close()

    def test_mirror_is_durable_even_when_notebook_writer_is_busy(self):
        self.relay.append(self.event(text='queued while busy'))
        book = Notebook(self.vault)
        try:
            result = sync_remote_once(self.vault, self.relay.after, 'Jon')
            self.assertEqual(result['pulled_remote_seq'], [1])
            self.assertEqual(result['spooled_remote_seq'], [1])
            self.assertFalse(result['notebook_available'])
            self.assertEqual(result['pending_local_spool'], 1)
        finally:
            book.close()

        result = sync_remote_once(self.vault, self.relay.after, 'Jon')
        self.assertTrue(result['notebook_available'])
        self.assertEqual(result['pending_local_spool'], 0)


if __name__ == '__main__':
    unittest.main()
