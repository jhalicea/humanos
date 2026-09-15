import json
import tempfile
import unittest
from pathlib import Path

from mirror_router_adapter import (
    RoutingContext,
    RoutingEventLedger,
    build_mirror_routing_event,
    route_for_mirror,
)
from model_router import ExperimentWorkflow, TaskProfile


class MirrorRouterAdapterTests(unittest.TestCase):
    def test_event_is_proposal_only_and_never_dispatches(self):
        result = route_for_mirror(TaskProfile(task_id="M1", well_defined=False))
        event = result["routing_event"]
        self.assertEqual("PROPOSED", event["status"])
        self.assertFalse(event["dispatch_allowed"])
        self.assertFalse(event["automatic_execution"])
        self.assertFalse(event["authority_granted"])
        self.assertFalse(event["policy_promotion"])
        self.assertFalse(result["model_dispatched"])
        self.assertFalse(result["authority_granted"])

    def test_adapter_preserves_candidate_route(self):
        event = build_mirror_routing_event(
            TaskProfile(task_id="M2", well_defined=True),
            event_id="evt-M2",
            created_at="2026-09-15T20:00:00+00:00",
        )
        recommendation = event["recommendation"]
        self.assertEqual("BUILD", recommendation["task_class"])
        self.assertEqual("luna", recommendation["primary_model"])
        self.assertEqual("learning", recommendation["router_mode"])
        self.assertFalse(recommendation["policy_locked"])

    def test_context_is_provenance_only_and_does_not_change_route(self):
        task = TaskProfile(task_id="M2B", well_defined=False)
        plain = build_mirror_routing_event(task)
        enriched = build_mirror_routing_event(
            task,
            context=RoutingContext(
                task_description="Decide how to route a new HumanOS subsystem build.",
                classifier_source="manual_test",
                classifier_confidence="HIGH",
                evidence_refs=("trial-b", "mpc-r3"),
                assumptions=("No provider execution requested",),
            ),
        )
        self.assertEqual(plain["recommendation"], enriched["recommendation"])
        context = enriched["routing_context"]
        self.assertEqual("HIGH", context["classifier_confidence"])
        self.assertEqual(["trial-b", "mpc-r3"], context["evidence_refs"])
        self.assertFalse(context["affects_route"])

    def test_experimental_workflow_is_preserved_but_not_promoted(self):
        event = build_mirror_routing_event(TaskProfile(
            task_id="M3",
            well_defined=True,
            operational_state_dominant=True,
            experiment_workflow=ExperimentWorkflow(
                experiment_id="MPC-R4",
                advisor_model="astra",
                advisor_effort="light",
                worker_model="terra",
                worker_effort="high",
                owner_accepted=True,
            ),
        ))
        workflow = event["recommendation"]["experimental_workflow"]
        self.assertEqual("astra", workflow["advisor_model"])
        self.assertEqual("light", workflow["advisor_effort"])
        self.assertEqual("terra", workflow["worker_model"])
        self.assertEqual("high", workflow["worker_effort"])
        self.assertFalse(workflow["promoted_to_policy"])
        self.assertFalse(event["policy_promotion"])

    def test_ledger_persists_and_verifies_one_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = RoutingEventLedger(Path(tmp) / "routing-events.jsonl")
            result = route_for_mirror(
                TaskProfile(task_id="M4", well_defined=False),
                ledger=ledger,
                event_id="evt-M4",
                created_at="2026-09-15T20:01:00+00:00",
            )
            self.assertIsNotNone(result["ledger_record"])
            self.assertEqual(1, result["ledger_record"]["seq"])
            self.assertTrue(ledger.verify())

    def test_ledger_chains_multiple_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = RoutingEventLedger(Path(tmp) / "routing-events.jsonl")
            route_for_mirror(TaskProfile(task_id="M5", well_defined=True), ledger=ledger, event_id="evt-M5")
            route_for_mirror(TaskProfile(task_id="M6", well_defined=False), ledger=ledger, event_id="evt-M6")
            events = ledger.read_all()
            self.assertEqual(2, len(events))
            self.assertEqual(events[0].event_hash, events[1].previous_hash)
            self.assertTrue(ledger.verify())

    def test_tampered_ledger_fails_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "routing-events.jsonl"
            ledger = RoutingEventLedger(path)
            route_for_mirror(TaskProfile(task_id="M7", well_defined=True), ledger=ledger, event_id="evt-M7")

            raw = json.loads(path.read_text(encoding="utf-8").strip())
            raw["body"]["status"] = "EXECUTED"
            path.write_text(json.dumps(raw) + "\n", encoding="utf-8")

            self.assertFalse(ledger.verify())
            with self.assertRaises(ValueError):
                ledger.append(action_id="evt-M8", body={"tampered": True})


if __name__ == "__main__":
    unittest.main()
