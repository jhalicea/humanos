"""Output recovery uses isolated vaults; no model or personal records are needed."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from notebook import Notebook


class DeliveryRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self.tmp.name) / 'vault'
        self.book = Notebook(self.vault)
        self.book.recover()
        self.identity = self.book.bind('Jon', 'test opening')

    def tearDown(self):
        self.book.close()
        self.tmp.cleanup()

    def saved_final(self, delivery='PREPARED_NOT_CONFIRMED', checkpoint=True):
        text = '  Exact answer.\r\nCorrection retained. 🧭\n'
        self.book.start(self.identity['hcid'], 'turn', 'Exact human input.\n')
        self.book.append('turn', 1, 'ASSISTANT', text)
        state = {'phase': 'COMPLETE', 'final': text, 'final_ordinal': 1}
        if delivery is not None:
            state['delivery'] = delivery
        self.book.save_task('turn', state)
        if checkpoint:
            self.book.checkpoint('turn')
        return text

    def reopen(self):
        self.book.close()
        self.book = Notebook(self.vault)

    def counts(self):
        return tuple(self.book.db.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
                     for table in ('transcript', 'events', 'recovery'))

    def test_startup_finds_checkpointed_answer_without_output(self):
        final = self.saved_final()
        self.reopen()
        pending = self.book.recover()
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]['tx'], 'turn')
        self.assertEqual(pending[0]['hcid'], self.identity['hcid'])
        self.assertEqual(pending[0]['recovery_kind'], 'DELIVERY')
        self.assertEqual(pending[0]['status'], 'CHECKPOINTED')
        self.assertEqual(self.book.task('turn')['final'], final)
        initial = self.counts()
        fallback = (self.book.root / 'recovery.jsonl').read_bytes()
        self.assertEqual(self.book.recover(), pending)
        self.assertEqual(self.counts(), initial)
        self.assertEqual((self.book.root / 'recovery.jsonl').read_bytes(), fallback)
        self.assertTrue(self.book.verify())

    def test_legacy_final_without_delivery_metadata_is_pending(self):
        self.saved_final(delivery=None)
        self.reopen()
        pending = self.book.recover()
        self.assertEqual(pending[0]['delivery'], 'NOT_CONFIRMED')
        self.assertEqual(self.book.message_count('turn'), 2)

    def test_prepare_validates_exact_final_before_attempt(self):
        final = self.saved_final()
        before = self.counts()
        with self.assertRaisesRegex(RuntimeError, 'differs from preserved'):
            self.book.prepare_delivery('turn', final.strip())
        self.assertEqual(self.counts(), before)
        self.assertEqual(self.book.task('turn')['delivery'], 'PREPARED_NOT_CONFIRMED')

    def test_prepare_requires_checkpoint_readback(self):
        final = self.saved_final(checkpoint=False)
        with self.assertRaisesRegex(RuntimeError, 'checkpoint readback'):
            self.book.prepare_delivery('turn', final)
        self.assertEqual(self.book.task('turn')['delivery'], 'PREPARED_NOT_CONFIRMED')

    def test_crash_during_delivery_is_uncertain_and_retries_exact_final(self):
        final = self.saved_final()
        self.assertTrue(self.book.prepare_delivery('turn', final))
        first_attempt = self.book.task('turn')['delivery_attempt']
        self.assertEqual(self.book.task('turn')['delivery'], 'DELIVERING')
        self.reopen()
        pending = self.book.recover()
        self.assertEqual(pending[0]['delivery'], 'OUTPUT_UNCERTAIN')
        counts = self.counts()
        self.book.recover()
        self.assertEqual(self.counts(), counts)
        self.assertTrue(self.book.prepare_delivery('turn', final))
        self.assertNotEqual(self.book.task('turn')['delivery_attempt'], first_attempt)
        self.assertEqual(self.book.task('turn')['delivery_attempts'], 2)
        self.assertTrue(self.book.finish_delivery('turn'))
        self.assertEqual(self.book.task('turn')['delivery'], 'WRITTEN_TO_OUTPUT_STREAM')
        self.assertEqual(self.book.message_count('turn'), 2)
        self.assertEqual(self.book.recover(), [])
        self.assertTrue(self.book.verify())

    def test_output_failure_retains_checkpoint_and_deduplicates_recovery(self):
        final = self.saved_final()
        self.book.prepare_delivery('turn', final)
        self.book.fail_delivery('turn', OSError('flush failed after partial output'))
        self.assertEqual(self.book.task('turn')['delivery'], 'OUTPUT_UNCERTAIN')
        self.assertEqual(self.book.get_transaction('turn')['status'], 'CHECKPOINTED')
        before = self.counts()
        self.book.fail_delivery('turn', OSError('flush failed after partial output'))
        self.assertEqual(self.counts(), before)
        self.book.checkpoint('turn')
        self.assertEqual(self.book.db.execute(
            "SELECT COUNT(*) FROM recovery WHERE tx='turn' AND scope='DELIVERY' AND closed=0").fetchone()[0], 1)
        self.assertEqual(self.book.message_count('turn'), 2)
        self.assertTrue(self.book.verify())

    def test_output_confirmation_requires_durable_attempt(self):
        self.saved_final()
        with self.assertRaisesRegex(RuntimeError, 'matching durable delivery attempt'):
            self.book.finish_delivery('turn')
        self.assertEqual(self.book.task('turn')['delivery'], 'PREPARED_NOT_CONFIRMED')

    def test_confirmed_output_is_not_delivered_or_logged_twice(self):
        final = self.saved_final()
        self.book.prepare_delivery('turn', final)
        self.book.finish_delivery('turn')
        before = self.counts()
        self.assertFalse(self.book.prepare_delivery('turn', final))
        self.assertFalse(self.book.finish_delivery('turn'))
        self.assertFalse(self.book.fail_delivery('turn', 'late duplicate callback'))
        self.assertEqual(self.counts(), before)
        self.assertEqual(self.book.recover(), [])

    def test_output_confirmation_closes_only_delivery_recovery(self):
        final = self.saved_final()
        self.book.recover()
        with self.book.db:
            self.book.db.execute("INSERT INTO recovery(tx,error,created,scope) VALUES('turn','other issue','test','NOTEBOOK')")
        self.book.prepare_delivery('turn', final)
        self.book.finish_delivery('turn')
        open_scopes = [r[0] for r in self.book.db.execute("SELECT scope FROM recovery WHERE closed=0")]
        self.assertEqual(open_scopes, ['NOTEBOOK'])

    def test_checkpoint_repair_does_not_close_delivery_recovery(self):
        self.saved_final()
        self.book.recover()
        self.book.problem('turn', 'simulated projection problem')
        self.book.checkpoint('turn')
        open_scopes = [r[0] for r in self.book.db.execute("SELECT scope FROM recovery WHERE closed=0")]
        self.assertEqual(open_scopes, ['DELIVERY'])
        self.assertEqual(self.book.get_transaction('turn')['status'], 'CHECKPOINTED')

    def test_attempt_state_and_event_commit_atomically(self):
        final = self.saved_final()
        before = self.counts()
        self.book.db.execute("CREATE TRIGGER fail_event BEFORE INSERT ON events BEGIN SELECT RAISE(ABORT, 'injected event failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.book.prepare_delivery('turn', final)
        self.assertEqual(self.book.task('turn')['delivery'], 'PREPARED_NOT_CONFIRMED')
        self.assertEqual(self.counts(), before)
        self.book.db.execute('DROP TRIGGER fail_event')
        self.assertTrue(self.book.verify())

    def test_delivery_failure_has_independent_fallback_when_database_fails(self):
        final = self.saved_final()
        self.book.prepare_delivery('turn', final)
        self.book.db.execute("CREATE TRIGGER fail_task BEFORE UPDATE ON tasks BEGIN SELECT RAISE(ABORT, 'injected task failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.book.fail_delivery('turn', 'broken output stream')
        fallback = json.loads((self.book.root / 'recovery.jsonl').read_text().splitlines()[-1])
        self.assertEqual(fallback['scope'], 'DELIVERY')
        self.assertEqual(fallback['error'], 'broken output stream')
        self.assertEqual(fallback['payload']['delivery'], 'OUTPUT_UNCERTAIN')
        self.book.db.execute('DROP TRIGGER fail_task')
        self.reopen()
        pending = self.book.recover()[0]
        self.assertEqual(pending['delivery'], 'OUTPUT_UNCERTAIN')
        self.assertEqual(pending['delivery_error'], 'broken output stream')
        self.assertEqual(self.book.get_transaction('turn')['status'], 'CHECKPOINTED')

    def test_legacy_recovery_schema_migrates_without_losing_rows(self):
        self.book.close()
        old_vault = Path(self.tmp.name) / 'legacy-vault'
        root = old_vault / 'runtime'
        root.mkdir(parents=True)
        with sqlite3.connect(str(root / 'notebook.sqlite3')) as db:
            db.execute('CREATE TABLE recovery(id INTEGER PRIMARY KEY AUTOINCREMENT, tx TEXT, error TEXT NOT NULL, closed INTEGER NOT NULL DEFAULT 0, created TEXT NOT NULL)')
            db.execute("INSERT INTO recovery(tx,error,created) VALUES(NULL,'preserve original error','original timestamp')")
        self.book = Notebook(old_vault)
        row = dict(self.book.db.execute('SELECT * FROM recovery').fetchone())
        self.assertEqual(row, {'id': 1, 'tx': None, 'error': 'preserve original error',
                               'closed': 0, 'created': 'original timestamp', 'scope': 'NOTEBOOK'})
        self.book.recover()
        self.assertTrue(self.book.verify())


if __name__ == '__main__':
    unittest.main()
