import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from notebook import Notebook
from recovery_ledger import RecoveryLedgerCorrupt, parse_recovery_file


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True).encode('utf-8')


class RecoveryLedgerParserTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.path = self.root / 'recovery.jsonl'

    def tearDown(self):
        self.tmp.cleanup()

    def record(self, marker='one'):
        return encoded({'tx': marker, 'error': 'retained', 'payload': {'marker': marker}, 'created': 'time'})

    def quarantine_dirs(self):
        root = self.root / 'recovery-quarantine'
        if not root.exists():
            return []
        return sorted(path for path in root.iterdir() if path.is_dir() and not path.name.startswith('.'))

    def test_physical_lf_parser_preserves_literal_unicode_line_separator(self):
        record = {'tx': 'unicode', 'error': 'retained',
                  'payload': {'marker': 'before\u2028after\u2029done'}, 'created': 'time'}
        self.path.write_bytes(encoded(record) + b'\n')
        result = parse_recovery_file(self.path)
        self.assertEqual(result.records, (record,))
        self.assertIsNone(result.quarantine)

    def test_malformed_middle_record_fails_closed_without_mutation_or_quarantine(self):
        raw = self.record('first') + b'\nnot-json\n' + self.record('third') + b'\n'
        self.path.write_bytes(raw)
        with self.assertRaisesRegex(RecoveryLedgerCorrupt, 'malformed JSON'):
            parse_recovery_file(self.path)
        self.assertEqual(self.path.read_bytes(), raw)
        self.assertFalse((self.root / 'recovery-quarantine').exists())

    def test_blank_middle_record_fails_closed(self):
        raw = self.record('first') + b'\n\n' + self.record('third') + b'\n'
        self.path.write_bytes(raw)
        with self.assertRaisesRegex(RecoveryLedgerCorrupt, 'blank complete record'):
            parse_recovery_file(self.path)
        self.assertEqual(self.path.read_bytes(), raw)

    def test_truncated_final_tail_is_preserved_without_rewriting_source(self):
        prefix = self.record('first') + b'\n'
        tail = b'{"tx":"broken"'
        raw = prefix + tail
        self.path.write_bytes(raw)
        result = parse_recovery_file(self.path)
        self.assertEqual(len(result.records), 1)
        self.assertEqual(self.path.read_bytes(), raw)
        self.assertEqual(result.quarantine['tail_offset_bytes'], len(prefix))
        self.assertEqual(result.quarantine['tail_length_bytes'], len(tail))
        self.assertEqual(result.quarantine['tail_sha256'], hashlib.sha256(tail).hexdigest())
        folder = self.quarantine_dirs()[0]
        self.assertEqual((folder / 'tail.bin').read_bytes(), tail)

    def test_invalid_utf8_final_tail_is_preserved(self):
        prefix = self.record('first') + b'\n'
        tail = b'\xe2\x82'
        self.path.write_bytes(prefix + tail)
        result = parse_recovery_file(self.path)
        self.assertEqual(result.quarantine['classification'], 'INVALID_UTF8_FINAL_TAIL')
        self.assertEqual(self.quarantine_dirs()[0].joinpath('tail.bin').read_bytes(), tail)

    def test_garbage_after_valid_object_in_final_tail_is_quarantined(self):
        tail = b'{"tx":"x"}garbage'
        self.path.write_bytes(tail)
        result = parse_recovery_file(self.path)
        self.assertEqual(result.records, ())
        self.assertEqual(result.quarantine['classification'], 'MALFORMED_JSON_FINAL_TAIL')
        self.assertEqual(self.path.read_bytes(), tail)

    def test_valid_unterminated_final_object_is_accepted_as_anomaly(self):
        record = {'tx': 'tail', 'error': 'retained', 'payload': None, 'created': 'time'}
        raw = encoded(record)
        self.path.write_bytes(raw)
        result = parse_recovery_file(self.path)
        self.assertEqual(result.records, (record,))
        self.assertEqual(result.anomaly['classification'], 'VALID_UNTERMINATED_FINAL_RECORD')
        self.assertIsNone(result.quarantine)
        self.assertEqual(self.path.read_bytes(), raw)

    def test_quarantine_is_idempotent_for_same_offset_and_bytes(self):
        prefix = self.record('first') + b'\n'
        tail = b'{"broken":'
        raw = prefix + tail
        self.path.write_bytes(raw)
        first = parse_recovery_file(self.path)
        second = parse_recovery_file(self.path)
        self.assertEqual(first.quarantine['tail_sha256'], second.quarantine['tail_sha256'])
        self.assertEqual(len(self.quarantine_dirs()), 1)
        self.assertEqual(self.path.read_bytes(), raw)


class NotebookRecoveryTailIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self.tmp.name) / 'vault'
        self.book = Notebook(self.vault)
        self.identity = self.book.bind('Jon', 'opening')
        self.fallback = self.book.root / 'recovery.jsonl'

    def tearDown(self):
        self.book.close()
        self.tmp.cleanup()

    def fallback_record(self, tx, text):
        return encoded({
            'tx': tx,
            'error': 'retained fallback',
            'payload': {'hcid': self.identity['hcid'], 'role': 'HUMAN', 'text': text},
            'created': 'time',
        })

    def event_count(self, kind):
        return self.book.db.execute('SELECT COUNT(*) FROM events WHERE kind=?', (kind,)).fetchone()[0]

    def test_valid_prefix_recovers_once_while_final_crash_tail_remains_untouched(self):
        prefix = self.fallback_record('fallback-tx', 'preserved exact input') + b'\n'
        tail = b'{"tx":"torn"'
        raw = prefix + tail
        self.fallback.write_bytes(raw)

        self.book.recover()
        self.assertEqual(self.book.get_transaction('fallback-tx')['input'], 'preserved exact input')
        self.assertEqual(self.book.message_count('fallback-tx'), 1)
        self.assertEqual(self.event_count('FALLBACK_INPUT_RECOVERED'), 1)
        self.assertEqual(self.event_count('RECOVERY_CRASH_TAIL_QUARANTINED'), 1)
        self.assertEqual(self.fallback.read_bytes(), raw)

        self.book.recover()
        self.assertEqual(self.book.message_count('fallback-tx'), 1)
        self.assertEqual(self.event_count('FALLBACK_INPUT_RECOVERED'), 1)
        self.assertEqual(self.event_count('RECOVERY_CRASH_TAIL_QUARANTINED'), 1)
        quarantine = self.book.root / 'recovery-quarantine'
        self.assertEqual(len([p for p in quarantine.iterdir() if p.is_dir() and not p.name.startswith('.')]), 1)
        self.assertEqual(self.fallback.read_bytes(), raw)

    def test_valid_unterminated_record_is_consumed_once_and_anomaly_is_deduplicated(self):
        raw = self.fallback_record('unterminated-tx', 'valid without newline')
        self.fallback.write_bytes(raw)
        self.book.recover()
        self.assertEqual(self.book.get_transaction('unterminated-tx')['input'], 'valid without newline')
        self.assertEqual(self.event_count('RECOVERY_UNTERMINATED_RECORD'), 1)
        self.book.recover()
        self.assertEqual(self.book.message_count('unterminated-tx'), 1)
        self.assertEqual(self.event_count('RECOVERY_UNTERMINATED_RECORD'), 1)
        self.assertEqual(self.fallback.read_bytes(), raw)

    def test_middle_corruption_aborts_before_valid_prefix_is_applied(self):
        raw = (self.fallback_record('must-not-run', 'valid prefix') + b'\nnot-json\n'
               + self.fallback_record('later', 'later') + b'\n')
        self.fallback.write_bytes(raw)
        with self.assertRaisesRegex(RecoveryLedgerCorrupt, 'malformed JSON'):
            self.book.recover()
        self.assertIsNone(self.book.get_transaction('must-not-run'))
        self.assertIsNone(self.book.get_transaction('later'))
        self.assertEqual(self.fallback.read_bytes(), raw)


class RecoveryLedgerAppendBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self.tmp.name) / 'vault'
        self.book = Notebook(self.vault)
        self.fallback = self.book.root / 'recovery.jsonl'

    def tearDown(self):
        self.book.close()
        self.tmp.cleanup()

    def test_problem_refuses_to_append_after_unterminated_tail_without_mutation(self):
        raw = b'{"tx":"torn"'
        self.fallback.write_bytes(raw)
        with self.assertRaisesRegex(RuntimeError, 'unterminated physical record'):
            self.book.problem(None, 'later failure')
        self.assertEqual(self.fallback.read_bytes(), raw)
        self.assertEqual(self.book.db.execute('SELECT COUNT(*) FROM recovery').fetchone()[0], 0)

    def test_recovery_writer_appends_exact_physical_lf_record(self):
        self.book.problem(None, 'unicode separator \u2028 retained')
        raw = self.fallback.read_bytes()
        self.assertTrue(raw.endswith(b'\n'))
        self.assertEqual(raw.count(b'\n'), 1)
        parsed = parse_recovery_file(self.fallback)
        self.assertEqual(len(parsed.records), 1)
        self.assertIn('\u2028', parsed.records[0]['error'])


class RecoveryDeliveryReviewRegressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self.tmp.name) / 'vault'
        self.book = Notebook(self.vault)
        self.identity = self.book.bind('Jon', 'opening')
        self.fallback = self.book.root / 'recovery.jsonl'

    def tearDown(self):
        self.book.close()
        self.tmp.cleanup()

    def prepare_delivery(self, tx='delivery-tx'):
        final = 'saved final'
        self.book.start(self.identity['hcid'], tx, 'human input')
        self.book.append(tx, 1, 'ASSISTANT', final)
        self.book.save_task(tx, {
            'phase': 'COMPLETE', 'final': final, 'final_ordinal': 1,
            'delivery': 'PREPARED_NOT_CONFIRMED',
        })
        self.book.checkpoint(tx)
        self.assertTrue(self.book.prepare_delivery(tx, final))
        return self.book.task(tx)['delivery_attempt']

    def delivery_record(self, tx, attempt, error, delivery='OUTPUT_UNCERTAIN'):
        return encoded({
            'tx': tx, 'scope': 'DELIVERY', 'error': error,
            'payload': {'delivery': delivery, 'attempt': attempt}, 'created': 'time',
        })

    def test_matching_unterminated_delivery_evidence_recovers_without_reappend(self):
        attempt = self.prepare_delivery()
        raw = self.delivery_record('delivery-tx', attempt, 'specific output failure')
        self.fallback.write_bytes(raw)

        self.book.recover()
        state = self.book.task('delivery-tx')
        self.assertEqual(state['delivery'], 'OUTPUT_UNCERTAIN')
        self.assertEqual(state['delivery_error'], 'specific output failure')
        self.assertEqual(self.fallback.read_bytes(), raw)

        self.book.recover()
        self.assertEqual(self.book.task('delivery-tx')['delivery_error'], 'specific output failure')
        self.assertEqual(self.fallback.read_bytes(), raw)

    def test_delivery_fallback_is_selected_by_tx_and_attempt(self):
        attempt = self.prepare_delivery()
        matching = self.delivery_record('delivery-tx', attempt, 'matching failure')
        unrelated = self.delivery_record('delivery-tx', 'older-or-newer-attempt', 'wrong failure')
        raw = matching + b'\n' + unrelated + b'\n'
        self.fallback.write_bytes(raw)

        self.book.recover()
        state = self.book.task('delivery-tx')
        self.assertEqual(state['delivery_error'], 'matching failure')
        self.assertEqual(state['delivery'], 'OUTPUT_UNCERTAIN')
        self.assertEqual(self.fallback.read_bytes(), raw)

    def test_unrelated_sealed_tail_does_not_abort_pending_delivery_recovery_pass(self):
        self.prepare_delivery()
        raw = encoded({'tx': 'unrelated', 'error': 'sealed evidence', 'payload': None, 'created': 'time'})
        self.fallback.write_bytes(raw)

        pending = self.book.recover()
        state = self.book.task('delivery-tx')
        self.assertEqual(state['delivery'], 'DELIVERING')
        self.assertTrue(any(item.get('tx') == 'delivery-tx' for item in pending))
        self.assertEqual(self.fallback.read_bytes(), raw)

    def test_fallback_append_rejects_middle_corruption_even_when_file_ends_in_lf(self):
        raw = encoded({'tx': 'ok', 'error': 'retained', 'payload': None, 'created': 'time'}) + b'\nnot-json\n'
        self.fallback.write_bytes(raw)
        with self.assertRaisesRegex(Exception, 'malformed JSON'):
            self.book.problem(None, 'must not append')
        self.assertEqual(self.fallback.read_bytes(), raw)
        self.assertEqual(self.book.db.execute('SELECT COUNT(*) FROM recovery').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()
