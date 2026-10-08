import argparse
import tempfile
import unittest
from pathlib import Path

from routing_dry_run import run_dry_run


class RoutingDryRunTests(unittest.TestCase):
    def _args(self, ledger: Path, **overrides):
        values = {
            "task_id": "DRY-TEST",
            "well_defined": False,
            "operational_state": False,
            "security": False,
            "canonical_state": False,
            "external_action": False,
            "irreversible": False,
            "high_consequence": False,
            "broad_parallel": False,
            "cross_system": False,
            "expensive_to_miss": False,
            "important_artifact": False,
            "owner_override": None,
            "ledger": ledger,
            "no_persist": False,
        }
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_ambiguous_task_dry_run_records_sol_recommendation(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_dry_run(self._args(Path(tmp) / "events.jsonl"))
            rec = result["routing_event"]["recommendation"]
            self.assertEqual("DECIDE", rec["task_class"])
            self.assertEqual("AMBER", rec["risk_lane"])
            self.assertEqual("sol", rec["primary_model"])
            self.assertTrue(result["ledger_recorded"])
            self.assertTrue(result["ledger_verified"])
            self.assertFalse(result["model_dispatched"])
            self.assertFalse(result["authority_granted"])

    def test_no_persist_mode_never_writes_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "events.jsonl"
            result = run_dry_run(self._args(ledger, well_defined=True, no_persist=True))
            self.assertFalse(ledger.exists())
            self.assertFalse(result["ledger_recorded"])
            self.assertIsNone(result["ledger_verified"])
            self.assertEqual("luna", result["routing_event"]["recommendation"]["primary_model"])

    def test_red_dry_run_preserves_review_without_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_dry_run(self._args(
                Path(tmp) / "events.jsonl",
                security=True,
            ))
            rec = result["routing_event"]["recommendation"]
            self.assertEqual("RED", rec["risk_lane"])
            self.assertEqual("sol", rec["primary_model"])
            self.assertEqual("astra", rec["reviewer_model"])
            self.assertFalse(result["model_dispatched"])
            self.assertFalse(result["authority_granted"])


if __name__ == "__main__":
    unittest.main()
