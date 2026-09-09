#!/usr/bin/env python3
from pathlib import Path
p = Path(__file__).with_name('apply_content_digest_privacy.py')
s = p.read_text(encoding='utf-8')
old = "for line in remaining:\n    if 'self.content_digest(' in line or 'self.digest_matches(' in line or 'hmac.new(' in line:\n        continue\n"
new = "for line in remaining:\n    if line.strip().startswith('def content_digest'):\n        continue\n    if 'self.content_digest(' in line or 'self.digest_matches(' in line or 'hmac.new(' in line:\n        continue\n"
if s.count(old) != 1:
    raise SystemExit('fail closed: guard patch sentinel mismatch')
p.write_text(s.replace(old, new, 1), encoding='utf-8')
print('bootstrap guard corrected in workflow checkout')
