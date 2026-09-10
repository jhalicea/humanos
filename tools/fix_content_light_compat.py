#!/usr/bin/env python3
"""Patch compatibility edges exposed by the first full content-light regression run."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def patch(path, replacements):
    target = ROOT / path
    source = target.read_text(encoding='utf-8')
    original = source
    for old, new, count in replacements:
        found = source.count(old)
        if found != count:
            raise SystemExit(f'fail closed: {path}: expected {count}, found {found}: {old[:100]!r}')
        source = source.replace(old, new, count)
    if source == original:
        raise SystemExit('fail closed: no changes for ' + path)
    target.write_text(source, encoding='utf-8')


patch('inbox_librarian.py', [
    ("from notebook import encode\n",
     "from notebook import encode\nfrom audit_privacy import classification_request_summary, classification_response_summary\n", 1),
    ("""        audit = {'source': source, 'source_sha256': inspected['proof']['sha256'],
                 'excerpt_sha256': inspected['excerpt_sha256'], 'method': inspected['method'],
                 'model': self.model.name, 'filename_quality': quality}
""",
     """        audit = classification_request_summary(
            self.manager.book, source, inspected['proof'], inspected['excerpt'],
            inspected['method'], self.model.name)
        audit['filename_quality'] = quality
""", 1),
    ("self.manager.book.event(tx, 'FILE_CLASSIFICATION_RESPONSE', dict(audit, decision=decision))",
     "self.manager.book.event(tx, 'FILE_CLASSIFICATION_RESPONSE', classification_response_summary(self.manager.book, audit, decision))", 1),
])

patch('tests/test_file_integration.py', [
    ("""        report = json.loads(self.events('turn', 'TOOL_RESULT')[0]['stdout'])
        self.assertEqual(len(report['groups']), 1)
        self.assertEqual(set(report['groups'][0]['files']), {'one.png', 'different-name.bin'})
""",
     """        audit = self.events('turn', 'TOOL_RESULT')[0]
        self.assertNotIn('stdout', audit)
        self.assertIn('stdout_digest', audit)
        self.assertIn('1 duplicate group(s)', final)
""", 1),
])

print('patched inbox audit events and updated legacy TOOL_RESULT test expectation')
