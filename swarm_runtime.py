"""HumanOS Swarm Runtime v3: multi-model orchestration over trusted broker."""
import argparse
import json
import os
from pathlib import Path
from engine import OllamaModel
from swarm import ControlPlane, PROFILE, encode
from swarm_models import ModelRouter

ROLES = frozenset({'coordinator', 'worker', 'verifier'})
SYSTEM = '''You are one role inside HumanOS AUTHORIZED_RED_TEAM_SWARM.
You are not the authority boundary. You may only propose broker actions that your
registered capability manifest permits. Never claim an action succeeded without a
broker observation. Never expand targets, privileges, impact, peers, time window, or
budgets. Return exactly one JSON object: {"action":{"tool":...,"arguments":...}}
or {"final":"..."}. Do not include hidden reasoning.'''


def validate_runtime_config(config):
    if not isinstance(config, dict) or set(config) != {'broker', 'control_state', 'orchestration'}: raise ValueError('Runtime config requires broker, control_state, orchestration')
    broker = config['broker']
    if not isinstance(broker, dict) or broker.get('profile') != PROFILE: raise ValueError('Runtime v3 requires AUTHORIZED_RED_TEAM_SWARM broker config')
    if not Path(config['control_state']).is_absolute(): raise ValueError('control_state must be absolute')
    orchestration = config['orchestration']
    if not isinstance(orchestration, dict) or set(orchestration) != {'roles', 'max_rounds', 'model_timeout'}: raise ValueError('orchestration requires roles, max_rounds, model_timeout')
    if type(orchestration['max_rounds']) is not int or not 1 <= orchestration['max_rounds'] <= 50: raise ValueError('max_rounds must be 1..50')
    if type(orchestration['model_timeout']) not in (int, float) or not 1 <= orchestration['model_timeout'] <= 120: raise ValueError('model_timeout must be 1..120 seconds')
    manifests = {m['agent_id']: m for m in broker.get('agents', [])}; roles = orchestration['roles']
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
    raise ValueError('Model must emit exactly one final or broker action')


class SwarmRuntime:
    def __init__(self, config, model_factory=None, model_router=None):
        self.config = json.loads(encode(validate_runtime_config(config))); self.broker = self.config['broker']; self.state_dir = Path(self.config['control_state']); self.plane = ControlPlane(self.broker, self.state_dir)
        router = model_router or ModelRouter(os.environ.get('HUMANOS_ENDPOINT', 'http://127.0.0.1:11434'))
        self.models = {m['agent_id']: (model_factory(m) if model_factory else router.build(m)) for m in self.broker['agents']}
        self.tokens = {m['agent_id']: m['token'] for m in self.broker['agents']}; self.manifests = {m['agent_id']: {k: v for k, v in m.items() if k != 'token'} for m in self.broker['agents']}
        self.roles = self.config['orchestration']['roles']; self.timeout = self.config['orchestration']['model_timeout']; self.max_rounds = self.config['orchestration']['max_rounds']; self.transcript = {a: [] for a in self.models}; self.finals = {}

    def _messages(self, agent_id, round_no):
        safe_envelope = {k: v for k, v in self.broker['envelope'].items() if k != 'authorization'}
        briefing = {'role': self.roles[agent_id], 'agent': self.manifests[agent_id], 'authorization': 'verified by trusted host; details withheld from model context', 'envelope': safe_envelope, 'round': round_no, 'rules': 'Use only declared broker capabilities and peers. Broker observations are authoritative.'}
        return [{'role': 'system', 'content': SYSTEM}, {'role': 'user', 'content': encode(briefing)}] + self.transcript[agent_id][-12:]

    def _record(self, agent_id, proposal, result=None):
        self.transcript[agent_id].append({'role': 'assistant', 'content': encode(proposal)})
        if result is not None: self.transcript[agent_id].append({'role': 'user', 'content': encode({'broker_observation': result})})

    def _invoke(self, agent_id, messages):
        model = self.models[agent_id]
        return model.structured(messages, self.timeout) if isinstance(model, OllamaModel) else model.invoke(messages, self.timeout)

    def _step(self, agent_id, round_no):
        if agent_id in self.finals: return
        proposal = validate_proposal(self._invoke(agent_id, self._messages(agent_id, round_no)))
        if 'final' in proposal: self.finals[agent_id] = proposal['final']; self._record(agent_id, proposal); return
        result = self.plane.execute(self.tokens[agent_id], proposal['action']); self._record(agent_id, proposal, result)
        if not result.get('ok') and 'ESCALATION_REQUIRED' in result.get('error', ''): raise PermissionError(result['error'])

    def run(self):
        order = sorted(self.models, key=lambda a: ({'coordinator': 0, 'worker': 1, 'verifier': 2}[self.roles[a]], a)); round_no = 0
        try:
            for round_no in range(1, self.max_rounds + 1):
                for agent_id in order: self._step(agent_id, round_no)
                if all(a in self.finals for a in self.models): break
            return {'status': 'COMPLETE' if all(a in self.finals for a in self.models) else 'ROUND_LIMIT', 'finals': dict(self.finals), 'rounds': round_no, 'ledger_records': len(self.plane.ledger.verify()), 'models': {a: self.manifests[a].get('model') for a in self.models}}
        finally: self.plane.close()


def main():
    parser = argparse.ArgumentParser(description='HumanOS Swarm Runtime v3'); parser.add_argument('--config', required=True); args = parser.parse_args(); result = SwarmRuntime(json.loads(Path(args.config).resolve().read_text())).run(); print(json.dumps(result, ensure_ascii=False, sort_keys=True)); return 0


if __name__ == '__main__': raise SystemExit(main())
