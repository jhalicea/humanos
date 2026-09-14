#!/usr/bin/env python3
"""Runnable HumanOS Capture MCP server.

Run with the current official MCP Python SDK v2, for example:

    HUMANOS_CAPTURE_DATABASE_URL='postgresql://...' mcp run capture_mcp_server.py

or deploy it with the SDK's Streamable HTTP transport. The database credential
should be the dedicated ``humanos_capture_writer`` role, which has EXECUTE on
one append function and no underlying table privileges.
"""

from __future__ import annotations

import os
from typing import Any

from mcp.server import MCPServer

from capture_fabric import CaptureGateway
from capture_postgres import PostgresCaptureRelay


mcp = MCPServer('HumanOS Capture')
_gateway: CaptureGateway | None = None


def gateway() -> CaptureGateway:
    global _gateway
    if _gateway is None:
        dsn = os.environ.get('HUMANOS_CAPTURE_DATABASE_URL', '')
        if not dsn:
            raise RuntimeError('HUMANOS_CAPTURE_DATABASE_URL is not configured')
        relay = PostgresCaptureRelay(dsn)
        _gateway = CaptureGateway(relay.append)
    return _gateway


@mcp.tool()
def humanos_append_capture_event(event: dict[str, Any]) -> dict[str, Any]:
    """Append one exact immutable conversation event to HumanOS.

    A repeated idempotency key with the identical event is safe. A repeated key
    with different content fails closed. This tool cannot read, update, delete,
    search, or administer the HumanOS database.
    """
    return gateway().append_event(event)
