import json
import multiprocessing
import tempfile
import threading
import unittest
from pathlib import Path

from mirror_router_adapter import (
    RoutingEventLedger,
    RoutingLedgerConflict,
    RoutingLedgerCorrupt,
    RoutingLedgerUnsafe,
    build_mirror_routing_event,
    route_for_mirror,
)
from model_router import ExperimentWorkflow, TaskProfile


def _process_append_worker(path, event_id, start_event, result_queue):
    try:
        start_event.wait(5)
        route_for_mirror(
            TaskProfile(task_id=event_id, well_defined=True),
            ledger=RoutingEventLedger(path),
            event_id=event_id,
        )
        result_queue.put(None)
    except Exception as error:  # pragma: no cover - only returned to parent for assertion
        result_queue.put(repr(error))


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
            with self.assertRaises(RoutingLedgerCorrupt):
                ledger.append(action_id="evt-M8", body={"tampered": True})

    def test_symlink_ledger_path_is_rejected_before_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target.jsonl"
            target.write_text("", encoding="utf-8")
            link = root / "routing-events.jsonl"
            link.symlink_to(target)
            ledger = RoutingEventLedger(link)
            with self.assertRaises(RoutingLedgerUnsafe):
                ledger.append(action_id="evt-symlink", body={"safe": True})
            self.assertEqual("", target.read_text(encoding="utf-8"))

    def test_symlink_lock_path_is_rejected_before_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "lock-target"
            target.write_text("do-not-touch", encoding="utf-8")
            (root / ".routing-events.lock").symlink_to(target)
            ledger = RoutingEventLedger(root / "routing-events.jsonl")
            with self.assertRaises(RoutingLedgerUnsafe):
                ledger.append(action_id="evt-lock-symlink", body={"safe": True})
            self.assertFalse((root / "routing-events.jsonl").exists())
            self.assertEqual("do-not-touch", target.read_text(encoding="utf-8"))

    def test_unterminated_tail_blocks_append_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "routing-events.jsonl"
            raw = b'{"seq":1'
            path.write_bytes(raw)
            ledger = RoutingEventLedger(path)
            with self.assertRaises(RoutingLedgerCorrupt):
                ledger.append(action_id="evt-after-tail", body={"safe": True})
            self.assertEqual(raw, path.read_bytes())

    def test_malformed_complete_record_blocks_append_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "routing-events.jsonl"
            raw = b'not-json\n'
            path.write_bytes(raw)
            ledger = RoutingEventLedger(path)
            with self.assertRaises(RoutingLedgerCorrupt):
                ledger.append(action_id="evt-after-corruption", body={"safe": True})
            self.assertEqual(raw, path.read_bytes())

    def test_identical_event_retry_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "routing-events.jsonl"
            ledger = RoutingEventLedger(path)
            kwargs = {
                "ledger": ledger,
                "event_id": "evt-retry",
                "created_at": "2026-09-15T20:02:00+00:00",
            }
            first = route_for_mirror(TaskProfile(task_id="M9", well_defined=True), **kwargs)
            second = route_for_mirror(TaskProfile(task_id="M9", well_defined=True), **kwargs)
            self.assertEqual(first["ledger_record"], second["ledger_record"])
            self.assertEqual(1, len(ledger.read_all()))
            self.assertTrue(ledger.verify())

    def test_same_event_id_with_different_body_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = RoutingEventLedger(Path(tmp) / "routing-events.jsonl")
            route_for_mirror(
                TaskProfile(task_id="M10", well_defined=True),
                ledger=ledger,
                event_id="evt-conflict",
                created_at="2026-09-15T20:03:00+00:00",
            )
            with self.assertRaises(RoutingLedgerConflict):
                route_for_mirror(
                    TaskProfile(task_id="M10", well_defined=False),
                    ledger=ledger,
                    event_id="evt-conflict",
                    created_at="2026-09-15T20:03:00+00:00",
                )
            self.assertEqual(1, len(ledger.read_all()))
            self.assertTrue(ledger.verify())

    def test_concurrent_process_appends_keep_one_valid_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "routing-events.jsonl")
            context = multiprocessing.get_context("spawn")
            start_event = context.Event()
            result_queue = context.Queue()
            processes = [
                context.Process(
                    target=_process_append_worker,
                    args=(path, f"evt-concurrent-{index}", start_event, result_queue),
                )
                for index in range(6)
            ]
            for process in processes:
                process.start()
            start_event.set()
            for process in processes:
                process.join(10)
                self.assertEqual(0, process.exitcode)
            errors = [result_queue.get(timeout=2) for _ in processes]
            self.assertEqual([None] * len(processes), errors)

            ledger = RoutingEventLedger(path)
            events = ledger.read_all()
            self.assertEqual(6, len(events))
            self.assertEqual(list(range(1, 7)), [event.seq for event in events])
            self.assertTrue(ledger.verify())


if __name__ == "__main__":
    unittest.main()
