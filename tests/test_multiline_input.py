import io
import unittest

from server import read_human_input


class FakeTTY(io.StringIO):
    def isatty(self):
        return True


def buffered_select(readers, _writers, _errors, _timeout):
    stream = readers[0]
    ready = stream.tell() < len(stream.getvalue())
    return ([stream] if ready else [], [], [])


class MultilineInputTests(unittest.TestCase):
    def test_single_line_input_is_unchanged(self):
        stdin = FakeTTY('')
        text = read_human_input(
            input_fn=lambda _prompt='': 'hello HumanOS',
            stdin=stdin,
            output=io.StringIO(),
            select_fn=buffered_select,
        )
        self.assertEqual(text, 'hello HumanOS')

    def test_automatic_multiline_paste_is_one_message(self):
        stdin = FakeTTY('second line\nthird line\n')
        text = read_human_input(
            input_fn=lambda _prompt='': 'first line',
            stdin=stdin,
            output=io.StringIO(),
            select_fn=buffered_select,
        )
        self.assertEqual(text, 'first line\nsecond line\nthird line')

    def test_automatic_multiline_paste_preserves_blank_lines(self):
        stdin = FakeTTY('\nthird line\n')
        text = read_human_input(
            input_fn=lambda _prompt='': 'first line',
            stdin=stdin,
            output=io.StringIO(),
            select_fn=buffered_select,
        )
        self.assertEqual(text, 'first line\n\nthird line')

    def test_explicit_paste_mode_ends_only_on_send(self):
        values = iter([':paste', 'first line', '/not-a-command', 'third line', '/send'])
        text = read_human_input(
            input_fn=lambda _prompt='': next(values),
            stdin=FakeTTY(''),
            output=io.StringIO(),
            select_fn=buffered_select,
        )
        self.assertEqual(text, 'first line\n/not-a-command\nthird line')

    def test_leading_spaces_are_preserved(self):
        stdin = FakeTTY('    indented child\n')
        text = read_human_input(
            input_fn=lambda _prompt='': '  indented parent',
            stdin=stdin,
            output=io.StringIO(),
            select_fn=buffered_select,
        )
        self.assertEqual(text, '  indented parent\n    indented child')


if __name__ == '__main__':
    unittest.main()
