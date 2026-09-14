#!/usr/bin/env python3
"""Runnable encrypted HumanOS Capture MCP server.

Production remote capture is fail-closed: the MCP writer requires a dedicated
least-privilege PostgreSQL credential, an owner-controlled X25519 *public* key,
and a separate relay token secret. The matching private key is never present on
the remote service.

Required environment variables:

    HUMANOS_CAPTURE_DATABASE_URL
    HUMANOS_CAPTURE_RECIPIENT_PUBLIC_KEY_B64
    HUMANOS_CAPTURE_TOKEN_SECRET_B64

The database stores encrypted envelopes only. The gateway sees tool input
transiently in process memory because it receives the provider request, but this
module does not log message bodies or expose read/search/delete/admin tools.
"""

from __future__ import annotations

import os
from typing import Any

from mcp.server import MCPServer

from capture_encryption import decode_public_key_b64, decode_secret_b64
from capture_fabric import CaptureEvent
from capture_secure_postgres import EncryptedPostgresCaptureWriter


mcp = MCPServer('HumanOS Capture')
_writer: EncryptedPostgresCaptureWriter | None = None


def writer() -> EncryptedPostgresCaptureWriter:
    global _writer
    if _writer is None:
        dsn = os.environ.get('HUMANOS_CAPTURE_DATABASE_URL', '')
        public_b64 = os.environ.get('HUMANOS_CAPTURE_RECIPIENT_PUBLIC_KEY_B64', '')
        token_b64 = os.environ.get('HUMANOS_CAPTURE_TOKEN_SECRET_B64', '')
        missing = [name for name, value in (
            ('HUMANOS_CAPTURE_DATABASE_URL', dsn),
            ('HUMANOS_CAPTURE_RECIPIENT_PUBLIC_KEY_B64', public_b64),
            ('HUMANOS_CAPTURE_TOKEN_SECRET_B64', token_b64),
        ) if not value]
        if missing:
            raise RuntimeError('Encrypted capture is not configured: missing ' + ', '.join(missing))
        _writer = EncryptedPostgresCaptureWriter(
            dsn,
            decode_public_key_b64(public_b64),
            decode_secret_b64(token_b64),
        )
    return _writer


@mcp.tool()
def humanos_append_capture_event(event: dict[str, Any]) -> dict[str, Any]:
    """Encrypt and append one immutable conversation event to HumanOS.

    The tool can append only. It cannot read, update, delete, search, decrypt,
    or administer HumanOS. The remote database receives ciphertext rather than
    plaintext transcript content.
    """
    validated = CaptureEvent.from_mapping(event)
    receipt = writer().append(validated)
    return {
        'seq': receipt.seq,
        'event_id': receipt.event_id,
        'ciphertext_digest': receipt.payload_digest,
        'received_at': receipt.received_at,
        'state': receipt.state,
    }
