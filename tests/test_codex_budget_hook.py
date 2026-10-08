"""Tests for finite Codex hook budgets; does not call a model."""
import json
import tempfile
import unittest
from pathlib import Path
from scripts.codex_budget_hook import MAX_TURNS, MAX_TOOLS, SCHEMA, assess, run, scoped
from scripts.codex_budget_setup import merge

class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.s = {"schema": SCHEMA, "sessions": {}}
    def call(self, name, key, n):
        return assess({"session_id": "s", "hook_event_name": name, key: str(n)}, self.s, 100)
    def test_scope(self):
        h = Path("/Users/test")
        self.assertTrue(scoped("/Users/test/Developer/10_Repos/humanos", h))
        self.assertTrue(scoped("/Users/test/Developer/20_Worktrees/humanos/feature", h))
        self.assertFalse(scoped("/Users/test/Developer/10_Repos/bodyfixos", h))
    def test_turns(self):
        for n in range(MAX_TURNS):
            self.assertTrue(self.call("UserPromptSubmit", "turn_id", n)[1])
        r, change = self.call("UserPromptSubmit", "turn_id", 99)
        self.assertEqual("block", r["decision"])
        self.assertFalse(change)
    def test_tools(self):
        self.call("UserPromptSubmit", "turn_id", 0)
        for n in range(MAX_TOOLS):
            self.assertTrue(self.call("PreToolUse", "tool_use_id", n)[1])
        r, _ = self.call("PreToolUse", "tool_use_id", 99)
        self.assertEqual("deny", r["hookSpecificOutput"]["permissionDecision"])
    def test_time_and_idempotence(self):
        self.call("UserPromptSubmit", "turn_id", 1)
        self.assertFalse(self.call("UserPromptSubmit", "turn_id", 1)[1])
        r, changed = assess({"session_id":"s","hook_event_name":"PreToolUse",
          "tool_use_id":"a"}, self.s, 1000)
        self.assertFalse(changed)
        self.assertEqual("deny",r["hookSpecificOutput"]["permissionDecision"])
    def test_state_persistence(self):
        with tempfile.TemporaryDirectory() as directory:
            h=Path(directory); root=h/"Developer"/"10_Repos"/"humanos";root.mkdir(parents=True)
            event={"cwd":str(root),"session_id":"s","hook_event_name":"UserPromptSubmit","turn_id":"t"}
            self.assertEqual({},run(event,home=h,now=100))
            stored=(h/".codex"/"humanos-budget"/"state.json").read_text()
            self.assertNotIn('"s"',stored)
    def test_merge_existing_hooks(self):
        original=json.dumps({"hooks":{"SessionStart":[{"hooks":[{"command":"existing"}]}]}})
        after=merge(original,"python budget")
        self.assertEqual(after,merge(after,"python budget"))
        self.assertEqual("existing",json.loads(after)["hooks"]["SessionStart"][0]["hooks"][0]["command"])

if __name__=="__main__":
    unittest.main()
