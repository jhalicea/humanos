"""HumanOS Swarm Runtime v3: multi-model orchestration over trusted broker."""
import argparse
import json
import os
from pathlib import Path
from engine import OllamaModel
from subagent_view import SubagentStatusStore, TerminalSubagentView
from swarm import ControlPlane, PROFILE, encode
from swarm_models import ModelRouter

ROLES = frozenset({'coordinator', 'worker', 'verifier'})
SYSTEM = '''You are one role inside HumanOS AUTHORIZED_RED_TEAM_SWARM.
You are not the authority boundary. You may only propose broker actions explicitly
listed in allowed_actions. Never invent a tool name or argument. Never claim an
action succeeded without a broker observation. Never expand targets, privileges,
impact, peers, time window, or budgets. Return exactly one JSON object containing
either an action that exactly matches one allowed_actions schema or a non-empty
{"final":"..."}. Do not include hidden reasoning.'''


def tool_contract(manifest):
    peers = list(manifest.get('peers', []))
    schemas = []
    for tool in manifest.get('capabilities', []):
        if tool == 'send_message':
            schemas.append({'tool': 'send_message', 'arguments': {'peer': '<one of: ' + ', '.join(peers) + '>', 'message': '<text>'}})
        elif tool == 'receive_messages':
            schemas.append({'tool': 'receive_messages', 'arguments': {}})
        elif tool == 'tcp_probe':
            schemas.append({'tool': 'tcp_probe', 'arguments': {'ip': '<authorized numeric IP>', 'port': '<authorized integer port>'}})
    return schemas


def validate_runtime_config(config):
    if not isinstance(config, dict) or set(config) != {'broker', 'control_state', 'orchestration'}: raise ValueError('Runtime config requires broker, control_state, orchestration')
    broker = config['broker']
    if not isinstance(broker, dict) or broker.get('profile') != PROFILE: raise ValueError('Runtime v3 requires AUTHORIZED_RED_TEAM_SWARM broker config')
    if not Path(config['control_state']).is_absolute(): raise ValueError('control_state must be absolute')
    orchestration = config['orchestration']
    if not isinstance(orchestration, dict) or not {'roles', 'max_rounds', 'model_timeout'} <= set(orchestration) or set(orchestration) - {'roles', 'model_roles', 'max_rounds', 'model_timeout'}: raise ValueError('orchestration requires roles, max_rounds, model_timeout and optional model_roles')
    if type(orchestration['max_rounds']) is not int or not 1 <= orchestration['max_rounds'] <= 50: raise ValueError('max_rounds must be 1..50')
    if type(orchestration['model_timeout']) not in (int, float) or not 1 <= orchestration['model_timeout'] <= 120: raise ValueError('model_timeout must be 1..120 seconds')
    manifests = {m['agent_id']: m for m in broker.get('agents', [])}; roles = orchestration['roles']; model_roles = orchestration.get('model_roles', {agent_id: manifest.get('model') for agent_id, manifest in manifests.items()})
    if not isinstance(model_roles, dict): raise ValueError('model_roles must assign one model to every agent')
    if set(model_roles) != set(manifests) or any(not isinstance(name, str) or not name for name in model_roles.values()): raise ValueError('model_roles must assign one model to every agent')
    if any(manifests[agent_id].get('model') != model for agent_id, model in model_roles.items()): raise ValueError('model_roles must match broker model manifests')
    if not isinstance(roles, dict) or set(roles) != set(manifests): raise ValueError('Every broker agent requires exactly one orchestration role')
    counts = {role: 0 for role in ROLES}
    for agent_id, role in roles.items():
        if role not in ROLES: raise ValueError('Unknown swarm role for ' + agent_id)
        counts[role] += 1
    if counts['coordinator'] != 1 or counts['worker'] < 1 or counts['verifier'] < 1: raise ValueError('Swarm requires exactly one coordinator, at least one worker, and one verifier')
    return config


def validate_proposal(value):
    if not isinstance(value, dict): raise ValueError('Model proposal must be an object')
    if set(value) == {'final'} and isinstance(value['final'], str) and value['final'].strip(): return value
    if set(value) == {'action'} and isinstance(value['action'], dict) and set(value['action']) == {'tool', 'arguments'}: return value
    if set(value) == {'action', 'final'} and isinstance(value['final'], str) and isinstance(value['action'], dict) and set(value['action']) == {'tool', 'arguments'}: return {'action': value['action']}
    raise ValueError('Model must emit exactly one final or broker action. Rejected JSON: ' + encode(value)[:8000])


class SwarmRuntime:
    def __init__(self, config, model_factory=None, model_router=None, status_callback=None):
        self.config = json.loads(encode(validate_runtime_config(config))); self.broker = self.config['broker']; self.state_dir = Path(self.config['control_state']); self.plane = ControlPlane(self.broker, self.state_dir)
        router = model_router or ModelRouter(os.environ.get('HUMANOS_ENDPOINT', 'http://127.0.0.1:11434'))
        self.models = {m['agent_id']: (model_factory(m) if model_factory else router.build(m)) for m in self.broker['agents']}
        self.tokens = {m['agent_id']: m['token'] for m in self.broker['agents']}; self.manifests = {m['agent_id']: {k: v for k, v in m.items() if k != 'token'} for m in self.broker['agents']}
        self.roles = self.config['orchestration']['roles']; self.timeout = self.config['orchestration']['model_timeout']; self.max_rounds = self.config['orchestration']['max_rounds']; self.transcript = {a: [] for a in self.models}; self.finals = {}
        self.status_error = None
        try:
            self.status = SubagentStatusStore(
                self.state_dir,
                self.broker['envelope'].get('run_id', 'UNKNOWN'),
                self.broker['agents'],
                self.roles,
                self.max_rounds,
                on_change=status_callback,
            )
        except Exception as exc:
            # Observability must not become an authority or availability boundary.
            self.status = None
            self.status_error = type(exc).__name__ + ': ' + str(exc)

    def _status(self, method, *args):
        if self.status is None:
            return
        try:
            getattr(self.status, method)(*args)
        except Exception as exc:
            self.status_error = type(exc).__name__ + ': ' + str(exc)

    def _messages(self, agent_id, round_no):
        manifest = self.manifests[agent_id]
        safe_envelope = {k: v for k, v in self.broker['envelope'].items() if k != 'authorization'}
        briefing = {'role': self.roles[agent_id], 'task': manifest['task'], 'agent': manifest,
                    'allowed_actions': tool_contract(manifest),
                    'authorization': 'verified by trusted host; details withheld from model context',
                    'envelope': safe_envelope, 'round': round_no,
                    'rules': 'Use only exact allowed_actions schemas. If no action is needed, return final. Broker observations are authoritative.'}
        return [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': encode(briefing)}] + self.transcript[agent_id][-12:]

    def _record(self, agent_id, proposal, result=None):
        self.transcript[agent_id].append({'role': 'assistant', 'content': encode(proposal)})
        if result is not None: self.transcript[agent_id].append({'role': 'user', 'content': encode({'broker_observation': result})})

    def _invoke(self, agent_id, messages):
        model = self.models[agent_id]
        return model.structured(messages, self.timeout) if isinstance(model, OllamaModel) else model.invoke(messages, self.timeout)

    def _step(self, agent_id, round_no):
        if agent_id in self.finals: return
        self._status('mark', agent_id, 'working', round_no, 'invoking model')
        try:
            messages = self._messages(agent_id, round_no)
            for attempt in range(2):
                try:
                    proposal = validate_proposal(self._invoke(agent_id, messages))
                    break
                except ValueError as exc:
                    if attempt:
                        raise
                    messages = messages + [{'role': 'user', 'content': encode({'error': str(exc), 'required': 'Return exactly {"action":{"tool":"...","arguments":{...}}} using one allowed_actions schema. Return {"final":"non-empty text"} only after your task is complete.'})}]
            if 'final' in proposal:
                self.finals[agent_id] = proposal['final']; self._record(agent_id, proposal)
                self._status('mark', agent_id, 'done', round_no, 'finished')
                return
            result = self.plane.execute(self.tokens[agent_id], proposal['action']); self._record(agent_id, proposal, result)
            if not result.get('ok') and 'ESCALATION_REQUIRED' in result.get('error', ''): raise PermissionError(result['error'])
            self._status('mark', agent_id, 'working', round_no, 'broker action observed')
        except Exception as exc:
            self._status('mark', agent_id, 'error', round_no, 'error: ' + type(exc).__name__)
            raise

    def run(self):
        order = sorted(self.models, key=lambda a: ({'coordinator': 0, 'worker': 1, 'verifier': 2}[self.roles[a]], a)); round_no = 0
        self._status('set_overall', 'RUNNING', 0)
        try:
            for round_no in range(1, self.max_rounds + 1):
                for agent_id in order: self._step(agent_id, round_no)
                if all(a in self.finals for a in self.models): break
            status = 'COMPLETE' if all(a in self.finals for a in self.models) else 'ROUND_LIMIT'
            if status == 'ROUND_LIMIT':
                self._status('stop_incomplete', round_no, 'round limit')
            self._status('set_overall', status, round_no)
            result = {'status': status, 'finals': dict(self.finals), 'rounds': round_no, 'ledger_records': len(self.plane.ledger.verify()), 'models': {a: self.manifests[a].get('model') for a in self.models}}
            if self.status is not None:
                result['subagent_state'] = str(self.status.path)
            if self.status_error is not None:
                result['subagent_status_error'] = self.status_error
            return result
        except Exception:
            self._status('set_overall', 'ERROR', round_no)
            raise
        finally: self.plane.close()


def main():
    parser = argparse.ArgumentParser(description='HumanOS Swarm Runtime v3')
    parser.add_argument('--config', required=True)
    parser.add_argument('--view', action='store_true', help='Render the subagent panel live in this terminal')
    args = parser.parse_args()
    view = TerminalSubagentView() if args.view else None
    result = SwarmRuntime(json.loads(Path(args.config).resolve().read_text()), status_callback=view).run()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__': raise SystemExit(main())
