import unittest

from capabilities import model_instructions


class CapabilityExampleSafetyTests(unittest.TestCase):
    def test_examples_are_explicit_placeholders_not_fake_workspace_facts(self):
        instructions = model_instructions()
        self.assertNotIn('example.txt', instructions)
        self.assertIn('syntax placeholders only', instructions)
        self.assertIn('Use a path only when it came from the human or a successful tool observation.', instructions)
        self.assertIn('PATH_FROM_HUMAN_OR_OBSERVATION.txt', instructions)


if __name__ == '__main__':
    unittest.main()
