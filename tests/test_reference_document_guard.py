import unittest

from references import reference_intent


class ReferenceDocumentGuardTests(unittest.TestCase):
    def test_short_plan_followups_still_bind(self):
        self.assertEqual(reference_intent('run that plan'), 'plan')
        self.assertEqual(reference_intent('do it'), 'plan')

    def test_short_file_followup_still_binds(self):
        self.assertEqual(reference_intent('read that file'), 'file')

    def test_multiline_review_packet_is_not_reinterpreted_as_plan_reference(self):
        text = '''HumanOS SQLite review\n\nAnalyze the current design.\nRun the transaction plan against these requirements.\nUse the results to produce a final verdict.\nDo not write production code.\n'''
        self.assertIsNone(reference_intent(text))

    def test_long_single_line_instruction_is_not_reinterpreted_as_reference(self):
        text = ('Review this implementation and use the plan terminology only as part of the analysis. ' * 8).strip()
        self.assertGreater(len(text), 400)
        self.assertIsNone(reference_intent(text))


if __name__ == '__main__':
    unittest.main()
