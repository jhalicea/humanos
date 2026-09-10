import json
import tempfile
import unittest
from pathlib import Path

from subagent_view import SubagentStatusStore, format_subagents, load_snapshot
from swarm_runtime import SwarmRuntime
from tests.test_swarm_runtime import ScriptedModel, config


class SubagentViewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp.cleanup()

    def test_status_snapshot_is_content_light(self):
        manifests = [
            {
                'agent_id': 'worker',
                'model': 'fixture-model',
                'task': 'SENSITIVE TASK CONTENT',
                'token': 'SENSITIVE-TOKEN',
            }
        ]
        store = SubagentStatusStore(
            Path(self.temp.name) / 'control',
            'run-1',
            manifests,
            {'worker': 'worker'},
            4,
        )
        text = store.path.read_text()
        self.assertNotIn('SENSITIVE TASK CONTENT', text)
        self.assertNotIn('SENSITIVE-TOKEN', text)
        snapshot = load_snapshot(store.path)
        self.assertEqual(snapshot['overall_status'], 'READY')
        self.assertEqual(snapshot['agents'][0]['status'], 'queued')

    def test_runtime_publishes_complete_subagent_state(self):
        scripts = {
            'coord': [{'final': 'coord complete'}],
            'worker': [{'final': 'worker complete'}],
            'verify': [{'final': 'verification complete'}],
        }
        runtime = SwarmRuntime(
            config(self.temp.name),
            lambda manifest: ScriptedModel(scripts[manifest['agent_id']]),
        )
        result = runtime.run()
        snapshot = load_snapshot(result['subagent_state'])
        self.assertEqual(snapshot['overall_status'], 'COMPLETE')
        self.assertEqual(snapshot['round'], 1)
        self.assertTrue(all(agent['status'] == 'done' for agent in snapshot['agents']))
        serialized = json.dumps(snapshot)
        self.assertNotIn('fixture authorization', serialized)
        self.assertNotIn('c' * 32, serialized)
        self.assertNotIn('w' * 32, serialized)

    def test_round_limit_marks_unfinished_agents_stopped(self):
        scripts = {
            'coord': [{'final': 'coord complete'}],
            'worker': [{'action': {'tool': 'receive_messages', 'arguments': {}}}],
            'verify': [{'final': 'verification complete'}],
        }
        runtime = SwarmRuntime(
            config(self.temp.name, max_rounds=1),
            lambda manifest: ScriptedModel(scripts[manifest['agent_id']]),
        )
        result = runtime.run()
        snapshot = load_snapshot(result['subagent_state'])
        states = {agent['agent_id']: agent['status'] for agent in snapshot['agents']}
        self.assertEqual(snapshot['overall_status'], 'ROUND_LIMIT')
        self.assertEqual(states['coord'], 'done')
        self.assertEqual(states['worker'], 'stopped')
        self.assertEqual(states['verify'], 'done')

    def test_text_view_has_active_and_done_sections(self):
        store = SubagentStatusStore(
            Path(self.temp.name) / 'control',
            'run-2',
            [
                {'agent_id': 'alpha', 'model': 'm1'},
                {'agent_id': 'beta', 'model': 'm2'},
            ],
            {'alpha': 'worker', 'beta': 'verifier'},
            3,
        )
        store.set_overall('RUNNING', 1)
        store.mark('alpha', 'working', 1, 'invoking model')
        store.mark('beta', 'done', 1, 'finished')
        text = format_subagents(store.snapshot())
        self.assertIn('HumanOS Subagents — RUNNING — round 1/3', text)
        self.assertIn('Active', text)
        self.assertIn('● alpha', text)
        self.assertIn('Done · 1', text)
        self.assertIn('✓ beta', text)


if __name__ == '__main__':
    unittest.main()
