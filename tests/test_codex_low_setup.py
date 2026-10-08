"""Isolated tests; never touch the owner's actual ~/.codex/config.toml."""
import tempfile
import tomllib
import unittest
from pathlib import Path

from scripts.codex_low_setup import install, render


class CodexLowSetupTests(unittest.TestCase):
    def test_new_global_config_sets_all_relevant_defaults(self):
        result = tomllib.loads(render(""))
        self.assertEqual("low", result["model_reasoning_effort"])
        self.assertEqual("low", result["plan_mode_reasoning_effort"])
        self.assertEqual("low", result["agents"]["default_subagent_reasoning_effort"])
        self.assertEqual("gpt-6-luna", result["agents"]["default_subagent_model"])
        self.assertEqual(1, result["agents"]["max_concurrent_threads_per_session"])

    def test_preserve_unrelated_global_and_agent_settings(self):
        before = """model = "gpt-6-astra"
model_reasoning_effort = "high"
approval_policy = "on-request"

[agents]
enabled = true
default_subagent_reasoning_effort = "high"

[mcp_servers.docs]
url = "https://example.test"
"""
        after = tomllib.loads(render(before))
        self.assertEqual("gpt-6-astra", after["model"])
        self.assertEqual("on-request", after["approval_policy"])
        self.assertTrue(after["agents"]["enabled"])
        self.assertEqual("https://example.test", after["mcp_servers"]["docs"]["url"])
        self.assertEqual("low", after["model_reasoning_effort"])

    def test_idempotent(self):
        once = render('[agents]\nenabled = false\n')
        self.assertEqual(once, render(once))

    def test_nested_agent_table_does_not_receive_parent_keys(self):
        before = '[agents.reviewer]\nmodel = "gpt-6-astra"\n'
        out = tomllib.loads(render(before))
        self.assertEqual("gpt-6-astra", out["agents"]["reviewer"]["model"])
        self.assertEqual("low", out["agents"]["default_subagent_reasoning_effort"])

    def test_dry_run_does_not_mutate_global_config(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            path.write_text('model_reasoning_effort = "high"\n')
            output = install(path, dry_run=True)
            self.assertTrue(output["changed"])
            self.assertFalse(output["applied"])
            self.assertEqual('model_reasoning_effort = "high"\n', path.read_text())

    def test_install_backups_and_normalizes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            path.write_text('model_reasoning_effort = "high"\n')
            outcome = install(path)
            self.assertTrue(outcome["applied"])
            self.assertEqual("low", tomllib.loads(path.read_text())["model_reasoning_effort"])
            backup = list(path.parent.glob("config.toml.backup-*"))
            self.assertEqual(1, len(backup))
            self.assertEqual('model_reasoning_effort = "high"\n', backup[0].read_text())
            self.assertFalse(install(path)["changed"])

    def test_warns_for_custom_agent_effort_override(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "agents").mkdir()
            (root / "agents" / "auditor.toml").write_text(
                'name = "auditor"\nmodel_reasoning_effort = "high"\n')
            warnings = install(root / "config.toml")["warnings"]
            self.assertIn("auditor.toml", warnings[0])

    def test_invalid_toml_is_rejected_without_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.toml"
            path.write_text("[broken\n")
            with self.assertRaises(ValueError):
                install(path)
            self.assertEqual("[broken\n", path.read_text())

    def test_symlink_config_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination = root / "actual.toml"
            destination.write_text("")
            (root / "config.toml").symlink_to(destination)
            with self.assertRaises(PermissionError):
                install(root / "config.toml")


if __name__ == "__main__":
    unittest.main()
