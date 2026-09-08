"""Failed execution can finish transcript capture without erasing its failure."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from notebook import BindingConflict, Notebook


class FailureCloseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self.tmp.name) / 'vault'
        self.book = Notebook(self.vault)
        self.book.recover()
        self.identity = self.book.bind('Jon', 'first input')
        self.human = '  Read missing.txt.\r\nKeep this correction. 🧭\n'
        self.final = '  I could not read missing.txt.\r\nYou can continue chatting. 🧭\n'
        self.book.start(self.identity['hcid'], 'failed', self.human)
        self.original = {'phase': 'MODEL', 'steps': 6, 'elapsed': 1.25,
                         'model': 'test', 'workspace': str(Path(self.tmp.name) / 'workspace'),
                         'permissions': {'read_paths': ['missing.txt']},
                         'messages': [{'role': 'user', 'content': self.human}]}
        self.book.save_task('failed', self.original)

    def tearDown(self):
        self.book.close()
        self.tmp.cleanup()

    def reopen(self):
        self.book.close()
        self.book = Notebook(self.vault)

    def task_recovery(self):
        return [dict(r) for r in self.book.db.execute("SELECT * FROM recovery WHERE tx='failed' AND scope='TASK'")]

    def test_exact_failure_capture_preserves_history_and_allows_next_turn(self):
        self.book.problem('failed', 'Task iteration budget exhausted')
        self.assertEqual(self.book.finalize_failure('failed', self.final, 'iteration limit'), self.final)
        rows = list(self.book.db.execute("SELECT role,text FROM transcript WHERE tx='failed' ORDER BY ordinal"))
        self.assertEqual([(r['role'], r['text']) for r in rows], [('HUMAN', self.human), ('ASSISTANT', self.final)])
        state = self.book.task('failed')
        self.assertEqual(state['phase'], 'COMPLETE')
        self.assertEqual(state['outcome'], 'FAILED')
        self.assertEqual(state['failure_snapshot'], self.original)
        self.assertEqual(state['permissions'], self.original['permissions'])
        self.assertEqual(state['delivery'], 'PREPARED_NOT_CONFIRMED')
        self.assertEqual(self.book.get_transaction('failed')['status'], 'CHECKPOINTED')
        self.assertEqual(self.task_recovery()[0]['closed'], 0)
        self.assertTrue(self.book.verify())
        self.book.start(self.identity['hcid'], 'next', 'Continue with another question')
        self.assertEqual(self.book.get_transaction('next')['status'], 'STARTED')

    def test_failure_and_delivery_recovery_remain_separate(self):
        self.book.finalize_failure('failed', self.final, 'iteration limit')
        self.book.recover()
        self.assertTrue(self.book.prepare_delivery('failed', self.final))
        self.book.finish_delivery('failed')
        self.book.checkpoint('failed')
        self.assertEqual(self.task_recovery()[0]['closed'], 0)
        self.assertEqual(self.book.db.execute("SELECT COUNT(*) FROM recovery WHERE scope='DELIVERY' AND closed=0").fetchone()[0], 0)
        self.assertEqual(self.book.task('failed')['outcome'], 'FAILED')

    def test_restart_and_repeated_closure_reuse_exact_original_final(self):
        self.book.finalize_failure('failed', self.final, 'first reason')
        before = self.book.db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
        self.reopen()
        self.assertEqual(self.book.finalize_failure('failed', 'A different proposed message', 'new reason'), self.final)
        self.assertEqual(self.book.message_count('failed'), 2)
        self.assertEqual(len(self.task_recovery()), 1)
        self.assertEqual(self.book.task('failed')['failure_reason'], 'first reason')
        self.assertEqual(self.book.db.execute('SELECT COUNT(*) FROM events').fetchone()[0], before)

    def test_interrupted_write_preserves_unknown_outcome_for_inspection(self):
        pending = {'name': 'create_file', 'path': 'report.txt', 'content': 'content'}
        self.original.update(phase='EXECUTING', pending=pending, approvals=['exact approval evidence'])
        self.book.save_task('failed', self.original)
        self.book.finalize_failure('failed', self.final, 'Interrupted write')
        state = self.book.task('failed')
        self.assertEqual(state['outcome'], 'NEEDS_RECONCILIATION')
        self.assertEqual(state['failure_snapshot'], self.original)
        self.assertEqual(state['pending'], pending)
        self.assertEqual(state['approvals'], ['exact approval evidence'])
        self.assertFalse((Path(self.original['workspace']) / 'report.txt').exists())
        self.reopen()
        self.book.recover()
        self.assertEqual(self.book.task('failed')['phase'], 'COMPLETE')
        self.assertEqual(self.book.task('failed')['outcome'], 'NEEDS_RECONCILIATION')
        self.assertEqual(self.task_recovery()[0]['closed'], 0)

    def test_unknown_interrupted_tool_also_requires_reconciliation(self):
        self.original.update(phase='EXECUTING', pending={'name': 'legacy_move'})
        self.book.save_task('failed', self.original)
        self.book.finalize_failure('failed', self.final, 'Unknown interrupted operation')
        self.assertEqual(self.book.task('failed')['outcome'], 'NEEDS_RECONCILIATION')

    def test_interrupted_read_is_a_failed_task_without_unknown_write(self):
        self.original.update(phase='EXECUTING', pending={'name': 'read_file', 'path': 'missing.txt'})
        self.book.save_task('failed', self.original)
        self.book.finalize_failure('failed', self.final, 'Read interrupted')
        self.assertEqual(self.book.task('failed')['outcome'], 'FAILED')

    def test_atomic_closure_rolls_back_on_audit_failure(self):
        self.book.db.execute("CREATE TRIGGER reject_close BEFORE INSERT ON events WHEN NEW.kind='TASK_FAILURE_FINALIZED' BEGIN SELECT RAISE(ABORT, 'injected audit failure'); END")
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'injected audit failure'):
            self.book.finalize_failure('failed', self.final, 'iteration limit')
        self.assertEqual(self.book.message_count('failed'), 1)
        self.assertEqual(self.book.task('failed'), self.original)
        self.assertEqual(self.task_recovery(), [])
        fallback = json.loads((self.book.root / 'recovery.jsonl').read_text().splitlines()[-1])
        self.assertEqual(fallback['payload']['failure_final'], self.final)
        self.assertEqual(self.book.get_transaction('failed')['status'], 'RECOVERY_REQUIRED')
        self.book.db.execute('DROP TRIGGER reject_close')
        self.book.finalize_failure('failed', self.final, 'iteration limit')
        self.assertEqual(self.book.message_count('failed'), 2)
        self.assertEqual(len(self.task_recovery()), 1)

    def test_checkpoint_failure_recovers_complete_capture_without_duplicate_final(self):
        with patch.object(self.book, 'write_projection', side_effect=OSError('injected disk failure')):
            with self.assertRaisesRegex(OSError, 'injected disk failure'):
                self.book.finalize_failure('failed', self.final, 'iteration limit')
        self.assertEqual(self.book.task('failed')['phase'], 'COMPLETE')
        self.assertEqual(self.book.get_transaction('failed')['status'], 'RECOVERY_REQUIRED')
        self.assertEqual(self.book.message_count('failed'), 2)
        self.reopen()
        self.book.recover()
        self.assertEqual(self.book.finalize_failure('failed', 'Must not replace original', 'retry'), self.final)
        self.assertEqual(self.book.message_count('failed'), 2)
        self.assertEqual(self.book.get_transaction('failed')['status'], 'CHECKPOINTED')
        self.assertEqual(len(self.task_recovery()), 1)
        self.assertEqual(self.task_recovery()[0]['closed'], 0)
        self.assertTrue(self.book.verify())

    def test_finalization_reuses_prepared_final_ordinal(self):
        self.original.update(phase='FINAL', final='Uncaptured draft', final_ordinal=1)
        self.book.save_task('failed', self.original)
        self.book.finalize_failure('failed', self.final, 'Draft could not complete')
        self.assertEqual(self.book.task('failed')['final_ordinal'], 1)
        self.assertEqual(self.book.task('failed')['failure_snapshot']['final'], 'Uncaptured draft')
        self.assertEqual(self.book.message_count('failed'), 2)

    def test_existing_different_final_evidence_is_never_overwritten(self):
        self.original.update(phase='FINAL', final='Original final', final_ordinal=1)
        self.book.save_task('failed', self.original)
        self.book.append('failed', 1, 'ASSISTANT', 'Original final')
        with self.assertRaisesRegex(ValueError, 'collides'):
            self.book.finalize_failure('failed', self.final, 'failure')
        self.assertEqual(self.book.task('failed'), self.original)
        self.assertEqual(self.book.message_count('failed'), 2)
        self.assertEqual(self.task_recovery(), [])

    def test_completed_success_is_never_converted_to_failure(self):
        self.book.append('failed', 1, 'ASSISTANT', 'Successful answer')
        self.book.save_task('failed', dict(self.original, phase='COMPLETE', final='Successful answer', final_ordinal=1))
        self.book.checkpoint('failed')
        with self.assertRaisesRegex(ValueError, 'immutable'):
            self.book.finalize_failure('failed', self.final, 'failure')
        self.assertEqual(self.book.task('failed')['final'], 'Successful answer')
        self.assertEqual(self.book.get_transaction('failed')['status'], 'CHECKPOINTED')
        self.assertEqual(self.task_recovery(), [])

    def test_missing_task_state_still_preserves_failed_initialization_input(self):
        self.book.db.execute("DELETE FROM tasks WHERE tx='failed'")
        self.book.db.commit()
        self.book.finalize_failure('failed', self.final, 'Context loading failed')
        self.assertEqual(self.book.task('failed')['failure_snapshot'], {})
        self.assertEqual(self.book.task('failed')['outcome'], 'FAILED')
        self.assertTrue(self.book.verify())

    def test_unverified_binding_and_external_capture_fail_closed(self):
        self.original['phase'] = 'EXTERNAL_CAPTURE_PENDING'
        self.book.save_task('failed', self.original)
        with self.assertRaisesRegex(RuntimeError, 'host reconciliation'):
            self.book.finalize_failure('failed', self.final, 'external failure')
        self.book.db.execute("UPDATE identities SET binding='RECONCILIATION_REQUIRED'")
        self.book.db.commit()
        with self.assertRaises(BindingConflict):
            self.book.finalize_failure('failed', self.final, 'binding failure')
        self.assertEqual(self.book.message_count('failed'), 1)
        self.assertEqual(self.task_recovery(), [])


if __name__ == '__main__':
    unittest.main()
