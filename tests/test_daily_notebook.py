import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from daily_notebook import project_day, render_day
from notebook import Notebook


class DailyNotebookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.book = Notebook(self.root / 'vault')
        self.identity = self.book.bind('Jon', 'opening')

    def tearDown(self):
        self.book.close()
        self.temp.cleanup()

    def capture(self):
        stamps = iter(('2026-09-10T13:00:00+00:00', '2026-09-10T13:00:01+00:00'))
        with patch('notebook.now', side_effect=lambda: next(stamps)):
            self.book.start(self.identity['hcid'], 'TX-day', 'exact user turn')
            self.book.append('TX-day', 1, 'ASSISTANT', 'exact assistant turn')
        self.book.project()
        self.book.verify()

    def test_exact_daily_projection_and_usage(self):
        self.capture()
        text = render_day(self.book, date(2026, 9, 10))
        self.assertIn('### USER\n\nexact user turn', text)
        self.assertIn('### ASSISTANT\n\nexact assistant turn', text)
        self.assertIn('- Messages captured: 2', text)
        self.assertIn('- User-input characters: 15', text)
        self.assertIn('- Assistant-output characters: 20', text)

    def test_projection_is_idempotent_and_read_back(self):
        self.capture()
        first = project_day(self.book, date(2026, 9, 10), output_dir=self.root / 'out')
        before = first.read_bytes()
        second = project_day(self.book, date(2026, 9, 10), output_dir=self.root / 'out')
        self.assertEqual(first, second)
        self.assertEqual(before, second.read_bytes())

    def test_hidden_text_is_not_exposed_or_counted(self):
        self.capture()
        self.book.set_privacy('TX-day', 0, 'HIDE', confirmation='HIDE')
        text = render_day(self.book, date(2026, 9, 10))
        self.assertNotIn('exact user turn', text)
        self.assertIn('[HIDDEN — content withheld]', text)
        self.assertIn('- User-input characters: 0', text)

    def test_no_messages_creates_nothing(self):
        self.assertIsNone(project_day(self.book, date(2026, 9, 10), output_dir=self.root / 'out'))
        self.assertFalse((self.root / 'out').exists())


if __name__ == '__main__':
    unittest.main()
