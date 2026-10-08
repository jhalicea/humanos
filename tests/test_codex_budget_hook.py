"""Tests for finite Codex hook budgets; does not call a model."""
import json
import tempfile
import unittest
from pathlib import Path
from scripts.codex_budget_hook import MAX_TURNS, MAX_TOOLS, SCHEMA, assess, run, scoped, low_configuration_problem
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
            codex=h/".codex";codex.mkdir()
            (codex/"config.toml").write_text(
                'model_reasoning_effort = "low"\n'
                'plan_mode_reasoning_effort = "low"\n'
                '[agents]\n'
                'default_subagent_model = "gpt-6-luna"\n'
                'default_subagent_reasoning_effort = "low"\n'
                'max_concurrent_threads_per_session = 1\n')
            event={"cwd":str(root),"session_id":"s","hook_event_name":"UserPromptSubmit","turn_id":"t"}
            self.assertEqual({},run(event,home=h,now=100))
            stored=(h/".codex"/"humanos-budget"/"state.json").read_text()
            self.assertNotIn('"s"',stored)
    def test_low_effort_drift_blocks_without_consuming_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            codex = home / ".codex"
            codex.mkdir()
            config = codex / "config.toml"
            config.write_text(
                'model_reasoning_effort = "high"\n'
                'plan_mode_reasoning_effort = "low"\n'
                '[agents]\n'
                'default_subagent_model = "gpt-6-luna"\n'
                'default_subagent_reasoning_effort = "low"\n'
                'max_concurrent_threads_per_session = 1\n')
            self.assertEqual("LOW_EFFORT_DEFAULTS_DRIFTED",
                             low_configuration_problem(home))
            root = home / "Developer" / "10_Repos" / "humanos"
            root.mkdir(parents=True)
            event = {"cwd": str(root), "session_id": "s",
                     "hook_event_name": "UserPromptSubmit", "turn_id": "t"}
            self.assertEqual("block", run(event, home=home, now=100)["decision"])
            self.assertFalse((codex / "humanos-budget" / "state.json").exists())

    def test_custom_astra_high_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            codex = home / ".codex"
            (codex / "agents").mkdir(parents=True)
            (codex / "config.toml").write_text(
                'model_reasoning_effort = "low"\n'
                'plan_mode_reasoning_effort = "low"\n'
                '[agents]\n'
                'default_subagent_model = "gpt-6-luna"\n'
                'default_subagent_reasoning_effort = "low"\n'
                'max_concurrent_threads_per_session = 1\n')
            agent = codex / "agents" / "astra.toml"
            agent.write_text('model_reasoning_effort = "high"\n')
            self.assertEqual("CUSTOM_AGENT_EFFORT_NOT_LOW",
                             low_configuration_problem(home))
            agent.write_text('model_reasoning_effort = "low"\n')
            self.assertIsNone(low_configuration_problem(home))

    def test_effective_effort_if_explicitly_reported_is_checked(self):
        response, changed = assess(
            {"session_id": "s", "hook_event_name": "UserPromptSubmit",
             "turn_id": "t", "model_reasoning_effort": "high"},
            self.s, 100)
        self.assertFalse(changed)
        self.assertEqual("block", response["decision"])
        self.assertIn("EFFECTIVE_EFFORT_NOT_LOW", response["reason"])

    def test_merge_existing_hooks(self):
        original=json.dumps({"hooks":{"SessionStart":[{"hooks":[{"command":"existing"}]}]}})
        after=merge(original,"python budget")
        self.assertEqual(after,merge(after,"python budget"))
        self.assertEqual("existing",json.loads(after)["hooks"]["SessionStart"][0]["hooks"][0]["command"])

if __name__=="__main__":
    unittest.main()
