#!/usr/bin/env python3
"""One-time, fail-closed source transformation for content-digest privacy.

This script is intentionally narrow. It patches only notebook.py at the exact
sentinels below and writes focused regression tests. If the source has drifted,
it aborts before writing anything.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebook.py"
TEST = ROOT / "tests" / "test_content_digest_privacy.py"

source = NOTEBOOK.read_text(encoding="utf-8")
original = source


def replace_once(old, new):
    global source
    count = source.count(old)
    if count != 1:
        raise SystemExit(f"fail closed: expected one source match, found {count}: {old[:80]!r}")
    source = source.replace(old, new, 1)


replace_once("import hashlib\n", "import hashlib\nimport hmac\n")

replace_once(
"""def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()
""",
"""DIGEST_PREFIX = 'hmac-sha256:'


def digest(text):
    \"\"\"Legacy SHA-256 verifier only. New content must use Notebook.content_digest.\"\"\"
    return hashlib.sha256(text.encode('utf-8')).hexdigest()
""")

replace_once(
"""        self.db = sqlite3.connect(str(self.root / 'notebook.sqlite3'))
""",
"""        self.integrity_key = self._load_integrity_key()
        self.db = sqlite3.connect(str(self.root / 'notebook.sqlite3'))
""")

replace_once(
"""    def close(self):
        self.db.close()
        self.lock.close()
""",
"""    def _load_integrity_key(self):
        \"\"\"Load/create the vault-scoped HMAC key; never expose it in projections.\"\"\"
        path = self.root / 'integrity.key'
        if path.exists():
            key = path.read_bytes()
            if len(key) != 32:
                raise RuntimeError('Notebook integrity key is invalid')
            try:
                os.chmod(path, 0o600)
            except OSError:
                pass
            return key
        key = os.urandom(32)
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(fd, 'wb', closefd=True) as f:
                f.write(key)
                f.flush()
                os.fsync(f.fileno())
        except Exception:
            try:
                path.unlink()
            except OSError:
                pass
            raise
        parent_fd = os.open(str(self.root), os.O_RDONLY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
        return key

    def content_digest(self, text):
        mac = hmac.new(self.integrity_key, text.encode('utf-8'), hashlib.sha256).hexdigest()
        return DIGEST_PREFIX + mac

    def digest_matches(self, stored, text):
        if not isinstance(stored, str):
            return False
        if stored.startswith(DIGEST_PREFIX):
            return hmac.compare_digest(stored, self.content_digest(text))
        # Backward compatibility only: old vault rows used naked SHA-256.
        return hmac.compare_digest(stored, digest(text))

    def close(self):
        self.db.close()
        self.lock.close()
""")

# New writes use keyed digests. Legacy digest() remains only for backward reads.
for old, new, expected in [
    ("'opening_hash': digest(opening)", "'opening_hash': self.content_digest(opening)", 1),
    ("(tx, 0, 'HUMAN', user_input, digest(user_input), now())", "(tx, 0, 'HUMAN', user_input, self.content_digest(user_input), now())", 1),
    ("(tx, ordinal, role, text, digest(text), now())", "(tx, ordinal, role, text, self.content_digest(text), now())", 1),
    ("(tx, ordinal, 'ASSISTANT', message, digest(message), now())", "(tx, ordinal, 'ASSISTANT', message, self.content_digest(message), now())", 1),
]:
    count = source.count(old)
    if count != expected:
        raise SystemExit(f"fail closed: expected {expected} matches, found {count}: {old!r}")
    source = source.replace(old, new)

replace_once(
"""        if (not human or human['role'] != 'HUMAN' or human['text'] != transaction['input'] or
                human['sha256'] != digest(human['text'])):
""",
"""        if (not human or human['role'] != 'HUMAN' or human['text'] != transaction['input'] or
                not self.digest_matches(human['sha256'], human['text'])):
""")

replace_once(
"""            if (prior['role'] != 'ASSISTANT' or prior['text'] != message or
                    prior['sha256'] != digest(message) or ordinal != self.message_count(tx) - 1):
""",
"""            if (prior['role'] != 'ASSISTANT' or prior['text'] != message or
                    not self.digest_matches(prior['sha256'], message) or ordinal != self.message_count(tx) - 1):
""")

replace_once(
"""                    'outcome': outcome, 'reason': str(reason), 'final_ordinal': ordinal,
                    'final_sha256': digest(message), 'prior_phase': original.get('phase'),
                    'prior_state_sha256': digest(encode(original)), 'pending': pending,
""",
"""                    'outcome': outcome, 'reason': str(reason), 'final_ordinal': ordinal,
                    'final_digest': self.content_digest(message), 'prior_phase': original.get('phase'),
                    'prior_state_digest': self.content_digest(encode(original)), 'pending': pending,
""")

replace_once(
"""        if (not final or final['role'] != 'ASSISTANT' or final['text'] != state.get('final') or
                digest(final['text']) != final['sha256'] or
""",
"""        if (not final or final['role'] != 'ASSISTANT' or final['text'] != state.get('final') or
                not self.digest_matches(final['sha256'], final['text']) or
""")

replace_once(
"""        state.update(delivery='DELIVERING', delivery_attempt=uuid.uuid4().hex,
                     delivery_attempts=state.get('delivery_attempts', 0) + 1,
                     delivery_started=now(), delivery_sha256=digest(response))
        state.pop('delivery_error', None)
        with self.db:
            self.db.execute('UPDATE tasks SET state=? WHERE tx=?', (encode(state), tx))
            self._append_event(tx, 'DELIVERY_STARTED', {
                'attempt': state['delivery_attempt'], 'sha256': state['delivery_sha256'],
                'characters_with_terminal_newline': len(response) + 1})
""",
"""        state.update(delivery='DELIVERING', delivery_attempt=uuid.uuid4().hex,
                     delivery_attempts=state.get('delivery_attempts', 0) + 1,
                     delivery_started=now(), delivery_digest=self.content_digest(response))
        state.pop('delivery_sha256', None)
        state.pop('delivery_error', None)
        with self.db:
            self.db.execute('UPDATE tasks SET state=? WHERE tx=?', (encode(state), tx))
            self._append_event(tx, 'DELIVERY_STARTED', {
                'attempt': state['delivery_attempt'], 'content_digest': state['delivery_digest'],
                'characters_with_terminal_newline': len(response) + 1})
""")

replace_once(
"""        if state.get('delivery') != 'DELIVERING' or state.get('delivery_sha256') != digest(state['final']):
            raise RuntimeError('Output confirmation requires a matching durable delivery attempt')
""",
"""        stored_delivery_digest = state.get('delivery_digest', state.get('delivery_sha256'))
        if state.get('delivery') != 'DELIVERING' or not self.digest_matches(stored_delivery_digest, state['final']):
            raise RuntimeError('Output confirmation requires a matching durable delivery attempt')
""")

replace_once(
"""            self._append_event(tx, 'DELIVERY', {'status': state['delivery'],
                                               'attempt': state['delivery_attempt'],
                                               'sha256': state['delivery_sha256']})
""",
"""            self._append_event(tx, 'DELIVERY', {'status': state['delivery'],
                                               'attempt': state['delivery_attempt'],
                                               'content_digest': stored_delivery_digest})
""")

replace_once(
"""        for row in self.db.execute('SELECT text,sha256 FROM transcript'):
            if digest(row['text']) != row['sha256']:
                raise RuntimeError('Transcript hash mismatch')
""",
"""        for row in self.db.execute('SELECT text,sha256 FROM transcript'):
            if not self.digest_matches(row['sha256'], row['text']):
                raise RuntimeError('Transcript hash mismatch')
""")

if source == original:
    raise SystemExit('fail closed: no source changes produced')

# No new naked content digest calls should remain outside the legacy verifier path.
remaining = [line for line in source.splitlines() if 'digest(' in line and 'def digest' not in line]
for line in remaining:
    if 'self.content_digest(' in line or 'self.digest_matches(' in line or 'hmac.new(' in line:
        continue
    if 'return hmac.compare_digest(stored, digest(text))' in line:
        continue
    raise SystemExit('fail closed: unclassified digest use remains: ' + line.strip())

NOTEBOOK.write_text(source, encoding='utf-8')

TEST.write_text(r'''import hashlib
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from notebook import DIGEST_PREFIX, Notebook, digest


class ContentDigestPrivacyTests(unittest.TestCase):
    def new_book(self, name='vault'):
        root = Path(self.tmp.name) / name
        book = Notebook(root)
        book.recover()
        return book

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def test_new_transcript_digest_is_keyed_not_plain_sha256(self):
        book = self.new_book()
        try:
            ident = book.bind('Jon', 'same opening')
            book.start(ident['hcid'], 'tx', 'predictable plaintext')
            stored = book.db.execute("SELECT sha256 FROM transcript WHERE tx='tx'").fetchone()[0]
            self.assertTrue(stored.startswith(DIGEST_PREFIX))
            self.assertNotEqual(stored, hashlib.sha256(b'predictable plaintext').hexdigest())
            self.assertTrue(book.verify())
        finally:
            book.close()

    def test_same_plaintext_in_different_vaults_has_different_digest(self):
        one = self.new_book('one')
        two = self.new_book('two')
        try:
            a = one.bind('Jon', 'opening')
            b = two.bind('Jon', 'opening')
            one.start(a['hcid'], 'tx-a', 'same secret-shaped text')
            two.start(b['hcid'], 'tx-b', 'same secret-shaped text')
            da = one.db.execute("SELECT sha256 FROM transcript WHERE tx='tx-a'").fetchone()[0]
            db = two.db.execute("SELECT sha256 FROM transcript WHERE tx='tx-b'").fetchone()[0]
            self.assertNotEqual(da, db)
        finally:
            one.close()
            two.close()

    def test_integrity_key_is_local_owner_only_and_not_projected(self):
        book = self.new_book()
        try:
            key_path = book.root / 'integrity.key'
            self.assertEqual(len(key_path.read_bytes()), 32)
            if os.name == 'posix':
                mode = stat.S_IMODE(key_path.stat().st_mode)
                self.assertEqual(mode & 0o077, 0)
            ident = book.bind('Jon', 'opening')
            book.start(ident['hcid'], 'tx', 'text')
            book.project()
            key_hex = key_path.read_bytes().hex()
            for path in book.root.rglob('*'):
                if path.is_file() and path != key_path and path.suffix in ('.json', '.md'):
                    self.assertNotIn(key_hex, path.read_text(encoding='utf-8'))
        finally:
            book.close()

    def test_legacy_sha256_transcript_remains_verifiable(self):
        book = self.new_book()
        try:
            ident = book.bind('Jon', 'opening')
            text = 'legacy row'
            with book.db:
                book.db.execute('INSERT INTO transactions VALUES(?,?,?,?,?)',
                                ('legacy', ident['hcid'], text, 'STARTED', 'legacy-time'))
                book.db.execute('INSERT INTO transcript(tx,ordinal,role,text,sha256,created) VALUES(?,?,?,?,?,?)',
                                ('legacy', 0, 'HUMAN', text, digest(text), 'legacy-time'))
            book.project()
            self.assertTrue(book.verify())
        finally:
            book.close()

    def test_wrong_key_fails_closed_for_new_rows(self):
        vault = Path(self.tmp.name) / 'vault'
        book = Notebook(vault)
        ident = book.bind('Jon', 'opening')
        book.start(ident['hcid'], 'tx', 'protected text')
        book.close()
        key_path = vault / 'runtime' / 'integrity.key'
        key_path.write_bytes(b'X' * 32)
        reopened = Notebook(vault)
        try:
            with self.assertRaisesRegex(RuntimeError, 'Transcript hash mismatch'):
                reopened.verify()
        finally:
            reopened.close()

    def test_delivery_events_use_content_digest_not_plain_sha256(self):
        book = self.new_book()
        try:
            ident = book.bind('Jon', 'opening')
            book.start(ident['hcid'], 'tx', 'hello')
            final = 'predictable final'
            book.append('tx', 1, 'ASSISTANT', final)
            book.save_task('tx', {'phase': 'COMPLETE', 'final': final, 'final_ordinal': 1,
                                  'delivery': 'PREPARED_NOT_CONFIRMED'})
            book.checkpoint('tx')
            self.assertTrue(book.prepare_delivery('tx', final))
            started = json.loads(book.db.execute(
                "SELECT payload FROM events WHERE tx='tx' AND kind='DELIVERY_STARTED'").fetchone()[0])
            self.assertIn('content_digest', started)
            self.assertNotIn('sha256', started)
            self.assertTrue(started['content_digest'].startswith(DIGEST_PREFIX))
            self.assertNotEqual(started['content_digest'], hashlib.sha256(final.encode()).hexdigest())
            self.assertTrue(book.finish_delivery('tx'))
            delivered = json.loads(book.db.execute(
                "SELECT payload FROM events WHERE tx='tx' AND kind='DELIVERY'").fetchone()[0])
            self.assertIn('content_digest', delivered)
            self.assertNotIn('sha256', delivered)
        finally:
            book.close()

    def test_existing_legacy_delivery_digest_can_still_finish(self):
        book = self.new_book()
        try:
            ident = book.bind('Jon', 'opening')
            book.start(ident['hcid'], 'tx', 'hello')
            final = 'legacy delivery final'
            book.append('tx', 1, 'ASSISTANT', final)
            state = {'phase': 'COMPLETE', 'final': final, 'final_ordinal': 1,
                     'delivery': 'DELIVERING', 'delivery_attempt': 'old-attempt',
                     'delivery_sha256': digest(final)}
            book.save_task('tx', state)
            book.checkpoint('tx')
            self.assertTrue(book.finish_delivery('tx'))
        finally:
            book.close()


if __name__ == '__main__':
    unittest.main()
''', encoding='utf-8')

print('patched notebook.py and wrote tests/test_content_digest_privacy.py')
