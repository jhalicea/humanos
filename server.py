"""HumanOS Runtime 0.1 with deterministic development-context routing."""
from __future__ import annotations

import json
import sys

from server_core import *  # Preserve the original server module's public API.
import server_core as _core
from context_runtime import RuntimeContextRouter
from permissions import task_scope

BASE = _core.BASE
PASTE_COMMAND = _core.PASTE_COMMAND
PASTE_SEND_COMMAND = _core.PASTE_SEND_COMMAND
PASTE_GRACE_SECONDS = _core.PASTE_GRACE_SECONDS
read_human_input = _core.read_human_input

_BaseHumanOSRuntime = _core.HumanOSRuntime


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

        route = self._router.inspect(row['input'])
        if not route.applicable:
            return self._agent.run(tx, hcid, None, context,
                                   reference_binding=reference_binding, work_binding=work_binding)

        safe_route = route.model_context()
        book.event(tx, 'CONTEXT_ROUTE', safe_route)
        notice = self._router.format_for_human(route)
        if notice:
            print(notice, file=sys.stderr)
        if route.requires_confirmation:
            return self._host_final(tx, row['hcid'], row['input'], notice)

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
