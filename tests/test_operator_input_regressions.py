import io
import unittest

from runtime_info import intent, request_for
from server import PASTE_GRACE_SECONDS, read_human_input


class _DelayedPasteStdin:
    def __init__(self, lines):
        self.lines = list(lines)

    def isatty(self):
        return True

    def readline(self):
        return self.lines.pop(0) if self.lines else ''


class OperatorInputRegressionTests(unittest.TestCase):
    def test_multiline_paste_allows_interline_arrival_delay(self):
        stdin = _DelayedPasteStdin(['second\n', '\n', 'third\n'])
        waits = []

        def delayed_select(readers, writers, errors, timeout):
            waits.append(timeout)
            # Simulate the next pasted line appearing ~30 ms later rather than
            # assuming the whole paste was already buffered. The old zero-time
            # continuation check stopped after the first continuation line.
            ready = bool(stdin.lines) and timeout >= 0.03
            return (readers if ready else [], [], [])

        result = read_human_input(
            input_fn=lambda prompt='': 'first',
            stdin=stdin,
            output=io.StringIO(),
            select_fn=delayed_select,
            paste_wait=PASTE_GRACE_SECONDS,
        )

        self.assertEqual(result, 'first\nsecond\n\nthird')
        self.assertGreaterEqual(PASTE_GRACE_SECONDS, 0.03)
        self.assertTrue(all(wait >= 0.03 for wait in waits[:-1]))

    def test_explicit_paste_mode_remains_deterministic(self):
        values = iter([':paste', 'line one', '', 'line three', '/send'])
        result = read_human_input(
            input_fn=lambda prompt='': next(values),
            stdin=_DelayedPasteStdin([]),
            output=io.StringIO(),
        )
        self.assertEqual(result, 'line one\n\nline three')

    def test_long_task_mentioning_notebook_is_not_hijacked(self):
        text = (
            'HUMANOS JOB HOS-R1-LOCAL-001-A3. ROLE: Local HumanOS capability auditor. '
            'This is a clean benchmark turn. Use runtime_capabilities and read_source only if needed. '
            'DO NOT use read_notebook or prior conversation history. Report ONLY: 1) actual capabilities '
            'verified from current tool observations; 2) top five missing or incomplete capabilities, ranked; '
            '3) the single capability to build next; 4) evidence for each claim; 5) exact local model identity '
            'only if actually observable, otherwise UNKNOWN.'
        )
        self.assertIsNone(intent(text))
        self.assertIsNone(request_for(text, []))

    def test_negative_notebook_constraint_never_routes_to_notebook(self):
        for text in ('do not use read_notebook', 'never read the notebook', 'avoid the notebook'):
            with self.subTest(text=text):
                self.assertNotEqual(intent(text), 'notebook')
                self.assertNotEqual(request_for(text, []), {'name': 'read_notebook'})

    def test_explicit_and_concise_notebook_queries_still_route_directly(self):
        self.assertEqual(intent('/notebook'), 'notebook')
        self.assertEqual(request_for('/notebook', []), {'name': 'read_notebook'})
        question = 'is this conversation in the notebook?'
        self.assertEqual(intent(question), 'notebook')
        self.assertEqual(request_for(question, []), {'name': 'read_notebook'})


if __name__ == '__main__':
    unittest.main()
