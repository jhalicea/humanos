#!/usr/bin/env python3
"""One-time fail-closed patch wiring integrity lifecycle into Notebook."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'notebook.py'
source = path.read_text(encoding='utf-8')
original = source

needle = "from audit_privacy import assert_content_light, request_summary\n"
replacement = needle + "from integrity_lifecycle import bind_integrity_key, load_or_create_integrity_key\n"
if source.count(needle) != 1 or 'from integrity_lifecycle import ' in source:
    raise SystemExit('fail closed: unexpected notebook import shape')
source = source.replace(needle, replacement, 1)

needle = "        self.integrity_key = self._load_integrity_key()\n        self.db = sqlite3.connect(str(self.root / 'notebook.sqlite3'))\n"
replacement = """        try:
            self.integrity_key = self._load_integrity_key()
        except BaseException:
            self.lock.close()
            raise
        self.db = sqlite3.connect(str(self.root / 'notebook.sqlite3'))
"""
if source.count(needle) != 1:
    raise SystemExit('fail closed: integrity-key initialization shape changed')
source = source.replace(needle, replacement, 1)

needle = """        if 'scope' not in {row['name'] for row in self.db.execute('PRAGMA table_info(recovery)')}:
            with self.db:
                self.db.execute(\"ALTER TABLE recovery ADD COLUMN scope TEXT NOT NULL DEFAULT 'NOTEBOOK'\")

"""
replacement = needle + """        try:
            # Reject a replaced key before recover() or any later code can append evidence.
            bind_integrity_key(self.db, self.integrity_key)
        except BaseException:
            self.db.close()
            self.lock.close()
            raise

"""
if source.count(needle) != 1:
    raise SystemExit('fail closed: recovery-schema migration shape changed')
source = source.replace(needle, replacement, 1)

start_marker = '    def _load_integrity_key(self):\n'
end_marker = '    def content_digest(self, text):\n'
if source.count(start_marker) != 1 or source.count(end_marker) != 1:
    raise SystemExit('fail closed: integrity-key method markers changed')
start = source.index(start_marker)
end = source.index(end_marker, start)
replacement = """    def _load_integrity_key(self):
        \"\"\"Load/create the stable vault key under fail-closed lifecycle rules.\"\"\"
        return load_or_create_integrity_key(self.root)

"""
source = source[:start] + replacement + source[end:]

if source == original:
    raise SystemExit('fail closed: no notebook changes produced')
path.write_text(source, encoding='utf-8')
print('patched notebook.py for stable integrity-key lifecycle')
