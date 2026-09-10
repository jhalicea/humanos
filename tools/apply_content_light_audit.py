#!/usr/bin/env python3
"""One-time fail-closed source migration for content-light audit events."""
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


patch('notebook.py', [
    ("from audit import AuditEvent, hash_event, verify_chain\n",
     "from audit import AuditEvent, hash_event, verify_chain\nfrom audit_privacy import assert_content_light, request_summary\n", 1),
    ("""    def _append_event(self, tx, kind, payload):
        \"\"\"Append inside the caller's transaction when state and evidence must agree.\"\"\"
        previous = self.db.execute('SELECT seq,event_hash FROM events ORDER BY seq DESC LIMIT 1').fetchone()
""",
     """    def _append_event(self, tx, kind, payload):
        \"\"\"Append content-light evidence inside the caller's state transaction.\"\"\"
        assert_content_light(payload)
        previous = self.db.execute('SELECT seq,event_hash FROM events ORDER BY seq DESC LIMIT 1').fetchone()
""", 1),
    ("""                    'final_digest': self.content_digest(message), 'prior_phase': original.get('phase'),
                    'prior_state_digest': self.content_digest(encode(original)), 'pending': pending,
                    'execution_closed': True, 'reconciliation_closed': False})
""",
     """                    'final_digest': self.content_digest(message), 'prior_phase': original.get('phase'),
                    'prior_state_digest': self.content_digest(encode(original)),
                    'pending_request': request_summary(self, pending) if pending else None,
                    'execution_closed': True, 'reconciliation_closed': False})
""", 1),
])

patch('engine.py', [
    ("from source_reader import SourceReader\n",
     "from source_reader import SourceReader\nfrom audit_privacy import (context_summary, exception_summary, model_response_summary,\n                           observation_summary, request_summary)\n", 1),
    ("self.book.event(tx, 'CONTEXT_LOADED', packet)",
     "self.book.event(tx, 'CONTEXT_LOADED', context_summary(self.book, packet))", 1),
    ("self.book.event(tx, 'TOOL_REQUEST', state['pending'])",
     "self.book.event(tx, 'TOOL_REQUEST', request_summary(self.book, state['pending']))", 1),
    ("""                                self.book.save_task_event(tx, state, 'AUTHORIZATION', {'request': request, 'allowed': False, 'reason': 'Plan execution was not explicitly requested by the human'})
""",
     """                                denied = request_summary(self.book, request)
                                denied.update(allowed=False, reason='Plan execution was not explicitly requested by the human')
                                self.book.save_task_event(tx, state, 'AUTHORIZATION', denied)
""", 1),
    ("""                        self.book.save_task_event(tx, state, 'AUTHORIZATION', {'request': request, 'allowed': allowed,
                            'scope_sha256': digest(encode(state['permissions']))})
""",
     """                        authorization = request_summary(self.book, request)
                        authorization.update(allowed=allowed,
                            scope_digest=self.book.content_digest(encode(state['permissions'])))
                        self.book.save_task_event(tx, state, 'AUTHORIZATION', authorization)
""", 1),
    ("self.book.event(tx, 'TOOL_RESULT', observation)",
     "self.book.event(tx, 'TOOL_RESULT', observation_summary(self.book, state['pending'], observation))", 1),
    ("self.book.event(tx, 'MODEL_RESPONSE_REJECTED', {'error': str(invalid)})",
     "self.book.event(tx, 'MODEL_RESPONSE_REJECTED', exception_summary(self.book, invalid))", 1),
    ("self.book.event(tx, 'MODEL_RESPONSE', {'model': self.model.name, 'proposal': proposal})",
     "self.book.event(tx, 'MODEL_RESPONSE', model_response_summary(self.book, self.model.name, proposal))", 1),
])

patch('file_manager.py', [
    ("from notebook import encode, digest\n",
     "from notebook import encode, digest\nfrom audit_privacy import plan_summary, state_summary\n", 1),
    ("self.book._append_event(tx, 'FILE_PLAN_CREATED', {'plan': plan, 'sha256': digest(encode(plan))})",
     "self.book._append_event(tx, 'FILE_PLAN_CREATED', plan_summary(self.book, plan))", 1),
    ("""        event = self.book.db.execute(\"SELECT payload FROM events WHERE kind='FILE_PLAN_CREATED' AND payload LIKE ?\", ('%'+plan_id+'%',)).fetchone()
        if not event or json.loads(event[0])['sha256'] != digest(encode(plan)):
            raise RuntimeError('Saved plan differs from its audit evidence')
""",
     """        event = self.book.db.execute(\"SELECT payload FROM events WHERE kind='FILE_PLAN_CREATED' AND payload LIKE ?\", ('%'+plan_id+'%',)).fetchone()
        if not event:
            raise RuntimeError('Saved plan differs from its audit evidence')
        creation = json.loads(event[0])
        if 'plan_digest' in creation:
            if creation['plan_digest'] != self.book.content_digest(encode(plan)):
                raise RuntimeError('Saved plan differs from its audit evidence')
        elif creation.get('sha256') != digest(encode(plan)):
            # Legacy Runtime 0.1 event compatibility; old append-only rows are not rewritten.
            raise RuntimeError('Saved plan differs from its audit evidence')
""", 1),
    ("""            if payload.get('plan_id') == plan_id and 'state' in payload:
                if payload['state'] != state:
                    raise RuntimeError('Saved plan progress differs from its audit evidence')
                break
""",
     """            if payload.get('plan_id') == plan_id and ('state_digest' in payload or 'state' in payload):
                if 'state_digest' in payload:
                    if payload['state_digest'] != self.book.content_digest(encode(state)):
                        raise RuntimeError('Saved plan progress differs from its audit evidence')
                elif payload['state'] != state:
                    # Legacy Runtime 0.1 event compatibility.
                    raise RuntimeError('Saved plan progress differs from its audit evidence')
                break
""", 1),
    ("self.book._append_event(None, event, {'plan_id': plan['plan_id'], 'state': state})",
     "self.book._append_event(None, event, state_summary(self.book, plan['plan_id'], state))", 1),
])

patch('file_intelligence.py', [
    ("from notebook import encode\n",
     "from notebook import encode\nfrom audit_privacy import classification_request_summary, classification_response_summary\n", 1),
    ("""        audit = {'source': path, 'source_sha256': inspected['proof']['sha256'],
                 'excerpt_sha256': inspected['excerpt_sha256'], 'method': inspected['method'],
                 'model': self.model.name}
""",
     """        audit = classification_request_summary(
            self.manager.book, path, inspected['proof'], inspected['excerpt'],
            inspected['method'], self.model.name)
""", 1),
    ("self.manager.book.event(tx, 'FILE_CLASSIFICATION_RESPONSE', dict(audit, decision=decision))",
     "self.manager.book.event(tx, 'FILE_CLASSIFICATION_RESPONSE', classification_response_summary(self.manager.book, audit, decision))", 1),
])

patch('tests/test_file_intelligence.py', [
    ("""        plan = json.loads(self.book.db.execute(
            \"SELECT payload FROM events WHERE tx='preview' AND kind='FILE_PLAN_CREATED'\").fetchone()[0])['plan']
""",
     """        plan_id = json.loads(self.book.db.execute(
            \"SELECT payload FROM events WHERE tx='preview' AND kind='FILE_PLAN_CREATED'\").fetchone()[0])['plan_id']
""", 1),
    ("apply.run('apply', self.identity['hcid'], '/apply ' + plan['plan_id'])",
     "apply.run('apply', self.identity['hcid'], '/apply ' + plan_id)", 1),
    ("self.assertEqual(approved, [{'name': 'apply_plan', 'plan_id': plan['plan_id']}])",
     "self.assertEqual(approved, [{'name': 'apply_plan', 'plan_id': plan_id}])", 1),
])

TEST = ROOT / 'tests' / 'test_audit_content_light.py'
if TEST.exists():
    raise SystemExit('fail closed: audit content-light test already exists')
TEST.write_text(r'''import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from audit_privacy import FORBIDDEN_AUDIT_KEYS
from engine import Agent, Tools
from file_intelligence import FileIntelligence
from file_manager import FileManager
from notebook import DIGEST_PREFIX, Notebook


class FakeModel:
    name = 'audit-test-model'
    def __init__(self, *responses):
        self.responses = iter(responses)
        self.calls = []
    def invoke(self, messages, timeout):
        self.calls.append(json.loads(json.dumps(messages)))
        value = next(self.responses)
        if isinstance(value, BaseException):
            raise value
        return value


class Classifier:
    name = 'audit-classifier'
    def structured(self, messages, timeout):
        return {'destination_folder': 'Private',
                'summary': 'SENSITIVE_CLASSIFICATION_SUMMARY_771',
                'rationale': 'SENSITIVE_CLASSIFICATION_RATIONALE_772',
                'confidence': .93}


class AuditContentLightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.book = Notebook(self.root / 'vault')
        self.book.recover()
        self.identity = self.book.bind('Jon', 'opening')
        self.workspace = self.root / 'workspace'; self.workspace.mkdir()
        self.core = self.root / 'core'; self.core.mkdir()

    def tearDown(self):
        self.book.close()
        self.tmp.cleanup()

    def events(self):
        return [json.loads(row[0]) for row in self.book.db.execute('SELECT payload FROM events')]

    def event_text(self):
        return '\n'.join(row[0] for row in self.book.db.execute('SELECT payload FROM events'))

    def test_append_guard_rejects_nested_raw_content_fields(self):
        for key in sorted(FORBIDDEN_AUDIT_KEYS):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'forbidden'):
                self.book.event('guard', 'TEST', {'nested': {key: 'payload'}})
        self.assertEqual(self.book.db.execute("SELECT COUNT(*) FROM events WHERE tx='guard'").fetchone()[0], 0)

    def test_context_model_and_read_payload_never_enter_event_chain(self):
        context_secret = 'CONTEXT_SECRET_984211'
        file_secret = 'WORKSPACE_SECRET_984212'
        final_secret = 'MODEL_FINAL_SECRET_984213'
        (self.core / 'selected.md').write_text(context_secret)
        (self.workspace / 'note.txt').write_text(file_secret)
        model = FakeModel({'tool': {'name': 'read_file', 'path': 'note.txt'}},
                          {'final': final_secret})
        agent = Agent(self.book, model, Tools(self.workspace), self.core)
        self.assertEqual(agent.run('turn', self.identity['hcid'], 'read note.txt', context=('selected.md',)), final_secret)
        ledger = self.event_text()
        for secret in (context_secret, file_secret, final_secret):
            self.assertNotIn(secret, ledger)
            self.assertNotIn(hashlib.sha256(secret.encode()).hexdigest(), ledger)
        self.assertIn(file_secret, json.dumps(self.book.task('turn')))
        self.assertIn(final_secret, self.book.db.execute(
            "SELECT text FROM transcript WHERE tx='turn' AND role='ASSISTANT'").fetchone()[0])
        for kind in ('CONTEXT_LOADED', 'MODEL_RESPONSE', 'TOOL_REQUEST', 'AUTHORIZATION', 'TOOL_RESULT'):
            payload = json.loads(self.book.db.execute(
                'SELECT payload FROM events WHERE tx=? AND kind=? ORDER BY seq DESC LIMIT 1', ('turn', kind)).fetchone()[0])
            self.assertTrue(any(isinstance(v, str) and v.startswith(DIGEST_PREFIX)
                                for v in _strings(payload)), (kind, payload))

    def test_create_content_is_bound_but_not_persisted_in_events(self):
        secret = 'CREATE_FILE_SECRET_550031'
        model = FakeModel({'tool': {'name': 'create_file', 'path': 'created.txt', 'content': secret}},
                          {'final': 'created'})
        agent = Agent(self.book, model, Tools(self.workspace), self.core, authorize=lambda request: True)
        self.assertEqual(agent.run('create', self.identity['hcid'], 'create the requested file'), 'created')
        self.assertEqual((self.workspace / 'created.txt').read_text(), secret)
        ledger = self.event_text()
        self.assertNotIn(secret, ledger)
        self.assertNotIn(hashlib.sha256(secret.encode()).hexdigest(), ledger)
        authorization = json.loads(self.book.db.execute(
            "SELECT payload FROM events WHERE tx='create' AND kind='AUTHORIZATION'").fetchone()[0])
        self.assertNotIn('content', authorization)
        self.assertTrue(authorization['content_digest'].startswith(DIGEST_PREFIX))
        self.assertTrue(authorization['request_digest'].startswith(DIGEST_PREFIX))

    def test_invalid_model_payload_is_not_echoed_into_rejection_event(self):
        secret = 'INVALID_MODEL_SECRET_220119'
        model = FakeModel({'bad': secret}, {'final': 'repaired'})
        agent = Agent(self.book, model, Tools(self.workspace), self.core)
        self.assertEqual(agent.run('invalid', self.identity['hcid'], 'hello'), 'repaired')
        payload = json.loads(self.book.db.execute(
            "SELECT payload FROM events WHERE tx='invalid' AND kind='MODEL_RESPONSE_REJECTED'").fetchone()[0])
        self.assertNotIn(secret, json.dumps(payload))
        self.assertEqual(payload['error_type'], 'ValueError')
        self.assertTrue(payload['error_digest'].startswith(DIGEST_PREFIX))

    def test_file_classification_and_plan_events_keep_only_proofs(self):
        secret = 'FILE_EXCERPT_SECRET_330117'
        (self.workspace / 'mystery.txt').write_text(secret)
        manager = FileManager(self.workspace, self.book)
        plan = FileIntelligence(manager, Classifier()).plan('.', 'classification')
        self.assertEqual(plan['status'], 'PREVIEW')
        ledger = self.event_text()
        for leaked in (secret, 'SENSITIVE_CLASSIFICATION_SUMMARY_771',
                       'SENSITIVE_CLASSIFICATION_RATIONALE_772'):
            self.assertNotIn(leaked, ledger)
        created = json.loads(self.book.db.execute(
            "SELECT payload FROM events WHERE kind='FILE_PLAN_CREATED'").fetchone()[0])
        self.assertEqual(created['plan_id'], plan['plan_id'])
        self.assertNotIn('plan', created)
        self.assertTrue(created['plan_digest'].startswith(DIGEST_PREFIX))
        response = json.loads(self.book.db.execute(
            "SELECT payload FROM events WHERE kind='FILE_CLASSIFICATION_RESPONSE'").fetchone()[0])
        self.assertNotIn('decision', response)
        self.assertTrue(response['decision_digest'].startswith(DIGEST_PREFIX))

    def test_deleting_source_payload_leaves_no_plaintext_in_append_only_ledger(self):
        secret = 'DELETABLE_CONTEXT_SECRET_941772'
        selected = self.core / 'selected.md'; selected.write_text(secret)
        agent = Agent(self.book, FakeModel({'final': 'ok'}), Tools(self.workspace), self.core)
        agent.run('delete-proof', self.identity['hcid'], 'use selected context', context=('selected.md',))
        selected.unlink()
        self.assertFalse(selected.exists())
        self.assertNotIn(secret, self.event_text())
        context_event = json.loads(self.book.db.execute(
            "SELECT payload FROM events WHERE tx='delete-proof' AND kind='CONTEXT_LOADED'").fetchone()[0])
        self.assertTrue(context_event['records'][0]['content_digest'].startswith(DIGEST_PREFIX))
        self.assertEqual(context_event['records'][0]['content_bytes'], len(secret.encode()))


def _strings(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)
    elif isinstance(value, str):
        yield value


if __name__ == '__main__':
    unittest.main()
''', encoding='utf-8')

print('patched notebook.py, engine.py, file_manager.py, file_intelligence.py, tests; added audit tests')
