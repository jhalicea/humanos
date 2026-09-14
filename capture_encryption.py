#!/usr/bin/env python3
"""Application-level encryption for HumanOS remote capture.

Remote services receive only an owner-controlled *public* X25519 key. The
matching private key remains local to HumanOS and is required to decrypt remote
capture envelopes before they enter the local mirror/Life Notebook.

The remote gateway still sees the incoming message transiently because it must
receive the MCP/tool request, but the database never needs plaintext transcript
content. No private decryption key is stored in Render, Neon, GitHub, or the
public repository.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
import hashlib
import hmac
import json
import os
from pathlib import Path
import stat
from typing import Any, Mapping

from capture_fabric import CaptureEvent, canonical_json


ENVELOPE_FORMAT = 'humanos-capture-envelope'
ENVELOPE_VERSION = 1
KEY_INFO = b'HumanOS Capture Envelope v1|X25519+HKDF-SHA256+AES-256-GCM|'
PRIVATE_KEY_BYTES = 32
PUBLIC_KEY_BYTES = 32
NONCE_BYTES = 12
TOKEN_BYTES = 32
MAX_CIPHERTEXT_BYTES = 1_100_000


class CaptureEncryptionError(RuntimeError):
    pass


def _crypto():
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric.x25519 import (
            X25519PrivateKey,
            X25519PublicKey,
        )
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    except ImportError as error:
        raise CaptureEncryptionError(
            'Encrypted capture requires cryptography; install requirements-capture.txt'
        ) from error
    return hashes, serialization, X25519PrivateKey, X25519PublicKey, AESGCM, HKDF


def _b64e(raw: bytes) -> str:
    return base64.b64encode(raw).decode('ascii')


def _b64d(name: str, text: Any, expected: int | None = None) -> bytes:
    if not isinstance(text, str) or not text:
        raise CaptureEncryptionError(name + ' must be nonempty base64 text')
    try:
        raw = base64.b64decode(text, validate=True)
    except Exception as error:
        raise CaptureEncryptionError(name + ' is invalid base64') from error
    if expected is not None and len(raw) != expected:
        raise CaptureEncryptionError(name + ' has invalid length')
    return raw


def _hex_token(name: str, value: Any, length: int = 64) -> str:
    if not isinstance(value, str) or len(value) != length:
        raise CaptureEncryptionError(name + ' has invalid length')
    try:
        int(value, 16)
    except ValueError as error:
        raise CaptureEncryptionError(name + ' must be lowercase hex') from error
    if value != value.lower():
        raise CaptureEncryptionError(name + ' must be lowercase hex')
    return value


def recipient_key_id(public_key: bytes) -> str:
    if not isinstance(public_key, bytes) or len(public_key) != PUBLIC_KEY_BYTES:
        raise CaptureEncryptionError('recipient public key must be 32 raw bytes')
    return hashlib.sha256(public_key).hexdigest()[:32]


def generate_recipient_keypair() -> tuple[bytes, bytes]:
    """Return raw (private, public) X25519 key bytes."""
    _, serialization, X25519PrivateKey, _, _, _ = _crypto()
    private = X25519PrivateKey.generate()
    private_raw = private.private_bytes(
        serialization.Encoding.Raw,
        serialization.PrivateFormat.Raw,
        serialization.NoEncryption(),
    )
    public_raw = private.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    return private_raw, public_raw


def save_recipient_keypair(root: str | Path) -> dict[str, str]:
    """Create an owner-only local recipient keypair without overwriting keys."""
    root = Path(root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == 'posix':
        os.chmod(root, 0o700)
    private_path = root / 'capture-recipient.x25519.private'
    public_path = root / 'capture-recipient.x25519.public'
    if private_path.exists() or public_path.exists():
        raise CaptureEncryptionError('capture recipient key already exists; refusing overwrite')
    private_raw, public_raw = generate_recipient_keypair()
    private_path.write_bytes(private_raw)
    public_path.write_bytes(public_raw)
    if os.name == 'posix':
        os.chmod(private_path, 0o600)
        os.chmod(public_path, 0o600)
    return {
        'private_path': str(private_path),
        'public_path': str(public_path),
        'recipient_key_id': recipient_key_id(public_raw),
        'public_key_b64': _b64e(public_raw),
    }


def load_private_key(path: str | Path) -> bytes:
    path = Path(path).expanduser().resolve()
    info = path.lstat()
    if path.is_symlink() or not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise CaptureEncryptionError('capture private key must be one regular non-linked file')
    if os.name == 'posix':
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise CaptureEncryptionError('capture private key must be owner-only (0600)')
    raw = path.read_bytes()
    if len(raw) != PRIVATE_KEY_BYTES:
        raise CaptureEncryptionError('capture private key has invalid length')
    return raw


def derive_public_key(private_key: bytes) -> bytes:
    _, serialization, X25519PrivateKey, _, _, _ = _crypto()
    if not isinstance(private_key, bytes) or len(private_key) != PRIVATE_KEY_BYTES:
        raise CaptureEncryptionError('recipient private key must be 32 raw bytes')
    return X25519PrivateKey.from_private_bytes(private_key).public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )


def decode_public_key_b64(value: str) -> bytes:
    return _b64d('recipient public key', value, PUBLIC_KEY_BYTES)


def decode_secret_b64(value: str) -> bytes:
    raw = _b64d('relay token secret', value)
    if len(raw) < TOKEN_BYTES:
        raise CaptureEncryptionError('relay token secret must contain at least 32 bytes')
    return raw


def generate_secret_b64() -> str:
    return _b64e(os.urandom(TOKEN_BYTES))


def _idempotency_token(secret: bytes, event: CaptureEvent) -> str:
    return hmac.new(
        secret,
        b'HumanOS capture idempotency v1|' + event.idempotency_key.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()


def _conflict_token(secret: bytes, plaintext: bytes) -> str:
    return hmac.new(
        secret,
        b'HumanOS capture conflict v1|' + plaintext,
        hashlib.sha256,
    ).hexdigest()


def _aad(envelope: Mapping[str, Any]) -> bytes:
    protected = {
        'format': envelope['format'],
        'version': envelope['version'],
        'recipient_key_id': envelope['recipient_key_id'],
        'idempotency_token': envelope['idempotency_token'],
        'conflict_token': envelope['conflict_token'],
        'ephemeral_public_key': envelope['ephemeral_public_key'],
    }
    return canonical_json(protected).encode('utf-8')


def validate_envelope(value: Mapping[str, Any]) -> dict[str, Any]:
    expected = {
        'format', 'version', 'recipient_key_id', 'idempotency_token',
        'conflict_token', 'ephemeral_public_key', 'nonce', 'ciphertext',
    }
    if not isinstance(value, Mapping) or set(value) != expected:
        raise CaptureEncryptionError('unexpected or missing encrypted envelope fields')
    envelope = dict(value)
    if envelope['format'] != ENVELOPE_FORMAT or envelope['version'] != ENVELOPE_VERSION:
        raise CaptureEncryptionError('unsupported capture envelope format')
    _hex_token('recipient_key_id', envelope['recipient_key_id'], 32)
    _hex_token('idempotency_token', envelope['idempotency_token'])
    _hex_token('conflict_token', envelope['conflict_token'])
    _b64d('ephemeral_public_key', envelope['ephemeral_public_key'], PUBLIC_KEY_BYTES)
    _b64d('nonce', envelope['nonce'], NONCE_BYTES)
    ciphertext = _b64d('ciphertext', envelope['ciphertext'])
    if len(ciphertext) < 16 or len(ciphertext) > MAX_CIPHERTEXT_BYTES:
        raise CaptureEncryptionError('ciphertext size is invalid')
    return envelope


def encrypt_event(event: CaptureEvent, recipient_public_key: bytes,
                  relay_token_secret: bytes) -> dict[str, Any]:
    event = event.validated()
    if not isinstance(relay_token_secret, bytes) or len(relay_token_secret) < TOKEN_BYTES:
        raise CaptureEncryptionError('relay token secret must contain at least 32 bytes')
    hashes, serialization, X25519PrivateKey, X25519PublicKey, AESGCM, HKDF = _crypto()
    if not isinstance(recipient_public_key, bytes) or len(recipient_public_key) != PUBLIC_KEY_BYTES:
        raise CaptureEncryptionError('recipient public key must be 32 raw bytes')

    plaintext = canonical_json(event.payload()).encode('utf-8')
    ephemeral = X25519PrivateKey.generate()
    ephemeral_public = ephemeral.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )
    key_id = recipient_key_id(recipient_public_key)
    envelope = {
        'format': ENVELOPE_FORMAT,
        'version': ENVELOPE_VERSION,
        'recipient_key_id': key_id,
        'idempotency_token': _idempotency_token(relay_token_secret, event),
        'conflict_token': _conflict_token(relay_token_secret, plaintext),
        'ephemeral_public_key': _b64e(ephemeral_public),
        'nonce': '',
        'ciphertext': '',
    }

    shared = ephemeral.exchange(X25519PublicKey.from_public_bytes(recipient_public_key))
    key = HKDF(
        algorithm=hashes.SHA256(), length=32, salt=None,
        info=KEY_INFO + key_id.encode('ascii'),
    ).derive(shared)
    nonce = os.urandom(NONCE_BYTES)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, _aad(envelope))
    envelope['nonce'] = _b64e(nonce)
    envelope['ciphertext'] = _b64e(ciphertext)
    return validate_envelope(envelope)


def decrypt_event(envelope: Mapping[str, Any], recipient_private_key: bytes) -> CaptureEvent:
    envelope = validate_envelope(envelope)
    hashes, _, X25519PrivateKey, X25519PublicKey, AESGCM, HKDF = _crypto()
    if not isinstance(recipient_private_key, bytes) or len(recipient_private_key) != PRIVATE_KEY_BYTES:
        raise CaptureEncryptionError('recipient private key must be 32 raw bytes')
    public_key = derive_public_key(recipient_private_key)
    key_id = recipient_key_id(public_key)
    if not hmac.compare_digest(key_id, envelope['recipient_key_id']):
        raise CaptureEncryptionError('capture envelope targets a different recipient key')

    private = X25519PrivateKey.from_private_bytes(recipient_private_key)
    ephemeral_public = X25519PublicKey.from_public_bytes(
        _b64d('ephemeral_public_key', envelope['ephemeral_public_key'], PUBLIC_KEY_BYTES)
    )
    shared = private.exchange(ephemeral_public)
    key = HKDF(
        algorithm=hashes.SHA256(), length=32, salt=None,
        info=KEY_INFO + key_id.encode('ascii'),
    ).derive(shared)
    try:
        plaintext = AESGCM(key).decrypt(
            _b64d('nonce', envelope['nonce'], NONCE_BYTES),
            _b64d('ciphertext', envelope['ciphertext']),
            _aad(envelope),
        )
    except Exception as error:
        raise CaptureEncryptionError('capture envelope authentication/decryption failed') from error
    try:
        payload = json.loads(plaintext.decode('utf-8'))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CaptureEncryptionError('decrypted capture payload is not valid UTF-8 JSON') from error
    return CaptureEvent.from_mapping(payload)


def ciphertext_digest(envelope: Mapping[str, Any]) -> str:
    envelope = validate_envelope(envelope)
    return hashlib.sha256(_b64d('ciphertext', envelope['ciphertext'])).hexdigest()
