"""Universal Conversation Capture for HumanOS.

This module preserves exact visible conversation turns from any supported host
(ChatGPT, Claude, Gemini, Grok, a local model UI, or an import adapter) without
calling an AI model just to save the transcript.

The Life Notebook remains the source of truth. Each host supplies a stable
conversation ID and turn ID. HumanOS derives a vault-keyed local transaction ID,
so retries are idempotent without exposing raw provider identifiers in the audit
stream.

The internal pending phase remains ``EXTERNAL_CAPTURE_PENDING`` for compatibility
with the existing Runtime 0.1 recovery rules. Here, "external" means only
"outside the local HumanOS runtime"; the public feature name is Universal
Conversation Capture.
"""

from notebook import now


CAPTURE_VERSION = 1
PENDING = 'EXTERNAL_CAPTURE_PENDING'
COMPLETE = 'COMPLETE'
HOST_DELIVERY = 'WRITTEN_TO_OUTPUT_STREAM'
HOST_DELIVERY_ORIGIN = 'EXTERNAL_HOST_CAPTURE'


def _required_text(name, value, max_length=None):
    if not isinstance(value, str) or not value:
        raise ValueError(name + ' must be a nonempty string')
    if max_length is not None and len(value) > max_length:
        raise ValueError(name + ' is too long')
    return value


class UniversalConversationCapture:
    """Persist exact host conversation turns into the Life Notebook.

    ``source`` identifies the host, for example ``chatgpt`` or ``claude``.
    ``conversation_id`` and ``turn_id`` are host-owned stable identifiers. They
    are never copied raw into the audit event stream. HumanOS derives a keyed
    local digest from them, so the same host turn is idempotent without exposing
    upstream identifiers in public projections or content-light audit records.
    """

    def __init__(self, book, source='chatgpt'):
        self.book = book
        self.source = _required_text('source', source, 64)

    def _host_key(self, conversation_id, turn_id):
        conversation_id = _required_text('conversation_id', conversation_id, 512)
        turn_id = _required_text('turn_id', turn_id, 512)
        material = self.source + '\x00' + conversation_id + '\x00' + turn_id
        return self.book.content_digest(material)

    def _tx(self, host_key_digest):
        # HMAC hex is stable inside this vault but not linkable across vaults.
        return 'EXT-' + host_key_digest.rsplit(':', 1)[-1][:40]

    def begin_turn(self, hcid, conversation_id, turn_id, human_text):
        """Persist and read back the exact human message before later processing.

        Safe to retry with the same identifiers and exact text. A conflicting
        retry fails closed through Notebook.start rather than altering evidence.
        No model call occurs here.
        """
        _required_text('hcid', hcid, 256)
        if not isinstance(human_text, str):
            raise ValueError('human_text must be a string')

        host_key = self._host_key(conversation_id, turn_id)
        tx = self._tx(host_key)
        self.book.start(hcid, tx, human_text)

        state = self.book.task(tx)
        if state is not None:
            if state.get('capture_version') != CAPTURE_VERSION:
                raise RuntimeError('Conversation capture version differs from preserved state')
            if state.get('source') != self.source or state.get('external_key_digest') != host_key:
                raise RuntimeError('Conversation capture identity differs from preserved state')
            if state.get('phase') not in (PENDING, COMPLETE):
                raise RuntimeError('Transaction already belongs to a different task state')
            self.book.verify()
            return tx

        state = {
            'phase': PENDING,
            'capture_version': CAPTURE_VERSION,
            'source': self.source,
            # Keep the historical field name for Runtime 0.1 compatibility.
            'external_key_digest': host_key,
            'human_ordinal': 0,
            'capture_started': now(),
        }
        self.book.save_task_event(tx, state, 'EXTERNAL_CAPTURE_STARTED', {
            'source': self.source,
            'capture_version': CAPTURE_VERSION,
            'external_key_digest': host_key,
            'human_digest': self.book.content_digest(human_text),
        })
        # start() already projected/read back the human text. Verify again after
        # durable capture-state evidence so a successful return means the whole
        # capture boundary is internally consistent.
        self.book.verify()
        return tx

    def finish_turn(self, tx, assistant_text):
        """Append the exact visible assistant message and checkpoint the turn.

        A retry after a crash between transcript append and state update reuses
        the already-preserved assistant row when the exact text matches. No model
        call occurs here.
        """
        _required_text('tx', tx, 256)
        if not isinstance(assistant_text, str):
            raise ValueError('assistant_text must be a string')

        transaction = self.book.get_transaction(tx)
        if transaction is None:
            raise ValueError('Unknown conversation capture transaction')
        state = self.book.task(tx)
        if state is None or state.get('capture_version') != CAPTURE_VERSION:
            raise RuntimeError('Conversation capture state is missing or incompatible')
        if state.get('source') != self.source:
            raise RuntimeError('Conversation capture source differs from preserved state')

        if state.get('phase') == COMPLETE:
            if (state.get('delivery_origin') != HOST_DELIVERY_ORIGIN or
                    state.get('final') != assistant_text or state.get('final_ordinal') != 1):
                raise ValueError('Completed conversation capture differs from preserved evidence')
            self.book.checkpoint(tx)
            return tx
        if state.get('phase') != PENDING:
            raise RuntimeError('Conversation capture is not waiting for an assistant message')

        count = self.book.message_count(tx)
        if count == 1:
            self.book.append(tx, 1, 'ASSISTANT', assistant_text)
        elif count == 2:
            prior = self.book.db.execute(
                'SELECT role,text FROM transcript WHERE tx=? AND ordinal=1', (tx,)
            ).fetchone()
            if not prior or prior['role'] != 'ASSISTANT' or prior['text'] != assistant_text:
                raise ValueError('Assistant retry differs from preserved transcript evidence')
        else:
            raise RuntimeError('Conversation turn contains an unexpected transcript shape')

        state = dict(state)
        state.update(
            phase=COMPLETE,
            final=assistant_text,
            final_ordinal=1,
            delivery=HOST_DELIVERY,
            delivery_origin=HOST_DELIVERY_ORIGIN,
            capture_finished=now(),
        )
        self.book.save_task_event(tx, state, 'EXTERNAL_CAPTURE_COMPLETED', {
            'source': self.source,
            'capture_version': CAPTURE_VERSION,
            'assistant_digest': self.book.content_digest(assistant_text),
            'delivery_origin': HOST_DELIVERY_ORIGIN,
        })
        self.book.checkpoint(tx)
        return tx

    def capture_turn(self, hcid, conversation_id, turn_id, human_text, assistant_text):
        """Capture an already-complete human/assistant turn exactly once."""
        tx = self.begin_turn(hcid, conversation_id, turn_id, human_text)
        return self.finish_turn(tx, assistant_text)

