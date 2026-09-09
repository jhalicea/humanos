import tempfile
import time
import unittest
from pathlib import Path
from browser_bridge import BrowserBroker, BrowserEnvelope


def envelope(**changes):
    value = {'run_id': 'browser-test', 'authorization': 'owner test authority',
             'expires': int(time.time()) + 60, 'hosts': ['example.com'],
             'capabilities': ['inspect', 'navigate', 'click', 'type', 'scroll', 'screenshot', 'download'],
             'max_actions': 10, 'max_bytes': 100000}
    value.update(changes); return value


class BrowserBrokerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.calls = []
        self.approvals = []
        self.broker = BrowserBroker(envelope(), Path(self.temp.name) / 'state', self.calls.append,
                                    approve=lambda value: self.approvals.append(value) or True)

    def tearDown(self): self.temp.cleanup()

    def call(self, tool, args={}): return self.broker.execute({'tool': tool, 'tab_id': 7, 'arguments': args})

    def test_read_only_needs_no_approval_and_is_audited(self):
        self.assertTrue(self.call('inspect')['ok']); self.assertEqual(self.approvals, [])
        self.assertEqual(self.calls, [{'tool': 'inspect', 'tab_id': 7, 'arguments': {}}])
        self.assertEqual(len((Path(self.temp.name) / 'state' / 'ledger' / 'actions.jsonl').read_text().splitlines()), 2)

    def test_powerful_actions_are_capable_and_approved(self):
        for tool, args in [('navigate', {'url':'https://example.com/a'}), ('click', {'selector':'button.pay'}),
                           ('type', {'selector':'textarea', 'text':'draft'}), ('scroll', {'x':1, 'y':2}),
                           ('download', {'url':'https://example.com/a.zip'})]:
            self.assertTrue(self.call(tool, args)['ok'])
        self.assertEqual(len(self.approvals), 4)

    def test_denial_happens_before_extension(self):
        for tool, args in [('navigate', {'url':'http://example.com'}), ('navigate', {'url':'https://evil.example'}),
                           ('shell', {}), ('click', {'selector':'x', 'extra':1})]:
            self.assertFalse(self.call(tool, args)['ok'])
        self.assertEqual(self.calls, [])

    def test_no_approval_means_no_effect(self):
        self.broker.approve = lambda _: False
        self.assertFalse(self.call('click', {'selector':'button'})['ok'])
        self.assertEqual(self.calls, [])

    def test_kill_budget_and_expiry_deny(self):
        self.broker.stop(); self.assertFalse(self.call('inspect')['ok'])
        short = BrowserBroker(envelope(max_actions=1), Path(self.temp.name) / 'short', lambda _: {})
        self.assertTrue(short.execute({'tool':'inspect','tab_id':1,'arguments':{}})['ok'])
        self.assertFalse(short.execute({'tool':'inspect','tab_id':1,'arguments':{}})['ok'])
        with self.assertRaises(ValueError):
            BrowserBroker(envelope(expires=int(time.time())-1), Path(self.temp.name) / 'expired', lambda _: {})

    def test_immutable_envelope_and_tab_identity(self):
        source = envelope(); broker = BrowserBroker(source, Path(self.temp.name) / 'immutable', lambda _: {}, approve=lambda _: True)
        source['hosts'].clear(); self.assertTrue(broker.execute({'tool':'navigate','tab_id':1,'arguments':{'url':'https://example.com'}})['ok'])
        self.assertFalse(broker.execute({'tool':'inspect','tab_id':True,'arguments':{}})['ok'])

    def test_invalid_envelope_rejected(self):
        for change in ({'hosts': []}, {'capabilities':['shell']}, {'max_actions':0}, {'expires':int(time.time())-1}):
            with self.assertRaises(ValueError): BrowserEnvelope(envelope(**change))

    def test_audit_tamper_stops_the_next_action_before_effect(self):
        self.assertTrue(self.call('inspect')['ok'])
        path = Path(self.temp.name) / 'state' / 'ledger' / 'actions.jsonl'
        path.write_text('{}\n')
        with self.assertRaises((PermissionError, ValueError)):
            self.call('inspect')
        self.assertEqual(len(self.calls), 1)
