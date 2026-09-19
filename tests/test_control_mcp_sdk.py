import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from mcp import Client

import control_mcp_server
from control_room import ControlRoomStore


class ControlMCPIntegrationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "control.sqlite3"
        self.old_db = os.environ.get("HUMANOS_CONTROL_DB")
        self.old_root = os.environ.get("HUMANOS_REPO_ROOT")
        os.environ["HUMANOS_CONTROL_DB"] = str(self.db_path)
        os.environ["HUMANOS_REPO_ROOT"] = str(Path(__file__).resolve().parents[1])

    def tearDown(self):
        if self.old_db is None:
            os.environ.pop("HUMANOS_CONTROL_DB", None)
        else:
            os.environ["HUMANOS_CONTROL_DB"] = self.old_db
        if self.old_root is None:
            os.environ.pop("HUMANOS_REPO_ROOT", None)
        else:
            os.environ["HUMANOS_REPO_ROOT"] = self.old_root
        self.tmp.cleanup()

    def _head(self):
        return subprocess.run(
            ["git", "-C", os.environ["HUMANOS_REPO_ROOT"], "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip().lower()

    async def test_in_process_mcp_request_reply_round_trip(self):
        store = ControlRoomStore(self.db_path)
        receipt = store.queue_local_request("hello from local HumanOS", external_approved=True)
        store.close()

        async with Client(control_mcp_server.mcp) as client:
            pending = await client.call_tool("humanos_control_next_request", {})
            self.assertEqual("PENDING", pending.structured_content["state"])
            request = pending.structured_content["request"]
            self.assertEqual(receipt["request_id"], request["request_id"])

            reply = await client.call_tool(
                "humanos_control_reply",
                {
                    "request_id": request["request_id"],
                    "request_digest": request["request_digest"],
                    "text": "hello from ChatGPT side",
                },
            )
            self.assertEqual("RECORDED", reply.structured_content["state"])

        store = ControlRoomStore(self.db_path)
        self.assertEqual(
            "hello from ChatGPT side",
            store.local_response(receipt["request_id"])["text"],
        )
        store.close()

    async def test_mcp_work_order_cannot_self_approve(self):
        head = self._head()
        work_order = {
            "work_id": "HOS-SLICE-MCP-SDK-001",
            "approval": {
                "approved_by": "jon",
                "decision": "APPROVE",
                "approval_ref": "integration-test",
            },
            "baseline_commit": head,
            "objective": "Exercise MCP work-order intake.",
            "scope": ["record immutable work order"],
            "non_goals": ["execute work"],
            "allowed_actions": ["queue only"],
            "forbidden_actions": ["merge", "deploy", "shell"],
            "acceptance_tests": ["MCP cannot make itself READY"],
            "rollback": "Delete isolated test database.",
            "done_condition": "Work order remains pending until local approval.",
            "data_class": "INTERNAL",
            "size_class": "S",
            "risk_class": "R3",
        }

        async with Client(control_mcp_server.mcp) as client:
            result = await client.call_tool(
                "humanos_control_submit_work_order", {"work_order": work_order}
            )
            self.assertEqual("PENDING_LOCAL_APPROVAL", result.structured_content["state"])
            digest = result.structured_content["payload_digest"]
            status = await client.call_tool(
                "humanos_control_work_status", {"work_id": work_order["work_id"]}
            )
            self.assertEqual("PENDING_LOCAL_APPROVAL", status.structured_content["state"])
            self.assertEqual(head, status.structured_content["baseline_commit"])

        store = ControlRoomStore(self.db_path)
        store.approve_work_order(
            work_order["work_id"], digest,
            approval_ref="local-test-owner", current_baseline=head,
        )
        self.assertEqual(
            "READY",
            store.work_status(work_order["work_id"], current_baseline=head)["state"],
        )
        store.close()


if __name__ == "__main__":
    unittest.main()
