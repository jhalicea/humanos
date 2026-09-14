"""Token-free exact transcript ingress for external conversation hosts.

This module is intentionally model-free. A host (for example a browser bridge,
ChatGPT integration, or later import worker) calls ``begin_turn`` as soon as the
human message is available, then ``finish_turn`` after the visible assistant
message is available. The Life Notebook remains the source of truth.

Storage and verification use the existing Notebook primitives:
- exact visible text is append-only;
- every human input is projected and read back before capture begins;
- the assistant response is appended once, then checkpointed and verified;
- retries are idempotent when the external turn identity and text are unchanged;
- interrupted turns remain ``EXTERNAL_CAPTURE_PENDING`` and are never treated as
  model work by the local runtime.

No model call, summary generation, or token-bearing inference is required for
this capture lane.
"""

from notebook import now


CAPTURE_VERSION = 1
PENDING = 'EXTERNAL_CAPTURE_PENDING'
COMPLETE = 'COMPLETE'
EXTERNAL_DELIVERY = 'WRITTEN_TO_OUTPUT_STREAM'
EXTERNAL_DELIVERY_ORIGIN = 'EXTERNAL_HOST_CAPTURE'


def _required_text(name, value, max_length=None):
    if not isinstance(value, str) or not value:
        raise ValueError(name + ' must be a nonempty string')
    if max_length is not None and len(value) > max_length:
        raise ValueError(name + ' is too long')
    return value


class ExternalTurnCapture:
    """Bridge exact external conversation turns into the Life Notebook.

    ``conversation_id`` and ``turn_id`` are host-owned stable identifiers. They
    are never copied into the audit event stream. HumanOS derives a keyed local
    digest from them, so the same host turn is idempotent without exposing the
    upstream identifiers in public projections or content-light audit records.
    """

    def __init__(self, book, source='chatgpt'):
        self.book = book
        self.source = _required_text('source', source, 64)

    def _external_key(self, conversation_id, turn_id):
        conversation_id = _required_text('conversation_id', conversation_id, 512)
        turn_id = _required_text('turn_id', turn_id, 512)
        material = self.source + '\x00' + conversation_id + '\x00' + turn_id
        return self.book.content_digest(material)

    def _tx(self, external_key_digest):
        # HMAC hex is stable inside this vault but not linkable across vaults.
        return 'EXT-' + external_key_digest.rsplit(':', 1)[-1][:40]

    def begin_turn(self, hcid, conversation_id, turn_id, human_text):
        """Persist and read back the exact human message before model work.

        Safe to retry with the same identifiers and exact text. A conflicting
        retry fails closed through Notebook.start rather than altering evidence.
        """
        _required_text('hcid', hcid, 256)
        if not isinstance(human_text, str):
            raise ValueError('human_text must be a string')

        external_key = self._external_key(conversation_id, turn_id)
        tx = self._tx(external_key)
        self.book.start(hcid, tx, human_text)

        state = self.book.task(tx)
        if state is not None:
            if state.get('capture_version') != CAPTURE_VERSION:
                raise RuntimeError('External capture version differs from preserved state')
            if state.get('source') != self.source or state.get('external_key_digest') != external_key:
                raise RuntimeError('External capture identity differs from preserved state')
            if state.get('phase') not in (PENDING, COMPLETE):
                raise RuntimeError('Transaction already belongs to a different task state')
            self.book.verify()
            return tx

        state = {
            'phase': PENDING,
            'capture_version': CAPTURE_VERSION,
            'source': self.source,
            'external_key_digest': external_key,
            'human_ordinal': 0,
            'capture_started': now(),
        }
        self.book.save_task_event(tx, state, 'EXTERNAL_CAPTURE_STARTED', {
            'source': self.source,
            'capture_version': CAPTURE_VERSION,
            'external_key_digest': external_key,
            'human_digest': self.book.content_digest(human_text),
        })
        # start() already projected/read back the human text. Verify again after
        # durable capture-state evidence so a successful return means the whole
        # capture boundary is internally consistent.
        self.book.verify()
        return tx

    def finish_turn(self, tx, assistant_text):
        """Append the exact external assistant message and checkpoint the turn.

        A retry after a crash between transcript append and state update reuses
        the already-preserved assistant row when the exact text matches.
        """
        _required_text('tx', tx, 256)
        if not isinstance(assistant_text, str):
            raise ValueError('assistant_text must be a string')

        transaction = self.book.get_transaction(tx)
        if transaction is None:
            raise ValueError('Unknown external capture transaction')
        state = self.book.task(tx)
        if state is None or state.get('capture_version') != CAPTURE_VERSION:
            raise RuntimeError('External capture state is missing or incompatible')
        if state.get('source') != self.source:
            raise RuntimeError('External capture source differs from preserved state')

        if state.get('phase') == COMPLETE:
            if (state.get('delivery_origin') != EXTERNAL_DELIVERY_ORIGIN or
                    state.get('final') != assistant_text or state.get('final_ordinal') != 1):
                raise ValueError('Completed external capture differs from preserved evidence')
            self.book.checkpoint(tx)
            return tx
        if state.get('phase') != PENDING:
            raise RuntimeError('External capture is not waiting for an assistant message')

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
            raise RuntimeError('External turn contains an unexpected transcript shape')

        state = dict(state)
        state.update(
            phase=COMPLETE,
            final=assistant_text,
            final_ordinal=1,
            delivery=EXTERNAL_DELIVERY,
            delivery_origin=EXTERNAL_DELIVERY_ORIGIN,
            capture_finished=now(),
        )
        self.book.save_task_event(tx, state, 'EXTERNAL_CAPTURE_COMPLETED', {
            'source': self.source,
            'capture_version': CAPTURE_VERSION,
            'assistant_digest': self.book.content_digest(assistant_text),
            'delivery_origin': EXTERNAL_DELIVERY_ORIGIN,
        })
        self.book.checkpoint(tx)
        return tx

    def capture_turn(self, hcid, conversation_id, turn_id, human_text, assistant_text):
        """Convenience method for hosts that receive an already-complete turn."""
        tx = self.begin_turn(hcid, conversation_id, turn_id, human_text)
        return self.finish_turn(tx, assistant_text)
