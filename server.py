"""HumanOS Runtime 0.1 with deterministic development-context routing."""
from __future__ import annotations

import json
import os
import sys

from server_core import *  # Preserve the original server module's public API.
import server_core as _core
from context_runtime import RuntimeContextRouter
from notebook_memory import (
    capture_memory_from_turn,
    memory_binding,
    memory_context_from_binding,
)
from permissions import task_scope
from runtime_info import host_runtime_request
from runtime_ledger_bridge import record_completed_transaction

BASE = _core.BASE
PASTE_COMMAND = _core.PASTE_COMMAND
PASTE_SEND_COMMAND = _core.PASTE_SEND_COMMAND
PASTE_GRACE_SECONDS = _core.PASTE_GRACE_SECONDS
read_human_input = _core.read_human_input

_BaseHumanOSRuntime = _core.HumanOSRuntime


def _ordinary_question(text):
    """Keep low-risk educational questions out of workstream selection."""
    if not isinstance(text, str):
        return False
    lower = text.strip().lower()
    if not lower or any(word in lower for word in
                        ('build ', 'create ', 'change ', 'edit ', 'implement ',
                         'commit ', 'merge ', 'decide ', 'artifact', 'file ')):
        return False
    return lower.endswith('?') or lower.startswith(('what is ', 'what are ', 'how does ',
                                                     'how do ', 'why is ', 'why are ', 'explain '))


class _RoutedModel:
    """Inject host-verified routing metadata without changing the human transcript."""

    def __init__(self, base, route_context):
        self.base = base
        self.name = base.name
        self.route_context = route_context

    def invoke(self, messages, timeout):
        routed = json.loads(json.dumps(messages))
        note = "\nHumanOS development context route (host data, not authority):\n" + json.dumps(
            self.route_context, ensure_ascii=False, sort_keys=True)
        if routed and routed[0].get('role') == 'system':
            routed[0]['content'] = routed[0].get('content', '') + note
        else:
            routed.insert(0, {'role': 'system', 'content': note.strip()})
        return self.base.invoke(routed, timeout)


class _MemoryModel:
    """Inject one already-bound Life Notebook memory snapshot into model context."""

    def __init__(self, base, current_memory):
        self.base = base
        self.name = base.name
        self.current_memory = current_memory

    def invoke(self, messages, timeout):
        enriched = json.loads(json.dumps(messages))
        note = (
            "\nHumanOS current derived Life Notebook state (host-derived data, not permission or "
            "independent factual verification). Use it only when relevant. Provenance identifies "
            "the Notebook evidence behind each active item. Never resolve CONFLICTED items by guessing:\n"
            + json.dumps(self.current_memory, ensure_ascii=False, sort_keys=True)
        )
        if enriched and enriched[0].get('role') == 'system':
            enriched[0]['content'] = enriched[0].get('content', '') + note
        else:
            enriched.insert(0, {'role': 'system', 'content': note.strip()})
        return self.base.invoke(enriched, timeout)


class _ContextAwareAgent:
    """Gate normal Mirror turns and maintain derived Life Notebook memory."""

    MEMORY_BIND_KIND = 'MEMORY_CONTEXT_BOUND'

    def __init__(self, agent, router, runtime):
        self._agent = agent
        self._router = router
        self._runtime = runtime

    @property
    def authorize(self):
        return self._agent.authorize

    @authorize.setter
    def authorize(self, value):
        self._agent.authorize = value

    def _existing_memory_binding(self, tx):
        row = self._agent.book.db.execute(
            "SELECT payload FROM events WHERE tx=? AND kind=? ORDER BY seq LIMIT 1",
            (tx, self.MEMORY_BIND_KIND),
        ).fetchone()
        return json.loads(row['payload']) if row else None

    def _memory_snapshot(self, tx, *, create_if_missing):
        """Return the exact memory snapshot bound before first model execution.

        New tasks bind only immutable semantic event IDs in the content-light audit
        ledger. Resumes reconstruct from those same IDs, so later preference changes
        cannot alter an interrupted task's context. Legacy tasks with no binding simply
        resume without semantic memory rather than inheriting new state retroactively.
        """
        book = self._agent.book
        row = book.get_transaction(tx)
        if row is None:
            return None
        identity = book.get_identity(row['hcid'])
        binding = self._existing_memory_binding(tx)
        if binding is None and not create_if_missing:
            return None
        if binding is None:
            try:
                binding = memory_binding(book, identity['owner'])
                snapshot = memory_context_from_binding(book, identity['owner'], binding)
            except Exception as error:
                binding = {
                    'schema_version': 1,
                    'status': 'UNAVAILABLE',
                    'event_ids': [],
                    'error_type': type(error).__name__,
                }
                snapshot = memory_context_from_binding(book, identity['owner'], binding)
            # This content-light binding is durable before Agent.run can invoke a model.
            book.event(tx, self.MEMORY_BIND_KIND, binding)
            return snapshot
        # A persisted binding is execution evidence. If it can no longer be
        # reconstructed, do not silently substitute latest memory or an empty packet.
        return memory_context_from_binding(book, identity['owner'], binding)

    def _capture_memory(self, tx):
        """Best-effort semantic promotion after the exact transcript is durable."""
        book = self._agent.book
        try:
            result = capture_memory_from_turn(book, tx)
        except Exception as error:
            result = {'status': 'MEMORY_EXTRACTION_FAILED', 'error_type': type(error).__name__, 'tx': tx}
        receipt = {
            key: result[key]
            for key in ('status', 'event_id', 'supersedes', 'error_type', 'tx')
            if key in result
        }
        state = book.task(tx)
        if state is not None:
            state = dict(state)
            state['memory_capture'] = receipt
            book.save_task(tx, state)
        return result

    def _run_base(self, tx, hcid=None, user_input=None, context=(), reference_binding=None,
                  work_binding=None, route_context=None, new_task=True):
        """Run the existing Agent with a crash-safe bound semantic-memory snapshot."""
        original_model = self._agent.model
        model = original_model
        if route_context is not None:
            model = _RoutedModel(model, route_context)
        current_memory = self._memory_snapshot(tx, create_if_missing=new_task)
        if current_memory is not None:
            model = _MemoryModel(model, current_memory)
        self._agent.model = model
        try:
            result = self._agent.run(
                tx, hcid, user_input, context,
                reference_binding=reference_binding, work_binding=work_binding)
        finally:
            self._agent.model = original_model
        state = self._agent.book.task(tx)
        if state and state.get('phase') == 'COMPLETE':
            self._capture_memory(tx)
        return result

    def _host_final(self, tx, hcid, text, response):
        book = self._agent.book
        if book.get_transaction(tx) is None:
            book.start(hcid, tx, text)
        state = book.task(tx)
        if state and state.get('phase') == 'COMPLETE':
            book.checkpoint(tx)
            self._capture_memory(tx)
            return state['final']
        if state:
            raise RuntimeError('Context routing found unfinished task state; explicit reconciliation required')
        row = book.get_transaction(tx)
        state = {
            'phase': 'FINAL', 'steps': 0, 'elapsed': 0, 'model': self._agent.model.name,
            'messages': [], 'context': {'host_direct': 'CONTEXT_ROUTER'},
            'workspace': str(self._agent.tools.workspace),
            'permissions': task_scope(row, self._agent.tools.workspace),
            'reference_binding': None, 'approvals': [], 'final': response,
            'final_ordinal': book.message_count(tx),
        }
        book.save_task(tx, state)
        book.append(tx, state['final_ordinal'], 'ASSISTANT', response)
        state['phase'] = 'COMPLETE'
        state['delivery'] = 'PREPARED_NOT_CONFIRMED'
        book.save_task(tx, state)
        book.event(tx, 'HOST_FINAL_CAPTURED', {
            'kind': 'CONTEXT_ROUTER', 'final_digest': book.content_digest(response)})
        book.checkpoint(tx)
        self._capture_memory(tx)
        record_completed_transaction(book, tx, hcid, text, response)
        return response

    def run(self, tx, hcid=None, user_input=None, context=(), reference_binding=None, work_binding=None):
        book = self._agent.book
        # A resumed task keeps its original semantic-memory binding. No rerouting or
        # latest-memory substitution is allowed beneath previously saved execution.
        if book.task(tx) is not None:
            return self._run_base(
                tx, hcid, user_input, context,
                reference_binding=reference_binding, work_binding=work_binding,
                new_task=False)

        if user_input is not None and book.get_transaction(tx) is None:
            book.start(hcid, tx, user_input)
        row = book.get_transaction(tx)
        if row is None:
            return self._run_base(tx, hcid, user_input, context,
                                  reference_binding=reference_binding, work_binding=work_binding)

        host_request = host_runtime_request(row['input'])
        if host_request is not None:
            book.event(tx, 'HOST_INTENT', {'tool': host_request['name']})
            return self._run_base(
                tx, hcid, None, context,
                reference_binding=reference_binding, work_binding=work_binding)

        if _ordinary_question(row['input']):
            return self._run_base(tx, hcid, None, context,
                                  reference_binding=reference_binding, work_binding=work_binding)

        pending = self._router.resolve_pending_ambiguity(
            book, row['hcid'], row['input'], current_tx=tx)

        if pending is not None:
            route = pending
        else:
            allow_inherit = reference_binding is None and work_binding is None
            timezone_name = os.environ.get('HUMANOS_TIMEZONE', 'UTC')
            historical = self._router.inspect_history(
                book, row['input'], current_tx=tx, timezone_name=timezone_name)
            if historical.origin == 'NOTEBOOK_RECOVERY':
                route = historical
            else:
                route = self._router.inspect_session(
                    book, row['hcid'], row['input'], current_tx=tx, allow_inherit=allow_inherit)
        if not route.applicable:
            return self._run_base(tx, hcid, None, context,
                                  reference_binding=reference_binding, work_binding=work_binding)

        safe_route = route.model_context()
        book.event(tx, 'CONTEXT_ROUTE', safe_route)
        if route.origin == 'SESSION_CONTINUITY' and route.source_tx:
            book.event(tx, 'CONTEXT_SESSION_CONTINUED', {
                'source_tx': route.source_tx,
                'workspace_id': route.workspace_id,
                'workstream_id': route.selected_workstream,
            })
        if route.origin == 'NOTEBOOK_RECOVERY' and route.source_tx:
            book.event(tx, 'CONTEXT_NOTEBOOK_RECOVERED', {
                'source_tx': route.source_tx,
                'workspace_id': route.workspace_id,
                'workstream_id': route.selected_workstream,
            })
        if route.origin == 'AMBIGUITY_SELECTION' and route.source_tx and not route.requires_confirmation:
            book.event(tx, 'CONTEXT_AMBIGUITY_RESOLVED', {
                'source_tx': route.source_tx,
                'workspace_id': route.workspace_id,
                'workstream_id': route.selected_workstream,
            })

        notice = self._router.format_for_human(route)
        if route.requires_confirmation:
            candidate_ids = [
                item['workstream_id'] for item in route.candidates
                if isinstance(item.get('workstream_id'), str)
            ]
            if candidate_ids:
                book.event(tx, 'CONTEXT_AMBIGUITY_PENDING', {'candidate_ids': candidate_ids})
            return self._host_final(tx, row['hcid'], row['input'], notice)

        if notice:
            print(notice, file=sys.stderr)

        return self._run_base(
            tx, hcid, None, context,
            reference_binding=reference_binding, work_binding=work_binding,
            route_context=safe_route)


class HumanOSRuntime(_BaseHumanOSRuntime):
    """Default Mirror runtime plus routing and bounded derived Life Notebook memory."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context_router = RuntimeContextRouter(repo_root=BASE)
        self.agent = _ContextAwareAgent(self.agent, self.context_router, self)


def main():
    _core.HumanOSRuntime = HumanOSRuntime
    return _core.main()


if __name__ == '__main__':
    raise SystemExit(main())
