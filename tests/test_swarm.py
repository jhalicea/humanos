import copy
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from swarm import ControlPlane, PROFILE, STOPS, serve


def configuration():
    return {'profile': PROFILE, 'envelope': {
        'run_id': 'isolated-test', 'targets': [{'ip': '127.0.0.1', 'port': 12345}],
        'authorization': {'human': 'test owner', 'reference': 'fixture-consent',
                          'provenance_sha256': hashlib.sha256(b'fixture').hexdigest(),
                          'owner_attested': True, 'environment': 'authorized_lab'},
        'not_before': int(time.time()) - 5, 'expires': int(time.time()) + 60,
        'permitted_impact': 'connect_only', 'stop_conditions': sorted(STOPS),
        'max_actions': 20, 'max_message_bytes': 100},
        'agents': [{'agent_id': name, 'model': 'fixture', 'version': '1', 'task': 'test',
                    'capabilities': ['tcp_probe', 'send_message', 'receive_messages'],
                    'peers': ['b'] if name == 'a' else [], 'token': name * 32}
                   for name in ('a', 'b')]}


class SwarmTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve() / 'control'
        self.config = configuration()
        self.plane = None

    def tearDown(self):
        if self.plane:
            self.plane.close()
        self.temp.cleanup()

    def start(self):
        self.plane = ControlPlane(self.config, self.root)
        return self.plane

    def call(self, tool='tcp_probe', args=None, token='a' * 32):
        return self.plane.execute(token, {'tool': tool, 'arguments': args if args is not None else {'ip': '127.0.0.1', 'port': 12345}})

    def test_immutable_input_and_returned_scope(self):
        self.start()
        self.config['envelope']['targets'].clear()
        self.plane.envelope['targets'].clear()
        self.assertEqual(len(self.plane.envelope['targets']), 1)
        self.plane.close(); self.plane = None
        with self.assertRaises(ValueError):
            self.start()
        self.config = configuration(); self.config['envelope']['max_actions'] = 21
        with self.assertRaisesRegex(PermissionError, 'Immutable'):
            self.start()

    def test_capability_denies_before_socket(self):
        self.config['agents'][0]['capabilities'] = []
        self.start()
        with patch('swarm.socket.socket') as net:
            self.assertFalse(self.call()['ok']); net.assert_not_called()

    def test_unknown_identity_and_impersonation(self):
        self.start()
        self.assertFalse(self.call(token='wrong')['ok'])
        self.assertFalse(self.plane.execute('a'*32, {'tool':'tcp_probe', 'arguments':{}, 'agent_id':'b'})['ok'])
        events = [r['event'] for r in self.plane.ledger.verify()]
        self.assertEqual(events[-1]['identity']['agent_id'], 'a')

    def test_undeclared_peer_and_broker_delivery(self):
        self.start()
        self.assertFalse(self.call('send_message', {'peer':'a','message':'x'}, 'b'*32)['ok'])
        self.assertTrue(self.call('send_message', {'peer':'b','message':'hello'})['ok'])
        result = self.call('receive_messages', {}, 'b'*32)
        self.assertEqual(result['observation']['messages'], [{'sender':'a','message':'hello'}])
        self.assertEqual(self.call('receive_messages', {}, 'b'*32)['observation']['messages'], [])

    def test_unauthorized_egress_stops_run(self):
        self.start()
        with patch('swarm.socket.socket') as net:
            for ip in ('192.0.2.1', 'localhost', '127.0.0.1.evil', '::1'):
                self.assertFalse(self.call(args={'ip':ip,'port':12345})['ok'])
            self.assertFalse(self.call()['ok']); net.assert_not_called()
        self.assertTrue(any(r['event'].get('reason') == 'scope_escape' for r in self.plane.ledger.verify()))

    def test_live_loopback_and_attribution(self):
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0)); listener.listen()
            target = {'ip':'127.0.0.1','port':listener.getsockname()[1]}
            self.config['envelope']['targets'] = [target]
            self.start()
            self.assertTrue(self.call(args=target)['observation']['connected'])
        event = self.plane.ledger.verify()[-1]['event']
        self.assertEqual(event['identity'], {k:v for k,v in self.config['agents'][0].items() if k != 'token'})
        self.assertEqual(event['authorization'], self.config['envelope']['authorization'])
        self.assertTrue(event['result']['observation']['connected'])
        self.assertNotIn('a'*32, (self.root/'actions.jsonl').read_text())

    def test_every_escalation_is_persistent(self):
        for reason in STOPS:
            with self.subTest(reason=reason):
                root = self.root / reason
                plane = ControlPlane(self.config, root)
                result = plane.execute('a'*32, {'tool':'escalate','arguments':{'reason':reason}})
                self.assertIn('ESCALATION_REQUIRED', result['error']); plane.close()
                plane = ControlPlane(self.config, root)
                self.assertFalse(plane.execute('a'*32, {'tool':'receive_messages','arguments':{}})['ok'])
                plane.close()

    def test_kill_switch(self):
        self.start(); self.plane.stop()
        self.assertFalse(self.call()['ok'])

    def test_external_kill_file(self):
        self.start(); (self.root/'STOP').touch()
        with patch('swarm.socket.socket') as net:
            self.assertFalse(self.call()['ok']); net.assert_not_called()

    def test_time_and_action_budgets(self):
        self.config['envelope']['max_actions'] = 1
        self.start()
        self.assertTrue(self.call('receive_messages', {})['ok'])
        self.plane.close(); self.plane = None; self.start()
        self.assertFalse(self.call('receive_messages', {})['ok'])
        with patch('swarm.time.time', return_value=self.config['envelope']['expires']):
            self.assertFalse(self.call()['ok'])

    def test_byte_budget_survives_restart(self):
        self.config['envelope']['max_message_bytes'] = 5
        self.start()
        self.assertTrue(self.call('send_message', {'peer':'b','message':'hello'})['ok'])
        self.plane.close(); self.plane = None; self.start()
        self.assertFalse(self.call('send_message', {'peer':'b','message':'!'})['ok'])

    def test_audit_edit_and_truncation(self):
        self.start(); self.call('receive_messages', {})
        path = self.root/'actions.jsonl'; original = path.read_bytes()
        for value in (b'', b'\n'.join(original.splitlines()[:-1])+b'\n', original.replace(b'fixture-consent', b'tampered-value')):
            path.write_bytes(value)
            with self.assertRaises((ValueError, PermissionError)):
                self.call()
            path.write_bytes(original)

    def test_audit_failure_prevents_effect(self):
        self.start()
        with patch.object(self.plane.ledger, 'append', side_effect=OSError('disk full')), patch('swarm.socket.socket') as net:
            with self.assertRaises(OSError): self.call()
            net.assert_not_called()

    def test_uncertain_action_is_not_replayed(self):
        self.start()
        self.plane.ledger.append({'kind':'ATTEMPT','action_id':'interrupted'})
        self.plane.close(); self.plane = None; self.start()
        self.assertFalse(self.call()['ok'])

    def test_exclusive_process_lock(self):
        self.start()
        with self.assertRaises(BlockingIOError): ControlPlane(self.config, self.root)

    def test_invalid_scope_and_manifests(self):
        for change in (lambda c: c['envelope']['authorization'].update(owner_attested=False),
                       lambda c: c['envelope'].update(permitted_impact='destructive'),
                       lambda c: c['envelope']['targets'][0].update(ip='localhost'),
                       lambda c: c['agents'][0].update(capabilities=['shell']),
                       lambda c: c['envelope'].update(stop_conditions=[])):
            c = copy.deepcopy(self.config); change(c)
            with self.assertRaises(ValueError): ControlPlane(c, self.root)

    def test_no_control_file_access_or_arbitrary_tools(self):
        self.start()
        for tool in ('read_file','create_file','shell','http','direct_message','grant','reset_budget'):
            self.assertFalse(self.call(tool, {'path':str(self.root)})['ok'])

    def test_profile_subprocess_preserves_notebook_boundary(self):
        config = dict(self.config, control_state=str(self.root))
        path = Path(self.temp.name)/'config.json'; path.write_text(json.dumps(config))
        frame = {'token':'a'*32, 'request':{'tool':'receive_messages','arguments':{}}}
        result = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1]/'server.py'), '--config', str(path)], input=json.dumps(frame)+'\n', text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), {'ok':True,'observation':{'messages':[]}})
        self.assertEqual(set(p.name for p in Path(self.temp.name).iterdir()), {'config.json','control'})

    def test_malformed_frame_stops(self):
        with self.assertRaises(ValueError): serve(self.config, self.root, io.StringIO('{}\n'), io.StringIO())
        self.start(); self.assertFalse(self.call()['ok'])

    def test_high_impact_and_privilege_escalation_before_effect(self):
        for key, reason in [('irreversible', 'high_impact'), ('privilege', 'unexpected_privilege')]:
            plane = ControlPlane(self.config, self.root / key)
            with patch('swarm.socket.socket') as net:
                result = plane.execute('a'*32, {'tool':'tcp_probe', 'arguments':{'ip':'127.0.0.1','port':12345,key:True}})
                self.assertIn(reason, result['error']); net.assert_not_called()
            plane.close()

    def test_future_time_denied(self):
        self.config['envelope']['not_before'] = int(time.time()) + 10
        self.start()
        with patch('swarm.socket.socket') as net:
            self.assertFalse(self.call()['ok']); net.assert_not_called()

    def test_result_audit_failure_poisoned_run(self):
        self.start()
        original = self.plane.ledger.append
        def fail_result(payload):
            if payload['kind'] == 'RESULT': raise OSError('result disk failure')
            return original(payload)
        with patch.object(self.plane.ledger, 'append', side_effect=fail_result):
            with self.assertRaises(OSError): self.call('receive_messages', {})
        self.assertFalse(self.call('receive_messages', {})['ok'])

    def test_symlink_ledger_refused(self):
        self.start(); self.plane.close(); self.plane = None
        path = self.root/'actions.jsonl'; saved = self.root/'saved'
        path.rename(saved); path.symlink_to(saved)
        with self.assertRaises(OSError): self.start()

    def test_nondefault_constructor_cannot_fall_back(self):
        from server import HumanOSRuntime
        with self.assertRaises(ValueError): HumanOSRuntime(config={'profile':PROFILE})
