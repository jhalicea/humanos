import sqlite3
import tempfile
import unittest
from pathlib import Path

from notebook import Notebook, RECORD_INTEGRITY_PREFIX, RECORD_INTEGRITY_VERSION


class RecordEnvelopeIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self.tmp.name) / 'vault'

    def tearDown(self):
        self.tmp.cleanup()

    def populated(self):
        book = Notebook(self.vault)
        ident = book.bind('Jon', 'opening')
        book.start(ident['hcid'], 'tx-a', 'human text')
        book.append('tx-a', 1, 'ASSISTANT', 'assistant text')
        book.project()
        self.assertTrue(book.verify())
        return book

    def raw_db(self):
        return sqlite3.connect(self.vault / 'runtime' / 'notebook.sqlite3')

    def test_new_rows_bind_global_seq_and_metadata(self):
        book = self.populated()
        try:
            rows = list(book.db.execute('SELECT * FROM transcript ORDER BY seq'))
            self.assertEqual([r['seq'] for r in rows], [1, 2])
            for row in rows:
                self.assertEqual(row['record_integrity_version'], RECORD_INTEGRITY_VERSION)
                self.assertTrue(row['record_integrity'].startswith(RECORD_INTEGRITY_PREFIX))
        finally:
            book.close()

    def test_counter_equals_max_plus_one(self):
        book = self.populated()
        try:
            counter = book.db.execute(
                'SELECT next_seq FROM transcript_sequence WHERE id=1'
            ).fetchone()[0]
            maximum = book.db.execute('SELECT MAX(seq) FROM transcript').fetchone()[0]
            self.assertEqual(counter, maximum + 1)
        finally:
            book.close()

    def test_counter_allocation_rollback_leaves_no_gap(self):
        book = self.populated()
        try:
            before = book.db.execute(
                'SELECT next_seq FROM transcript_sequence WHERE id=1'
            ).fetchone()[0]
            book.db.execute('BEGIN IMMEDIATE')
            reserved = book._reserve_transcript_seq()
            self.assertEqual(reserved, before)
            book.db.rollback()
            after = book.db.execute(
                'SELECT next_seq FROM transcript_sequence WHERE id=1'
            ).fetchone()[0]
            self.assertEqual(after, before)
            self.assertTrue(book.verify())
        finally:
            book.close()

    def test_counter_missing_fails_closed(self):
        book = self.populated()
        book.close()
        with self.raw_db() as db:
            db.execute('DELETE FROM transcript_sequence')
        with self.assertRaisesRegex(RuntimeError, 'counter row is missing'):
            Notebook(self.vault)

    def test_counter_lower_fails_closed(self):
        book = self.populated()
        book.close()
        with self.raw_db() as db:
            db.execute('UPDATE transcript_sequence SET next_seq=1 WHERE id=1')
        with self.assertRaisesRegex(RuntimeError, 'sequence continuity mismatch'):
            Notebook(self.vault)

    def test_counter_higher_fails_closed(self):
        book = self.populated()
        book.close()
        with self.raw_db() as db:
            db.execute('UPDATE transcript_sequence SET next_seq=100 WHERE id=1')
        with self.assertRaisesRegex(RuntimeError, 'sequence continuity mismatch'):
            Notebook(self.vault)

    def test_seq_tampering_fails_envelope_verification(self):
        book = self.populated()
        book.close()
        with self.raw_db() as db:
            db.execute('DROP TRIGGER transcript_no_update')
            db.execute("UPDATE transcript SET seq=50 WHERE tx='tx-a' AND ordinal=1")
        with self.assertRaises(RuntimeError):
            Notebook(self.vault)

    def test_middle_post_activation_gap_is_detected(self):
        book = Notebook(self.vault)
        ident = book.bind('Jon', 'opening')
        for i in range(3):
            book.start(ident['hcid'], f'tx-{i}', f'human-{i}')
        book.project()
        book.close()
        with self.raw_db() as db:
            db.execute('DROP TRIGGER transcript_no_delete')
            db.execute('DELETE FROM transcript WHERE seq=2')
        with self.assertRaisesRegex(RuntimeError, 'sequence gap detected'):
            Notebook(self.vault)

    def test_old_runtime_style_insert_is_blocked(self):
        book = self.populated()
        try:
            ident = book.get_identity(book.get_transaction('tx-a')['hcid'])
            with self.assertRaises(sqlite3.IntegrityError):
                with book.db:
                    book.db.execute('INSERT INTO transactions VALUES(?,?,?,?,?)',
                                    ('old-runtime', ident['hcid'], 'text', 'STARTED', 'time'))
                    book.db.execute(
                        'INSERT INTO transcript(tx,ordinal,role,text,sha256,created) VALUES(?,?,?,?,?,?)',
                        ('old-runtime', 0, 'HUMAN', 'text', book.content_digest('text'), 'time')
                    )
            self.assertIsNone(book.get_transaction('old-runtime'))
            self.assertTrue(book.verify())
        finally:
            book.close()

    def test_out_of_band_gap_insert_is_rejected(self):
        book = self.populated()
        try:
            max_seq = book.db.execute('SELECT MAX(seq) FROM transcript').fetchone()[0]
            with self.assertRaises(sqlite3.IntegrityError):
                with book.db:
                    book.db.execute(
                        """INSERT INTO transcript(
                            seq,tx,ordinal,role,text,sha256,created,
                            record_integrity,record_integrity_version
                        ) VALUES(?,?,?,?,?,?,?,?,?)""",
                        (
                            max_seq + 1000, 'tx-a', 9, 'ASSISTANT', 'x',
                            book.content_digest('x'), 'time',
                            RECORD_INTEGRITY_PREFIX + ('0' * 64), RECORD_INTEGRITY_VERSION,
                        ),
                    )
            self.assertTrue(book.verify())
        finally:
            book.close()

    def test_policy_activation_boundary_is_authenticated(self):
        book = self.populated()
        book.close()
        with self.raw_db() as db:
            db.execute(
                "UPDATE runtime_meta SET value='9999' WHERE key='record_integrity_activation_seq'"
            )
        with self.assertRaisesRegex(RuntimeError, 'policy authentication failed'):
            Notebook(self.vault)


if __name__ == '__main__':
    unittest.main()
