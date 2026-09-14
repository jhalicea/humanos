#!/usr/bin/env python3
"""Least-privilege HumanOS Capture MCP application layer.

This file intentionally contains no MCP SDK dependency.  It is the transport-
neutral application layer an MCP server wrapper exposes.  That keeps HumanOS
independent of a particular MCP library/version while giving every wrapper the
same tiny authority surface.

Writer-facing MCP surface:
    humanos_append_capture_event(event)

Reader/importer operations are deliberately not exposed to conversational AI
writers.  Local HumanOS synchronization uses its own reader credential/path.
"""

from __future__ import annotations

from typing import Any, Mapping

from capture_fabric import CaptureGateway


APPEND_TOOL = {
    'name': 'humanos_append_capture_event',
    'description': (
        'Append one exact immutable conversation event to the HumanOS remote '
        'capture relay. Repeating the same idempotency key and exact payload is '
        'safe; changing the payload under the same key fails closed.'
    ),
    'inputSchema': {
        'type': 'object',
        'additionalProperties': False,
        'required': ['event'],
        'properties': {
            'event': {
                'type': 'object',
                'additionalProperties': False,
                'required': [
                    'version', 'source', 'conversation_id', 'turn_id',
                    'event_type', 'role', 'text', 'idempotency_key',
                    'variant_id', 'source_created_at',
                ],
                'properties': {
                    'version': {'const': 1},
                    'source': {'type': 'string', 'minLength': 1, 'maxLength': 128},
                    'conversation_id': {'type': 'string', 'minLength': 1, 'maxLength': 4096},
                    'turn_id': {'type': 'string', 'minLength': 1, 'maxLength': 4096},
                    'event_type': {
                        'enum': [
                            'human_message', 'assistant_message',
                            'human_edit', 'assistant_regeneration',
                        ]
                    },
                    'role': {'enum': ['human', 'assistant']},
                    'text': {'type': 'string', 'minLength': 1},
                    'idempotency_key': {'type': 'string', 'minLength': 1, 'maxLength': 4096},
                    'variant_id': {'type': 'string', 'minLength': 1, 'maxLength': 4096},
                    'source_created_at': {'type': ['string', 'null']},
                },
            }
        },
    },
}


class HumanOSCaptureMCP:
    """Minimal authority surface intended to sit behind an MCP transport."""

    def __init__(self, gateway: CaptureGateway):
        self.gateway = gateway

    def list_tools(self) -> list[dict[str, Any]]:
        return [APPEND_TOOL]

    def call_tool(self, name: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
        if name != APPEND_TOOL['name']:
            raise PermissionError('Unknown or unauthorized HumanOS capture tool')
        if not isinstance(arguments, Mapping) or set(arguments) != {'event'}:
            raise ValueError('MCP append call requires exactly one event field')
        if not isinstance(arguments['event'], Mapping):
            raise ValueError('event must be an object')
        return self.gateway.append_event(arguments['event'])
