"""HumanOS Runtime 0.1 with deterministic development-context routing."""
from __future__ import annotations

import json
import os
import sys

from server_core import *  # Preserve the original server module's public API.
import server_core as _core
from context_runtime import RuntimeContextRouter
from permissions import task_scope
from runtime_info import host_runtime_request
from intent_classifier import classify
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
                                                     'how do ', 'why is ', 'why are ',
                                                     'explain ', 'teach me ', 'tell me '))


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


class _ContextAwareAgent:
    """Gate normal Mirror turns before model/tool execution."""

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

    def _host_final(self, tx, hcid, text, response):
        book = self._agent.book
        if book.get_transaction(tx) is None:
            book.start(hcid, tx, text)
        state = book.task(tx)
        if state and state.get('phase') == 'COMPLETE':
            book.checkpoint(tx)
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
        record_completed_transaction(book, tx, hcid, text, response)
        return response

    def run(self, tx, hcid=None, user_input=None, context=(), reference_binding=None, work_binding=None):
        book = self._agent.book
        # A resumed task already has a durable execution context. Do not reroute it
        # under potentially changed registry metadata.
        if book.task(tx) is not None:
            return self._agent.run(tx, hcid, user_input, context,
                                   reference_binding=reference_binding, work_binding=work_binding)

        if user_input is not None and book.get_transaction(tx) is None:
            book.start(hcid, tx, user_input)
        row = book.get_transaction(tx)
        if row is None:
            return self._agent.run(tx, hcid, user_input, context,
                                   reference_binding=reference_binding, work_binding=work_binding)

        host_request = host_runtime_request(row['input'])
        if host_request is not None:
            # Host/runtime facts outrank development-workstream routing. The
            # base Agent resolves this exact human-derived request deterministically.
            book.event(tx, 'HOST_INTENT', {'tool': host_request['name']})
            return self._agent.run(
                tx, hcid, None, context,
                reference_binding=reference_binding, work_binding=work_binding)

        if row['input'].strip().lower().startswith(('what is ', 'what are ', 'how does ', 'how do ', 'why is ', 'why are ', 'explain ', 'teach me ')):
            intent = classify(self._agent.model, row['input'])
            if intent["intent"] in ("education", "casual") and intent["confidence"] >= 0.75:
                return self._agent.run(tx, hcid, None, context,
                                       reference_binding=reference_binding, work_binding=work_binding)

        pending = self._router.resolve_pending_ambiguity(
            book, row['hcid'], row['input'], current_tx=tx)

        if pending is not None:
            route = pending
        else:
            # File/plan reference bindings and delegated-work bindings are more
            # specific authorities than generic conversational continuity. They may
            # still receive an explicit fresh route, but cannot cause a short phrase
            # such as "do it" to inherit an unrelated prior workstream implicitly.
            allow_inherit = reference_binding is None and work_binding is None
            # Mirror accepts timezone only from an explicit owner/runtime setting.
            # It never derives timezone from IP, device location, model output, or request text.
            timezone_name = os.environ.get('HUMANOS_TIMEZONE', 'UTC')
            historical = self._router.inspect_history(
                book, row['input'], current_tx=tx, timezone_name=timezone_name)
            if historical.origin == 'NOTEBOOK_RECOVERY':
                route = historical
            else:
                route = self._router.inspect_session(
                    book, row['hcid'], row['input'], current_tx=tx, allow_inherit=allow_inherit)
        if not route.applicable:
            return self._agent.run(tx, hcid, None, context,
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
                book.event(tx, 'CONTEXT_AMBIGUITY_PENDING', {
                    'candidate_ids': candidate_ids,
                })
            # This notice is the durable final response. Do not also print it to
            # stderr, which previously duplicated ambiguity prompts in the terminal.
            return self._host_final(tx, row['hcid'], row['input'], notice)

        if notice:
            print(notice, file=sys.stderr)

        original_model = self._agent.model
        self._agent.model = _RoutedModel(original_model, safe_route)
        try:
            return self._agent.run(tx, hcid, None, context,
                                   reference_binding=reference_binding, work_binding=work_binding)
        finally:
            self._agent.model = original_model


class HumanOSRuntime(_BaseHumanOSRuntime):
    """Default Mirror runtime plus the promoted development Context Registry gate."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.context_router = RuntimeContextRouter(repo_root=BASE)
        self.agent = _ContextAwareAgent(self.agent, self.context_router, self)


def main():
    # server_core.main resolves HumanOSRuntime from its module globals. Patch only
    # that constructor; all existing CLI/recovery behavior stays in the preserved
    # runtime implementation copied at this commit.
    _core.HumanOSRuntime = HumanOSRuntime
    return _core.main()


if __name__ == '__main__':
    raise SystemExit(main())
