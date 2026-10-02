import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from engine import Agent, Tools
from notebook import Notebook
from notebook_memory import (
    capture_memory_from_turn,
    get_preference,
    memory_context,
    rebuild_memory_state,
    verify_memory,
)
from server import _ContextAwareAgent


class _NoRoute:
    applicable = False
    origin = 'NONE'
    source_tx = None
    requires_confirmation = False
    candidates = []
    workspace_id = None
    selected_workstream = None


class _ContextlessRouter:
    def resolve_pending_ambiguity(self, *args, **kwargs):
        return None

    def inspect_history(self, *args, **kwargs):
        return _NoRoute()

    def inspect_session(self, *args, **kwargs):
        return _NoRoute()


class _MemoryAwareModel:
    name = 'memory-test-model'

    def __init__(self):
        self.calls = []

    def invoke(self, messages, timeout):
        copied = json.loads(json.dumps(messages))
        self.calls.append(copied)
        user = copied[-1]['content'].casefold()
        system = copied[0]['content'] if copied else ''
        if 'how do i like my morning summaries' in user:
            return {'final': 'concise' if '"value": "concise"' in system.casefold() else 'unknown'}
        if 'provenance for my morning summaries' in user:
            has_source = all(token in system for token in ('"provenance"', '"page"', '"seq"', '"tx"'))
            return {'final': 'provenance available' if has_source else 'provenance unavailable'}
        return {'final': 'acknowledged'}


class _OutageModel:
    name = 'resume-memory-model'

    def invoke(self, messages, timeout):
        raise RuntimeError('synthetic model outage')


class _ResumeMemoryModel:
    name = 'resume-memory-model'

    def __init__(self):
        self.calls = []

    def invoke(self, messages, timeout):
        copied = json.loads(json.dumps(messages))
        self.calls.append(copied)
        system = copied[0]['content'] if copied else ''
        if '"value": "concise"' in system.casefold() and '"value": "detailed"' not in system.casefold():
            return {'final': 'frozen concise'}
        return {'final': 'wrong memory snapshot'}


class NotebookMemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.vault = self.root / 'vault'
        self.workspace = self.root / 'workspace'
        self.core = self.root / 'core'
        self.core.mkdir()
        (self.core / 'constitution.md').write_text('Human owns HumanOS.')
        self.book = Notebook(self.vault)
        self.book.recover()
        self.binding = self.book.bind('Jon', 'memory acceptance page')

    def tearDown(self):
        if self.book is not None:
            self.book.close()
        self.tmp.cleanup()

    def _complete(self, tx, human, assistant='acknowledged'):
        self.book.start(self.binding['hcid'], tx, human)
        self.book.append(tx, 1, 'ASSISTANT', assistant)
        self.book.save_task(tx, {
            'phase': 'COMPLETE', 'final': assistant, 'final_ordinal': 1,
            'delivery': 'PREPARED_NOT_CONFIRMED',
        })
        self.book.checkpoint(tx)

    def _live_agent(self, model=None):
        base = Agent(self.book, model or _MemoryAwareModel(), Tools(self.workspace), self.core)
        return _ContextAwareAgent(base, _ContextlessRouter(), None)

    def test_preference_has_exact_transcript_provenance_and_is_idempotent(self):
        self._complete('tx-pref-1', 'I prefer concise morning summaries.')
        first = capture_memory_from_turn(self.book, 'tx-pref-1')
        second = capture_memory_from_turn(self.book, 'tx-pref-1')
        self.assertEqual(first['status'], 'CAPTURED')
        self.assertEqual(second['status'], 'ALREADY_CAPTURED')
        self.assertEqual(second['event_id'], first['event_id'])
        remembered = get_preference(self.book, 'Jon', 'morning summaries')
        self.assertEqual(remembered['status'], 'ACTIVE')
        self.assertEqual(remembered['value'], 'concise')
        self.assertEqual(remembered['provenance']['tx'], 'tx-pref-1')
        self.assertEqual(remembered['provenance']['message'], 'I prefer concise morning summaries.')
        self.assertIsInstance(remembered['provenance']['seq'], int)
        self.assertTrue(remembered['provenance']['page'].startswith('LN-'))
        self.assertEqual(verify_memory(self.book)['events'], 1)

    def test_restart_preserves_preference_and_provenance(self):
        self._complete('tx-pref-restart', 'I prefer concise morning summaries.')
        capture_memory_from_turn(self.book, 'tx-pref-restart')
        hcid = self.binding['hcid']
        self.book.close()
        self.book = Notebook(self.vault)
        self.book.recover()
        self.assertEqual(self.book.get_identity(hcid)['owner'], 'Jon')
        remembered = get_preference(self.book, 'Jon', 'morning summaries')
        self.assertEqual(remembered['value'], 'concise')
        self.assertEqual(remembered['provenance']['tx'], 'tx-pref-restart')
        self.assertEqual(verify_memory(self.book)['status'], 'VERIFIED')

    def test_explicit_correction_supersedes_without_rewriting_history(self):
        self._complete('tx-old', 'I prefer concise morning summaries.')
        old = capture_memory_from_turn(self.book, 'tx-old')
        self._complete('tx-new', 'Actually, make them detailed.')
        new = capture_memory_from_turn(self.book, 'tx-new')
        self.assertEqual(new['supersedes'], old['event_id'])
        replay = capture_memory_from_turn(self.book, 'tx-new')
        self.assertEqual(replay['status'], 'ALREADY_CAPTURED')
        self.assertEqual(replay['event_id'], new['event_id'])
        events = list(self.book.db.execute(
            'SELECT event_id,value,supersedes FROM memory_events ORDER BY seq'))
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]['value'], 'concise')
        self.assertIsNone(events[0]['supersedes'])
        self.assertEqual(events[1]['value'], 'detailed')
        self.assertEqual(events[1]['supersedes'], events[0]['event_id'])
        remembered = get_preference(self.book, 'Jon', 'morning summaries')
        self.assertEqual(remembered['value'], 'detailed')
        self.assertEqual(remembered['provenance']['tx'], 'tx-new')
        self.assertEqual(verify_memory(self.book)['events'], 2)

    def test_unqualified_second_declaration_becomes_conflicted(self):
        self._complete('tx-a', 'I prefer concise morning summaries.')
        capture_memory_from_turn(self.book, 'tx-a')
        self._complete('tx-b', 'I prefer detailed morning summaries.')
        capture_memory_from_turn(self.book, 'tx-b')
        remembered = get_preference(self.book, 'Jon', 'morning summaries')
        self.assertEqual(remembered['status'], 'CONFLICTED')
        context = memory_context(self.book, 'Jon')
        self.assertEqual(context['preferences'], [])
        self.assertEqual(context['conflicts'], [
            {'subject': 'morning summaries', 'status': 'CONFLICTED'}])

    def test_derived_state_can_be_destroyed_and_rebuilt_from_events(self):
        self._complete('tx-rebuild', 'I prefer concise morning summaries.')
        capture_memory_from_turn(self.book, 'tx-rebuild')
        with self.book.db:
            self.book.db.execute('DELETE FROM memory_state')
        self.assertEqual(get_preference(self.book, 'Jon', 'morning summaries')['status'], 'NOT_FOUND')
        rebuilt = rebuild_memory_state(self.book)
        self.assertEqual(rebuilt, {'status': 'REBUILT', 'records': 1})
        self.assertEqual(get_preference(self.book, 'Jon', 'morning summaries')['value'], 'concise')
        self.assertEqual(verify_memory(self.book)['status'], 'VERIFIED')

    def test_live_mirror_loop_captures_restart_context_and_supersession(self):
        model = _MemoryAwareModel()
        agent = self._live_agent(model)
        result = agent.run('tx-live-1', self.binding['hcid'], 'I prefer concise morning summaries.')
        self.assertEqual(result, 'acknowledged')
        self.assertEqual(get_preference(self.book, 'Jon', 'morning summaries')['value'], 'concise')
        receipt = self.book.task('tx-live-1')['memory_capture']
        self.assertEqual(set(receipt), {'status', 'event_id', 'supersedes', 'tx'})
        self.assertNotIn('state', receipt)

        hcid = self.binding['hcid']
        self.book.close()
        self.book = Notebook(self.vault)
        self.book.recover()
        model = _MemoryAwareModel()
        agent = self._live_agent(model)

        answer = agent.run('tx-live-2', hcid, 'How do I like my morning summaries?')
        self.assertEqual(answer, 'concise')
        self.assertIn('LOCAL_DERIVED_LIFE_NOTEBOOK_STATE', model.calls[-1][0]['content'])

        provenance = agent.run('tx-live-3', hcid, 'What is the provenance for my morning summaries?')
        self.assertEqual(provenance, 'provenance available')

        correction = agent.run('tx-live-4', hcid, 'Actually, make them detailed.')
        self.assertEqual(correction, 'acknowledged')
        remembered = get_preference(self.book, 'Jon', 'morning summaries')
        self.assertEqual(remembered['value'], 'detailed')
        self.assertEqual(remembered['provenance']['tx'], 'tx-live-4')
        self.assertEqual(self.book.db.execute('SELECT COUNT(*) FROM memory_events').fetchone()[0], 2)

    def test_interrupted_task_resumes_with_exact_bound_memory_snapshot(self):
        self._complete('tx-pref-base', 'I prefer concise morning summaries.')
        first = capture_memory_from_turn(self.book, 'tx-pref-base')
        agent = self._live_agent(_OutageModel())

        with self.assertRaisesRegex(RuntimeError, 'synthetic model outage'):
            agent.run('tx-interrupted', self.binding['hcid'], 'Tell me something.')

        binding_row = self.book.db.execute(
            "SELECT payload FROM events WHERE tx=? AND kind='MEMORY_CONTEXT_BOUND' ORDER BY seq LIMIT 1",
            ('tx-interrupted',),
        ).fetchone()
        self.assertIsNotNone(binding_row)
        binding = json.loads(binding_row['payload'])
        self.assertEqual(binding['status'], 'READY')
        self.assertEqual(binding['event_ids'], [first['event_id']])
        self.assertNotIn('concise', binding_row['payload'].casefold())
        self.assertNotIn('morning summaries', binding_row['payload'].casefold())

        self._complete('tx-pref-change', 'Actually, make them detailed.')
        capture_memory_from_turn(self.book, 'tx-pref-change')
        self.assertEqual(get_preference(self.book, 'Jon', 'morning summaries')['value'], 'detailed')

        resume_model = _ResumeMemoryModel()
        agent._agent.model = resume_model
        answer = agent.run('tx-interrupted', self.binding['hcid'])
        self.assertEqual(answer, 'frozen concise')
        system = resume_model.calls[-1][0]['content']
        self.assertIn('"value": "concise"', system.casefold())
        self.assertNotIn('"value": "detailed"', system.casefold())
        binding_count = self.book.db.execute(
            "SELECT COUNT(*) FROM events WHERE tx=? AND kind='MEMORY_CONTEXT_BOUND'",
            ('tx-interrupted',),
        ).fetchone()[0]
        self.assertEqual(binding_count, 1)

    def test_memory_failure_cannot_erase_or_block_completed_conversation(self):
        model = _MemoryAwareModel()
        agent = self._live_agent(model)
        with patch('server.capture_memory_from_turn', side_effect=RuntimeError('synthetic extractor failure')):
            result = agent.run('tx-failure', self.binding['hcid'], 'I prefer concise morning summaries.')
        self.assertEqual(result, 'acknowledged')
        transcript = list(self.book.db.execute(
            "SELECT role,text FROM transcript WHERE tx='tx-failure' ORDER BY seq"))
        self.assertEqual([(row['role'], row['text']) for row in transcript], [
            ('HUMAN', 'I prefer concise morning summaries.'),
            ('ASSISTANT', 'acknowledged'),
        ])
        state = self.book.task('tx-failure')
        self.assertEqual(state['phase'], 'COMPLETE')
        self.assertEqual(state['memory_capture']['status'], 'MEMORY_EXTRACTION_FAILED')
        self.assertEqual(state['memory_capture']['error_type'], 'RuntimeError')


if __name__ == '__main__':
    unittest.main()
