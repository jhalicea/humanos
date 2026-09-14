import importlib.util
import unittest

from capture_fabric import CaptureEvent
from capture_encryption import (
    CaptureEncryptionError,
    ciphertext_digest,
    decrypt_event,
    encrypt_event,
    generate_recipient_keypair,
)


@unittest.skipUnless(importlib.util.find_spec('cryptography'), 'cryptography not installed')
class CaptureEncryptionTests(unittest.TestCase):
    def event(self, **changes):
        value = dict(
            source='chatgpt',
            conversation_id='conversation-α',
            turn_id='turn-1',
            event_type='human_message',
            role='human',
            text='  exact text 🧭\nsecond line  ',
            idempotency_key='chatgpt/conversation-α/turn-1/human/primary',
            variant_id='primary',
            source_created_at=None,
        )
        value.update(changes)
        return CaptureEvent(**value).validated()

    def test_round_trip_preserves_exact_text_and_metadata(self):
        private_key, public_key = generate_recipient_keypair()
        envelope = encrypt_event(self.event(), public_key, b't' * 32)
        self.assertNotIn('text', envelope)
        self.assertNotIn('conversation_id', envelope)
        restored = decrypt_event(envelope, private_key)
        self.assertEqual(restored, self.event())
        self.assertEqual(restored.text, '  exact text 🧭\nsecond line  ')
        self.assertEqual(len(ciphertext_digest(envelope)), 64)

    def test_same_event_reencrypts_differently_but_tokens_stay_stable(self):
        private_key, public_key = generate_recipient_keypair()
        first = encrypt_event(self.event(), public_key, b't' * 32)
        second = encrypt_event(self.event(), public_key, b't' * 32)
        self.assertEqual(first['idempotency_token'], second['idempotency_token'])
        self.assertEqual(first['conflict_token'], second['conflict_token'])
        self.assertNotEqual(first['ciphertext'], second['ciphertext'])
        self.assertEqual(decrypt_event(first, private_key), decrypt_event(second, private_key))

    def test_changed_plaintext_changes_conflict_token(self):
        _, public_key = generate_recipient_keypair()
        first = encrypt_event(self.event(), public_key, b't' * 32)
        second = encrypt_event(self.event(text='different'), public_key, b't' * 32)
        self.assertEqual(first['idempotency_token'], second['idempotency_token'])
        self.assertNotEqual(first['conflict_token'], second['conflict_token'])

    def test_tampering_fails_authenticated_decryption(self):
        private_key, public_key = generate_recipient_keypair()
        envelope = encrypt_event(self.event(), public_key, b't' * 32)
        envelope['conflict_token'] = '0' * 64
        with self.assertRaisesRegex(CaptureEncryptionError, 'authentication/decryption failed'):
            decrypt_event(envelope, private_key)

    def test_wrong_private_key_fails_closed(self):
        _, public_key = generate_recipient_keypair()
        wrong_private, _ = generate_recipient_keypair()
        envelope = encrypt_event(self.event(), public_key, b't' * 32)
        with self.assertRaisesRegex(CaptureEncryptionError, 'different recipient key'):
            decrypt_event(envelope, wrong_private)


if __name__ == '__main__':
    unittest.main()
