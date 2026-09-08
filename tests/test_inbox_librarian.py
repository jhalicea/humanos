import json
from pathlib import Path
import tempfile
import unittest

from engine import Agent, Tools
from file_manager import FileManager
from inbox_librarian import InboxLibrarian
from notebook import Notebook
from runtime_info import format_plan, request_for


class InboxModel:
    name = 'inbox-test-model'
    def __init__(self, proposal): self.proposal, self.calls = proposal, []
    def structured(self, messages, timeout):
        self.calls.append(messages)
        return dict(self.proposal)
    def invoke(self, messages, timeout): return {'final': 'ordinary response'}


def proposal(folder='Projects/Atlas', filename='internet-access-guide.pdf'):
    return {'destination_folder': folder, 'suggested_filename': filename,
            'summary': 'A reference document about internet access.',
            'rationale': 'The content and file type fit the Atlas research area.', 'confidence': .88}


class InboxLibrarianTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.workspace = self.root / 'workspace'; (self.workspace / 'inbox').mkdir(parents=True)
        self.book = Notebook(self.root / 'vault'); self.book.recover()
        self.manager = FileManager(self.workspace, self.book)
    def tearDown(self): self.book.close(); self.tmp.cleanup()

    def test_generic_name_gets_reviewable_rename_and_destination(self):
        source = self.workspace / 'inbox/internet.pdf'; source.write_bytes(b'%PDF-1.4 no extracted text')
        model = InboxModel(proposal())
        plan = InboxLibrarian(self.manager, model).plan('inbox', 'tx')
        move = plan['moves'][0]
        self.assertEqual(move['destination'], 'inbox/Projects/Atlas/internet-access-guide.pdf')
        self.assertTrue(move['classification']['generic_name'])
        self.assertTrue(move['classification']['rename'])
        self.assertIn('Suggested filename:', format_plan(plan))
        self.assertTrue(source.exists())

    def test_descriptive_name_can_be_kept_without_fake_rename(self):
        self.workspace.joinpath('inbox/atlas-research.pdf').write_bytes(b'%PDF-1.4')
        model = InboxModel(proposal('.', 'atlas-research.pdf'))
        plan = InboxLibrarian(self.manager, model).plan('inbox')
        self.assertEqual(plan['moves'], [])
        item = plan['metadata']['decisions'][0]
        self.assertFalse(item['classification']['generic_name'])
        self.assertFalse(item['classification']['rename'])

    def test_filename_path_or_extension_change_fails_closed(self):
        intelligence = InboxLibrarian(self.manager, InboxModel(proposal()))
        for filename in ('folder/name.pdf', 'renamed.txt', '.hidden.pdf'):
            bad = dict(proposal(), suggested_filename=filename)
            with self.subTest(filename=filename), self.assertRaises((ValueError, PermissionError)):
                intelligence._validate(bad, 'internet.pdf')

    def test_idempotent_inbox_plan_does_not_repeat_model_call(self):
        self.workspace.joinpath('inbox/internet.pdf').write_bytes(b'%PDF-1.4')
        model = InboxModel(proposal())
        librarian = InboxLibrarian(self.manager, model)
        first = librarian.plan('inbox', 'same')
        second = librarian.plan('inbox', 'same')
        self.assertEqual(first, second)
        self.assertEqual(len(model.calls), 1)

    def test_inbox_command_and_natural_language_are_explicit(self):
        self.assertEqual(request_for('/organize-inbox', []), {'name': 'plan_inbox_organization', 'path': 'inbox'})
        self.assertEqual(request_for('Mirror organize my inbox', []), {'name': 'plan_inbox_organization', 'path': 'inbox'})
        self.assertIsNone(request_for('organize my inbox except taxes', []))


class InboxAgentTests(unittest.TestCase):
    def test_agent_captures_inbox_preview_without_moving(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); workspace = root / 'workspace'; (workspace / 'inbox').mkdir(parents=True)
            (workspace / 'inbox/internet.pdf').write_bytes(b'%PDF-1.4')
            book = Notebook(root / 'vault'); book.recover(); identity = book.bind('Jon', 'inbox')
            try:
                model = InboxModel(proposal())
                agent = Agent(book, model, Tools(workspace), root / 'core', finalize_on_error=True)
                final = agent.run('tx', identity['hcid'], '/organize-inbox')
                self.assertIn('Suggested filename:', final)
                self.assertTrue((workspace / 'inbox/internet.pdf').exists())
                self.assertEqual(book.get_transaction('tx')['status'], 'CHECKPOINTED')
            finally:
                book.close()


if __name__ == '__main__': unittest.main()
