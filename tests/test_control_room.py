import tempfile
import unittest
from pathlib import Path

from control_room import ControlRoomStore

BASE = "2d4b383c6723177a3d1ad6ef3774d79dc8e6b7cd"


def order(work_id="HOS-SLICE-MCP-001", baseline=BASE):
    return {
        "work_id": work_id,
        "approval": {"approved_by": "jon", "decision": "APPROVE", "approval_ref": "chat-turn-2026-09-18"},
        "baseline_commit": baseline,
        "objective": "Queue one bounded MCP control slice.",
        "scope": ["control room bridge"],
        "non_goals": ["automatic execution"],
        "allowed_actions": ["queue only"],
        "forbidden_actions": ["merge", "deploy"],
        "acceptance_tests": ["work order is immutable", "stale baseline fails readiness"],
        "rollback": "Delete the feature branch; no canonical data migration.",
        "done_condition": "Tests pass and evidence is preserved.",
        "data_class": "INTERNAL",
        "size_class": "M",
        "risk_class": "R3",
    }


class ControlRoomTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = ControlRoomStore(Path(self.tmp.name) / "control.sqlite3")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_unapproved_request_is_not_exposed(self):
        self.store.queue_local_request("private draft", external_approved=False)
        self.assertIsNone(self.store.next_external_request())

    def test_restricted_request_cannot_be_external(self):
        for value in ("RESTRICTED", "restricted", " restricted "):
            with self.assertRaises(PermissionError):
                self.store.queue_local_request("restricted", data_class=value, external_approved=True)
        with self.assertRaises(ValueError):
            self.store.queue_local_request("unknown", data_class="UNKNOWN", external_approved=True)

    def test_nul_and_oversized_work_lists_fail_closed(self):
        with self.assertRaises(ValueError):
            self.store.queue_local_request("bad\x00text", external_approved=True)
        value = order()
        value["scope"] = ["x"] * 129
        with self.assertRaises(ValueError):
            self.store.submit_work_order(value, current_baseline=BASE)

    def test_nonfinite_work_order_json_is_rejected(self):
        value = order()
        value["budget"] = {"max_cost": float("nan")}
        with self.assertRaises(ValueError):
            self.store.submit_work_order(value, current_baseline=BASE)

    def test_request_response_round_trip_is_digest_bound_and_idempotent(self):
        receipt = self.store.queue_local_request("hello", external_approved=True)
        pending = self.store.next_external_request()
        self.assertEqual("hello", pending["text"])
        with self.assertRaises(PermissionError):
            self.store.append_external_response(pending["request_id"], "0" * 64, "bad")
        first = self.store.append_external_response(pending["request_id"], pending["request_digest"], "world")
        second = self.store.append_external_response(pending["request_id"], pending["request_digest"], "world")
        self.assertEqual("RECORDED", first["state"])
        self.assertEqual("IDEMPOTENT", second["state"])
        self.assertEqual("world", self.store.local_response(receipt["request_id"])["text"])
        self.assertIsNone(self.store.next_external_request())

    def test_conflicting_response_fails_closed(self):
        receipt = self.store.queue_local_request("hello", external_approved=True)
        self.store.append_external_response(receipt["request_id"], receipt["request_digest"], "one")
        with self.assertRaises(RuntimeError):
            self.store.append_external_response(receipt["request_id"], receipt["request_digest"], "two")

    def test_work_order_requires_jon_approval(self):
        value = order()
        value["approval"] = {"approved_by": "worker", "decision": "APPROVE", "approval_ref": "x"}
        with self.assertRaises(PermissionError):
            self.store.submit_work_order(value, current_baseline=BASE)

    def test_work_order_requires_separate_local_approval_and_then_tracks_staleness(self):
        queued = self.store.submit_work_order(order(), current_baseline=BASE)
        self.assertEqual("PENDING_LOCAL_APPROVAL", queued["state"])
        self.assertEqual(
            "PENDING_LOCAL_APPROVAL",
            self.store.work_status("HOS-SLICE-MCP-001", current_baseline=BASE)["state"],
        )
        with self.assertRaises(PermissionError):
            self.store.approve_work_order(
                "HOS-SLICE-MCP-001", "0" * 64,
                approval_ref="local-confirmation", current_baseline=BASE
            )
        approval = self.store.approve_work_order(
            "HOS-SLICE-MCP-001", queued["payload_digest"],
            approval_ref="local-confirmation", current_baseline=BASE
        )
        self.assertEqual("READY", approval["state"])
        self.assertEqual(
            "READY",
            self.store.work_status("HOS-SLICE-MCP-001", current_baseline=BASE)["state"],
        )
        self.assertEqual(
            "STALE",
            self.store.work_status("HOS-SLICE-MCP-001", current_baseline="deadbeef")["state"],
        )
        self.assertEqual(
            "STALE",
            self.store.work_status("HOS-SLICE-MCP-001", current_baseline=BASE)["state"],
        )
        with self.assertRaises(PermissionError):
            self.store.approve_work_order(
                "HOS-SLICE-MCP-001", queued["payload_digest"],
                approval_ref="local-confirmation", current_baseline=BASE
            )

    def test_work_order_same_payload_is_idempotent_conflict_fails(self):
        self.store.submit_work_order(order(), current_baseline=BASE)
        same = self.store.submit_work_order(order(), current_baseline=BASE)
        self.assertEqual("IDEMPOTENT", same["record_state"])
        changed = order()
        changed["objective"] = "different objective"
        with self.assertRaises(RuntimeError):
            self.store.submit_work_order(changed, current_baseline=BASE)

    def test_immutable_rows_cannot_be_edited_directly(self):
        receipt = self.store.queue_local_request("hello", external_approved=False)
        with self.assertRaises(Exception):
            with self.store.db:
                self.store.db.execute(
                    "UPDATE control_requests SET external_approved=1 WHERE request_id=?",
                    (receipt["request_id"],),
                )
        queued = self.store.submit_work_order(order("HOS-SLICE-MCP-IMMUTABLE"), current_baseline=BASE)
        with self.assertRaises(Exception):
            with self.store.db:
                self.store.db.execute(
                    "UPDATE control_work_orders SET payload_digest=? WHERE work_id=?",
                    ("0" * 64, "HOS-SLICE-MCP-IMMUTABLE"),
                )

    def test_database_permissions_are_owner_only_on_posix(self):
        import os
        import stat
        if os.name != "posix":
            self.skipTest("POSIX permissions only")
        mode = stat.S_IMODE(self.store.path.stat().st_mode)
        self.assertEqual(0o600, mode)

    def test_restricted_work_cannot_authorize_external_egress(self):
        value = order()
        value["data_class"] = "RESTRICTED"
        value["allowed_actions"] = ["external friend review"]
        with self.assertRaises(PermissionError):
            self.store.submit_work_order(value, current_baseline=BASE)


if __name__ == "__main__":
    unittest.main()
