import importlib.util
import os
import unittest

from capture_encryption import generate_recipient_keypair
from capture_fabric import CaptureEvent
from capture_secure_postgres import (
    EncryptedPostgresCaptureReader,
    EncryptedPostgresCaptureWriter,
)


@unittest.skipUnless(importlib.util.find_spec('cryptography'), 'cryptography not installed')
@unittest.skipUnless(os.environ.get('HUMANOS_TEST_POSTGRES_DSN'), 'Postgres test DSN not configured')
class SecurePostgresCaptureTests(unittest.TestCase):
    def setUp(self):
        private_key, public_key = generate_recipient_keypair()
        dsn = os.environ['HUMANOS_TEST_POSTGRES_DSN']
        self.writer = EncryptedPostgresCaptureWriter(dsn, public_key, b'z' * 32)
        self.reader = EncryptedPostgresCaptureReader(dsn, private_key)

    def event(self, **changes):
        value = dict(
            source='chatgpt',
            conversation_id='secure-conversation-α',
            turn_id='turn-secure-1',
            event_type='human_message',
            role='human',
            text='  secret exact text 🛡️\nsecond line  ',
            idempotency_key='secure/test/event/1',
            variant_id='primary',
            source_created_at=None,
        )
        value.update(changes)
        return CaptureEvent(**value).validated()

    def test_encrypted_write_retry_read_and_decrypt(self):
        first = self.writer.append(self.event())
        second = self.writer.append(self.event())
        self.assertEqual(first.seq, second.seq)
        self.assertEqual(first.event_id, second.event_id)
        rows = self.reader.after(first.seq - 1, 10)
        self.assertEqual(len(rows), 1)
        receipt, event = rows[0]
        self.assertEqual(receipt.seq, first.seq)
        self.assertEqual(event.text, '  secret exact text 🛡️\nsecond line  ')
        self.assertEqual(event.conversation_id, 'secure-conversation-α')

    def test_conflicting_retry_fails_closed(self):
        self.writer.append(self.event())
        with self.assertRaises(Exception):
            self.writer.append(self.event(text='changed plaintext'))


if __name__ == '__main__':
    unittest.main()
