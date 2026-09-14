import hashlib
import hmac
import json
from pathlib import Path
import tempfile
import unittest

from capture_fabric import (
    CaptureEvent,
    CaptureGateway,
    ProviderWebhookIngress,
    SQLiteRelay,
    canonical_json,
    hmac_webhook_verifier,
)


class CaptureFabricTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.relay = SQLiteRelay(Path(self.tmp.name) / 'relay.sqlite3')
        self.gateway = CaptureGateway(self.relay.append)

    def tearDown(self):
        self.relay.close()
        self.tmp.cleanup()

    def event(self, **changes):
        value = {
            'version': 1,
            'source': 'chatgpt',
            'conversation_id': 'conversation-α',
            'turn_id': 'turn-1',
            'event_type': 'human_message',
            'role': 'human',
            'text': '  exact text 🧭\nsecond line  ',
            'idempotency_key': 'chatgpt/conversation-α/turn-1/human/primary',
            'variant_id': 'primary',
            'source_created_at': None,
        }
        value.update(changes)
        return value

    def test_exact_unicode_and_whitespace_round_trip(self):
        receipt = self.gateway.append_event(self.event())
        self.assertEqual(receipt['state'], 'REMOTE_CAPTURED')
        rows = self.relay.after(0)
        self.assertEqual(len(rows), 1)
        _, event = rows[0]
        self.assertEqual(event.text, '  exact text 🧭\nsecond line  ')

    def test_same_retry_is_idempotent(self):
        first = self.gateway.append_event(self.event())
        second = self.gateway.append_event(self.event())
        self.assertEqual(first, second)
        self.assertEqual(len(self.relay.after(0)), 1)

    def test_conflicting_retry_fails_closed(self):
        self.gateway.append_event(self.event())
        with self.assertRaisesRegex(ValueError, 'Conflicting retry'):
            self.gateway.append_event(self.event(text='different'))
        self.assertEqual(len(self.relay.after(0)), 1)

    def test_gateway_rejects_extra_fields(self):
        payload = self.event()
        payload['unexpected'] = 'nope'
        with self.assertRaisesRegex(ValueError, 'Unexpected or missing'):
            self.gateway.append_event(payload)

    def test_event_type_and_role_must_agree(self):
        with self.assertRaisesRegex(ValueError, 'Human event'):
            self.gateway.append_event(self.event(role='assistant'))
        with self.assertRaisesRegex(ValueError, 'Assistant event'):
            self.gateway.append_event(self.event(
                event_type='assistant_regeneration', role='human'))

    def test_append_only_table_rejects_update_and_delete(self):
        self.gateway.append_event(self.event())
        with self.assertRaises(Exception):
            with self.relay.db:
                self.relay.db.execute('UPDATE capture_events SET received_at=? WHERE seq=1', ('x',))
        with self.assertRaises(Exception):
            with self.relay.db:
                self.relay.db.execute('DELETE FROM capture_events WHERE seq=1')
        self.assertEqual(len(self.relay.after(0)), 1)

    def test_sequence_cursor_returns_only_newer_events(self):
        first = self.gateway.append_event(self.event())
        self.gateway.append_event(self.event(
            turn_id='turn-2',
            idempotency_key='chatgpt/conversation-α/turn-2/human/primary'))
        rows = self.relay.after(first['seq'])
        self.assertEqual([event.turn_id for _, event in rows], ['turn-2'])

    def test_webhook_signature_fails_closed_and_accepts_verified_body(self):
        secret = b's' * 32
        payload = self.event()
        body = canonical_json(payload).encode('utf-8')
        mapper = lambda raw: json.loads(raw.decode('utf-8'))
        ingress = ProviderWebhookIngress(
            self.gateway,
            hmac_webhook_verifier(secret),
            mapper,
        )
        with self.assertRaises(PermissionError):
            ingress.receive({'x-humanos-signature': 'bad'}, body)

        signature = hmac.new(secret, body, hashlib.sha256).hexdigest()
        receipt = ingress.receive({'X-HumanOS-Signature': signature}, body)
        self.assertEqual(receipt['state'], 'REMOTE_CAPTURED')
        self.assertEqual(len(self.relay.after(0)), 1)


if __name__ == '__main__':
    unittest.main()
