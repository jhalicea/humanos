import sqlite3
import tempfile
import unittest
from pathlib import Path

from notebook import Notebook, RECORD_INTEGRITY_PREFIX, RECORD_INTEGRITY_VERSION, digest


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

    def test_missing_trigger_cannot_hide_weak_post_activation_row(self):
        book = self.populated()
        weak_digest = book.content_digest('weak row')
        book.close()
        with self.raw_db() as db:
            db.execute('DROP TRIGGER transcript_require_record_integrity')
            next_seq = db.execute(
                'SELECT next_seq FROM transcript_sequence WHERE id=1'
            ).fetchone()[0]
            db.execute('UPDATE transcript_sequence SET next_seq=next_seq+1 WHERE id=1')
            db.execute(
                """INSERT INTO transcript(
                    seq,tx,ordinal,role,text,sha256,created,
                    record_integrity,record_integrity_version
                ) VALUES(?,?,?,?,?,?,?,?,?)""",
                (next_seq, 'tx-a', 2, 'ASSISTANT', 'weak row', weak_digest, 'time', None, None),
            )
        with self.assertRaisesRegex(RuntimeError, 'envelope missing after activation boundary'):
            Notebook(self.vault)

    def test_missing_trigger_and_policy_cannot_reclassify_upgraded_vault_as_legacy(self):
        book = self.populated()
        book.close()
        with self.raw_db() as db:
            db.execute('DROP TRIGGER transcript_require_record_integrity')
            db.execute("DELETE FROM runtime_meta WHERE key='record_integrity_policy'")
        with self.assertRaisesRegex(RuntimeError, 'policy metadata is missing or downgraded'):
            Notebook(self.vault)

    def test_policy_metadata_copied_from_different_key_vault_fails_closed(self):
        first = self.populated()
        first.close()

        other_vault = Path(self.tmp.name) / 'other-vault'
        other = Notebook(other_vault)
        ident = other.bind('Jon', 'opening')
        other.start(ident['hcid'], 'tx-b', 'human text')
        other.append('tx-b', 1, 'ASSISTANT', 'assistant text')
        other.project()
        self.assertTrue(other.verify())
        other.close()

        other_db = sqlite3.connect(other_vault / 'runtime' / 'notebook.sqlite3')
        try:
            copied = dict(other_db.execute(
                "SELECT key,value FROM runtime_meta WHERE key IN ("
                "'record_integrity_policy','record_integrity_activation_seq','record_integrity_policy_proof')"
            ))
        finally:
            other_db.close()

        with self.raw_db() as db:
            for key, value in copied.items():
                db.execute('UPDATE runtime_meta SET value=? WHERE key=?', (value, key))

        with self.assertRaisesRegex(RuntimeError, 'policy authentication failed'):
            Notebook(self.vault)


    def test_null_record_integrity_version_is_rejected_at_insert(self):
        book = self.populated()
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                with book._immediate():
                    seq = book._reserve_transcript_seq()
                    book.db.execute(
                        """INSERT INTO transcript(
                            seq,tx,ordinal,role,text,sha256,created,
                            record_integrity,record_integrity_version
                        ) VALUES(?,?,?,?,?,?,?,?,?)""",
                        (
                            seq, 'tx-a', 2, 'ASSISTANT', 'partial',
                            book.content_digest('partial'), 'time',
                            RECORD_INTEGRITY_PREFIX + ('0' * 64), None,
                        ),
                    )
            self.assertTrue(book.verify())
        finally:
            book.close()


    def test_policy_deletion_cannot_disarm_envelope_trigger_while_open(self):
        book = self.populated()
        try:
            with self.raw_db() as db:
                db.execute("DELETE FROM runtime_meta WHERE key='record_integrity_policy'")

            attacker = self.raw_db()
            try:
                next_seq = attacker.execute(
                    'SELECT next_seq FROM transcript_sequence WHERE id=1'
                ).fetchone()[0]
                attacker.execute('UPDATE transcript_sequence SET next_seq=next_seq+1 WHERE id=1')
                with self.assertRaises(sqlite3.IntegrityError):
                    attacker.execute(
                        """INSERT INTO transcript(
                            seq,tx,ordinal,role,text,sha256,created,
                            record_integrity,record_integrity_version
                        ) VALUES(?,?,?,?,?,?,?,?,?)""",
                        (next_seq, 'tx-a', 2, 'ASSISTANT', 'weak',
                         book.content_digest('weak'), 'time', None, None),
                    )
                attacker.rollback()
            finally:
                attacker.close()

            with self.assertRaisesRegex(RuntimeError, 'policy metadata is missing or downgraded'):
                book.append('tx-a', 2, 'ASSISTANT', 'blocked')
            self.assertEqual(book.message_count('tx-a'), 2)
        finally:
            book.close()

    def test_same_name_noop_trigger_is_replaced_on_reopen(self):
        book = self.populated()
        book.close()
        with self.raw_db() as db:
            db.execute('DROP TRIGGER transcript_require_record_integrity')
            db.execute("""CREATE TRIGGER transcript_require_record_integrity
                BEFORE INSERT ON transcript BEGIN SELECT 1; END""")

        reopened = Notebook(self.vault)
        try:
            sql = reopened.db.execute(
                "SELECT sql FROM sqlite_master WHERE type='trigger' "
                "AND name='transcript_require_record_integrity'"
            ).fetchone()[0]
            self.assertIn('record envelope required', sql)
            self.assertIn('record_integrity_version IS NULL', sql)
        finally:
            reopened.close()

    def test_trigger_definition_change_after_startup_blocks_append(self):
        book = self.populated()
        try:
            with self.raw_db() as db:
                db.execute('DROP TRIGGER transcript_require_record_integrity')
                db.execute("""CREATE TRIGGER transcript_require_record_integrity
                    BEFORE INSERT ON transcript BEGIN SELECT 1; END""")
            with self.assertRaisesRegex(RuntimeError, 'trigger definition changed after Notebook startup'):
                book.append('tx-a', 2, 'ASSISTANT', 'blocked')
            self.assertEqual(book.message_count('tx-a'), 2)
        finally:
            book.close()

    def test_unrelated_schema_change_does_not_block_append(self):
        book = self.populated()
        try:
            with book.db:
                book.db.execute('CREATE TABLE unrelated_runtime_state(id INTEGER PRIMARY KEY)')
            book.append('tx-a', 2, 'ASSISTANT', 'still allowed')
            book.project()
            self.assertTrue(book.verify())
        finally:
            book.close()

    def test_counter_tamper_after_startup_blocks_before_reservation(self):
        book = self.populated()
        try:
            with self.raw_db() as db:
                db.execute('UPDATE transcript_sequence SET next_seq=100 WHERE id=1')
            with self.assertRaisesRegex(RuntimeError, 'continuity mismatch before write'):
                book.append('tx-a', 2, 'ASSISTANT', 'blocked')
            self.assertEqual(book.message_count('tx-a'), 2)
            self.assertEqual(
                book.db.execute('SELECT next_seq FROM transcript_sequence WHERE id=1').fetchone()[0],
                100,
            )
        finally:
            book.close()


    def test_legacy_row_deletion_after_activation_fails_closed(self):
        runtime = self.vault / 'runtime'
        runtime.mkdir(parents=True, mode=0o700)
        with sqlite3.connect(runtime / 'notebook.sqlite3') as db:
            db.executescript("""
                CREATE TABLE identities(
                  hcid TEXT PRIMARY KEY, owner TEXT NOT NULL, page TEXT UNIQUE NOT NULL,
                  binding TEXT NOT NULL, opening_hash TEXT NOT NULL, created TEXT NOT NULL);
                CREATE TABLE transactions(
                  tx TEXT PRIMARY KEY, hcid TEXT NOT NULL REFERENCES identities(hcid),
                  input TEXT NOT NULL, status TEXT NOT NULL, created TEXT NOT NULL);
                CREATE TABLE transcript(
                  seq INTEGER PRIMARY KEY AUTOINCREMENT, tx TEXT NOT NULL REFERENCES transactions(tx),
                  ordinal INTEGER NOT NULL, role TEXT NOT NULL, text TEXT NOT NULL,
                  sha256 TEXT NOT NULL, created TEXT NOT NULL, UNIQUE(tx,ordinal));
            """)
            db.execute('INSERT INTO identities VALUES(?,?,?,?,?,?)',
                       ('legacy-hcid', 'Jon', 'legacy-page', 'VERIFIED', digest('opening'), 'legacy-time'))
            for seq in (1, 2):
                tx = f'legacy-{seq}'
                text = f'legacy row {seq}'
                db.execute('INSERT INTO transactions VALUES(?,?,?,?,?)',
                           (tx, 'legacy-hcid', text, 'STARTED', 'legacy-time'))
                db.execute('INSERT INTO transcript(seq,tx,ordinal,role,text,sha256,created) VALUES(?,?,?,?,?,?,?)',
                           (seq, tx, 0, 'HUMAN', text, digest(text), 'legacy-time'))

        book = Notebook(self.vault)
        try:
            self.assertEqual(book._meta('record_integrity_activation_seq'), '2')
            self.assertEqual(book._meta('record_integrity_legacy_row_count'), '2')
            book.project()
            self.assertTrue(book.verify())
        finally:
            book.close()

        with self.raw_db() as db:
            db.execute('DROP TRIGGER transcript_no_delete')
            db.execute('DELETE FROM transcript WHERE seq=1')

        with self.assertRaisesRegex(RuntimeError, 'Legacy transcript row count mismatch'):
            Notebook(self.vault)

    def test_legacy_row_count_metadata_is_authenticated(self):
        runtime = self.vault / 'runtime'
        runtime.mkdir(parents=True, mode=0o700)
        with sqlite3.connect(runtime / 'notebook.sqlite3') as db:
            db.executescript("""
                CREATE TABLE identities(
                  hcid TEXT PRIMARY KEY, owner TEXT NOT NULL, page TEXT UNIQUE NOT NULL,
                  binding TEXT NOT NULL, opening_hash TEXT NOT NULL, created TEXT NOT NULL);
                CREATE TABLE transactions(
                  tx TEXT PRIMARY KEY, hcid TEXT NOT NULL REFERENCES identities(hcid),
                  input TEXT NOT NULL, status TEXT NOT NULL, created TEXT NOT NULL);
                CREATE TABLE transcript(
                  seq INTEGER PRIMARY KEY AUTOINCREMENT, tx TEXT NOT NULL REFERENCES transactions(tx),
                  ordinal INTEGER NOT NULL, role TEXT NOT NULL, text TEXT NOT NULL,
                  sha256 TEXT NOT NULL, created TEXT NOT NULL, UNIQUE(tx,ordinal));
            """)
            db.execute('INSERT INTO identities VALUES(?,?,?,?,?,?)',
                       ('legacy-hcid', 'Jon', 'legacy-page', 'VERIFIED', digest('opening'), 'legacy-time'))
            db.execute('INSERT INTO transactions VALUES(?,?,?,?,?)',
                       ('legacy', 'legacy-hcid', 'legacy row', 'STARTED', 'legacy-time'))
            db.execute('INSERT INTO transcript(seq,tx,ordinal,role,text,sha256,created) VALUES(?,?,?,?,?,?,?)',
                       (1, 'legacy', 0, 'HUMAN', 'legacy row', digest('legacy row'), 'legacy-time'))

        book = Notebook(self.vault)
        book.project()
        self.assertTrue(book.verify())
        book.close()

        with self.raw_db() as db:
            db.execute("UPDATE runtime_meta SET value='0' WHERE key='record_integrity_legacy_row_count'")

        with self.assertRaisesRegex(RuntimeError, 'policy authentication failed'):
            Notebook(self.vault)


if __name__ == '__main__':
    unittest.main()
