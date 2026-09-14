"""Backward-compatible import surface for early capture prototypes.

The public feature is now Universal Conversation Capture. New code should import
``UniversalConversationCapture`` from ``conversation_capture``. These aliases
remain so existing Runtime 0.1 tests and any early adapters do not break while
the feature is promoted.
"""

from conversation_capture import (
    CAPTURE_VERSION,
    COMPLETE,
    HOST_DELIVERY,
    HOST_DELIVERY_ORIGIN,
    PENDING,
    UniversalConversationCapture,
)


ExternalTurnCapture = UniversalConversationCapture
EXTERNAL_DELIVERY = HOST_DELIVERY
EXTERNAL_DELIVERY_ORIGIN = HOST_DELIVERY_ORIGIN


__all__ = [
    'CAPTURE_VERSION',
    'PENDING',
    'COMPLETE',
    'EXTERNAL_DELIVERY',
    'EXTERNAL_DELIVERY_ORIGIN',
    'ExternalTurnCapture',
]
