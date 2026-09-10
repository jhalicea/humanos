from pathlib import Path

path = Path(__file__).resolve().parents[1] / "references.py"
text = path.read_text()
old = '''    if not lowered:\n        return None\n    if re.search(r"\\b(plan|changes?|moves?)\\b", lowered) and (_REFERENCE.search(lowered) or _PLAN_ACTION.search(lowered)):\n'''
new = '''    if not lowered:\n        return None\n    # Explicit slash commands already carry exact human authority. Never let\n    # conversational reference resolution replace their target with history.\n    if re.match(r"^/(?:apply|undo)\\s+\\S+", lowered):\n        return None\n    if re.search(r"\\b(plan|changes?|moves?)\\b", lowered) and (_REFERENCE.search(lowered) or _PLAN_ACTION.search(lowered)):\n'''
if text.count(old) != 1:
    raise SystemExit("references.py explicit-command anchor mismatch")
path.write_text(text.replace(old, new, 1))

with (Path(__file__).resolve().parents[1] / "tests" / "test_references.py").open("a") as f:
    f.write(r'''

class ContextReferenceExplicitAuthorityTests(unittest.TestCase):
    setUp = test_runtime.RuntimeTests.setUp
    tearDown = test_runtime.RuntimeTests.tearDown

    def test_explicit_apply_command_is_never_reference_resolved(self):
        from references import reference_intent
        self.assertIsNone(reference_intent('/apply PLAN-EXACT-123'))
        self.assertIsNone(reference_intent('/undo PLAN-EXACT-123'))
''')
