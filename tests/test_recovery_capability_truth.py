import tempfile
import unittest
from pathlib import Path

from capabilities import model_instructions, runtime_describe, summary
from engine import Tools
from notebook import Notebook


class RecoveryClassificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.book = Notebook(self.root / 'vault')
        self.book.recover()
        self.binding = self.book.bind('Jon', 'opening')

    def tearDown(self):
        self.book.close()
        self.tmp.cleanup()

    def test_bare_started_transaction_is_not_resumable(self):
        self.book.start(self.binding['hcid'], 'bare', 'historical fragment')
        self.assertEqual(self.book.recovery_classification('bare'), 'NEEDS_RECONCILIATION')
        queue = {item['tx']: item for item in self.book.recovery_pending()}
        self.assertEqual(queue['bare']['recovery_kind'], 'NEEDS_RECONCILIATION')

    def test_saved_model_task_is_resumable(self):
        self.book.start(self.binding['hcid'], 'task', 'continue useful work')
        self.book.save_task('task', {
            'phase': 'MODEL',
            'permissions': {'version': 4},
            'model': 'test-model',
            'workspace': str(self.root / 'workspace'),
        })
        self.assertEqual(self.book.recovery_classification('task'), 'RESUMABLE')

    def test_external_capture_never_becomes_execution(self):
        self.book.start(self.binding['hcid'], 'capture', 'captured transcript fragment')
        self.book.save_task('capture', {
            'phase': 'EXTERNAL_CAPTURE_PENDING',
            'capture_source': 'external',
        })
        self.assertEqual(self.book.recovery_classification('capture'), 'CAPTURE_ONLY')
        self.assertNotEqual(self.book.recovery_classification('capture'), 'RESUMABLE')

    def test_summary_separates_recovery_classes(self):
        self.book.start(self.binding['hcid'], 'bare', 'fragment')
        self.book.start(self.binding['hcid'], 'task', 'real task')
        self.book.save_task('task', {'phase': 'MODEL', 'permissions': {'version': 4}})
        self.book.start(self.binding['hcid'], 'capture', 'capture')
        self.book.save_task('capture', {'phase': 'EXTERNAL_CAPTURE_PENDING'})
        result = self.book.recovery_summary()
        self.assertEqual(result['resumable'], 1)
        self.assertEqual(result['needs_reconciliation'], 1)
        self.assertEqual(result['capture_only'], 1)


class CapabilityTruthTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tmp.name) / 'workspace'

    def tearDown(self):
        self.tmp.cleanup()

    def test_browser_registered_but_not_ready_without_bridge(self):
        tools = Tools(self.workspace)
        states = tools.capability_states()
        browser = states['browser_inspect']
        self.assertTrue(browser['registered'])
        self.assertFalse(browser['configured'])
        self.assertFalse(browser['ready'])
        self.assertEqual(browser['state'], 'REGISTERED_NOT_CONFIGURED')

        described = {item['name']: item for item in runtime_describe(states)}
        self.assertFalse(described['browser_inspect']['available'])
        self.assertEqual(
            described['browser_inspect']['runtime_state']['state'],
            'REGISTERED_NOT_CONFIGURED',
        )

    def test_model_is_not_told_unconfigured_browser_is_available(self):
        tools = Tools(self.workspace)
        instructions = model_instructions(tools.capability_states())
        self.assertIn('browser_inspect: unavailable; the browser tool is installed', instructions)
        self.assertNotIn('{"tool": {"name": "browser_inspect"', instructions)

    def test_human_summary_explains_browser_remediation(self):
        tools = Tools(self.workspace)
        text = summary(tools.capability_states())
        self.assertIn('REGISTERED_NOT_CONFIGURED', text)
        self.assertIn('BROWSER.md', text)
        self.assertIn('Human approval gates remain required', text)


if __name__ == '__main__':
    unittest.main()
