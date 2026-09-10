from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'tools' / 'apply_record_envelope_patch.py'
NOTEBOOK = ROOT / 'notebook.py'
TEST = ROOT / 'tests' / 'test_record_envelope_integrity.py'


def replace_once(text, old, new, label):
    if old not in text:
        raise RuntimeError('patch anchor missing: ' + label)
    if text.count(old) != 1:
        raise RuntimeError('patch anchor not unique: ' + label)
    return text.replace(old, new, 1)


# Repair the quoting bug in the original guarded patch in-memory, then apply it.
source = OLD.read_text(encoding='utf-8')
source = source.replace("TEST.write_text(r'''import sqlite3", 'TEST.write_text(r\"\"\"import sqlite3', 1)
source = source.replace("\n''', encoding='utf-8')\n\nprint('record envelope patch applied')",
                        "\n\"\"\", encoding='utf-8')\n\nprint('record envelope patch applied')", 1)
compile(source, str(OLD), 'exec')
exec(compile(source, str(OLD), 'exec'), {'__file__': str(OLD), '__name__': '__main__'})

text = NOTEBOOK.read_text(encoding='utf-8')

text = replace_once(
    text,
    "    def record_integrity(self, tx, ordinal, role, content_digest, created):\n        envelope = {\n",
    "    def _next_transcript_seq(self):\n        return self.db.execute('SELECT COALESCE(MAX(seq),0)+1 FROM transcript').fetchone()[0]\n\n    def record_integrity(self, seq, tx, ordinal, role, content_digest, created):\n        envelope = {\n            'seq': seq,\n",
    'bind seq in envelope')

text = replace_once(
    text,
    "    def _insert_transcript(self, tx, ordinal, role, text):\n        stamp = now()\n        content_digest = self.content_digest(text)\n        record_integrity = self.record_integrity(tx, ordinal, role, content_digest, stamp)\n        self.db.execute('''INSERT INTO transcript(\n            tx,ordinal,role,text,sha256,created,record_integrity,record_integrity_version)\n            VALUES(?,?,?,?,?,?,?,?)''',\n            (tx, ordinal, role, text, content_digest, stamp, record_integrity, RECORD_INTEGRITY_VERSION))\n",
    "    def _insert_transcript(self, tx, ordinal, role, text):\n        seq = self._next_transcript_seq()\n        stamp = now()\n        content_digest = self.content_digest(text)\n        record_integrity = self.record_integrity(seq, tx, ordinal, role, content_digest, stamp)\n        self.db.execute('''INSERT INTO transcript(\n            seq,tx,ordinal,role,text,sha256,created,record_integrity,record_integrity_version)\n            VALUES(?,?,?,?,?,?,?,?,?)''',\n            (seq, tx, ordinal, role, text, content_digest, stamp, record_integrity, RECORD_INTEGRITY_VERSION))\n",
    'single insert with seq')

text = replace_once(
    text,
    "        expected = self.record_integrity(row['tx'], row['ordinal'], row['role'], row['sha256'], row['created'])\n",
    "        expected = self.record_integrity(row['seq'], row['tx'], row['ordinal'], row['role'], row['sha256'], row['created'])\n",
    'verify seq binding')

text = replace_once(
    text,
    "            bind_integrity_key(self.db, self.integrity_key)\n        except BaseException:\n",
    "            bind_integrity_key(self.db, self.integrity_key)\n            with self.db:\n                self.db.execute('INSERT OR REPLACE INTO runtime_meta(key,value) VALUES(?,?)',\n                                ('record_integrity_policy', 'required-v1'))\n                self.db.execute(\"\"\"CREATE TRIGGER IF NOT EXISTS transcript_require_record_integrity\n                    BEFORE INSERT ON transcript\n                    WHEN (SELECT value FROM runtime_meta WHERE key='record_integrity_policy')='required-v1'\n                    BEGIN\n                        SELECT CASE WHEN NEW.record_integrity IS NULL OR NEW.record_integrity_version IS NULL\n                            THEN RAISE(ABORT, 'HumanOS Security Violation: transcript record envelope required')\n                        END;\n                    END;\"\"\")\n        except BaseException:\n",
    'downgrade protection')

NOTEBOOK.write_text(text, encoding='utf-8')

test = TEST.read_text(encoding='utf-8')
test = test.replace(
    "            with book.db:\n                book.db.execute('INSERT INTO transactions VALUES(?,?,?,?,?)',\n                                ('legacy', ident['hcid'], text, 'STARTED', 'legacy-time'))\n",
    "            with book.db:\n                book.db.execute(\"UPDATE runtime_meta SET value='legacy-test' WHERE key='record_integrity_policy'\")\n                book.db.execute('INSERT INTO transactions VALUES(?,?,?,?,?)',\n                                ('legacy', ident['hcid'], text, 'STARTED', 'legacy-time'))\n",
    1)
test = test.replace(
    "                                ('legacy', 0, 'HUMAN', text, digest(text), 'legacy-time'))\n            book.project()\n",
    "                                ('legacy', 0, 'HUMAN', text, digest(text), 'legacy-time'))\n                book.db.execute(\"UPDATE runtime_meta SET value='required-v1' WHERE key='record_integrity_policy'\")\n            book.project()\n",
    1)
insert_at = test.index("    def test_unicode_roundtrip_keeps_exact_content_and_envelope")
extra = '''    def test_seq_tampering_is_detected(self):\n        book = self.tamper(\"UPDATE transcript SET seq=99 WHERE tx='tx-a' AND ordinal=1\")\n        try:\n            with self.assertRaisesRegex(RuntimeError, 'record integrity mismatch'):\n                book.verify()\n        finally:\n            book.close()\n\n    def test_old_runtime_style_insert_is_blocked_after_activation(self):\n        book = Notebook(self.vault)\n        try:\n            ident = book.bind('Jon', 'opening')\n            with self.assertRaisesRegex(sqlite3.IntegrityError, 'record envelope required'):\n                with book.db:\n                    book.db.execute('INSERT INTO transactions VALUES(?,?,?,?,?)',\n                                    ('old-runtime', ident['hcid'], 'text', 'STARTED', 'time'))\n                    book.db.execute(\"\"\"INSERT INTO transcript(tx,ordinal,role,text,sha256,created)\n                                       VALUES(?,?,?,?,?,?)\"\"\",\n                                    ('old-runtime', 0, 'HUMAN', 'text', book.content_digest('text'), 'time'))\n        finally:\n            book.close()\n\n'''
test = test[:insert_at] + extra + test[insert_at:]
TEST.write_text(test, encoding='utf-8')

print('record envelope v2 patch applied')
