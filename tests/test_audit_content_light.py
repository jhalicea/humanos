import hashlib
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
