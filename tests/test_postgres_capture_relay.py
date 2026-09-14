import os
import unittest

from capture_fabric import CaptureEvent
from postgres_capture_relay import PostgresCaptureRelay


@unittest.skipUnless(os.environ.get('HUMANOS_TEST_POSTGRES_DSN'), 'Postgres relay DSN not configured')
class PostgresCaptureRelayTests(unittest.TestCase):
    def setUp(self):
        self.relay = PostgresCaptureRelay(os.environ['HUMANOS_TEST_POSTGRES_DSN'])

    def tearDown(self):
        self.relay.close()

    def test_python_postgres_round_trip_and_retry(self):
        event = CaptureEvent(
            source='chatgpt',
            conversation_id='python-integration-conversation',
            turn_id='turn-1',
            event_type='human_message',
            role='human',
            text='  exact from Python 🧭\nline two  ',
            idempotency_key='python-integration/conversation/turn-1/human/primary',
            variant_id='primary',
        )
        first = self.relay.append(event)
        second = self.relay.append(event)
        self.assertEqual(first, second)
        self.assertEqual(first.payload_digest, event.digest())

        rows = self.relay.after(first.seq - 1, 10)
        matching = [(receipt, captured) for receipt, captured in rows if receipt.seq == first.seq]
        self.assertEqual(len(matching), 1)
        receipt, captured = matching[0]
        self.assertEqual(receipt.payload_digest, event.digest())
        self.assertEqual(captured.text, event.text)
        self.assertEqual(captured.payload(), event.payload())


if __name__ == '__main__':
    unittest.main()
