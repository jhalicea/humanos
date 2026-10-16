"""Candidate ChatGPT-agent role overlay must reuse existing execution contracts.

This is a *descriptive* registry test, not evidence of a running ChatGPT agent.
"""
import json
from pathlib import Path
import unittest
from execution_contracts import validate_friend_packet, PRIVACY_CLASSES

ROOT = Path(__file__).resolve().parents[1]


class ChatAgentProtocolTests(unittest.TestCase):
    def setUp(self):
        self.roles = json.loads((ROOT / "config/agent_roles.candidate.json").read_text())
        self.packet = json.loads((ROOT / "examples/qa-chat-001-friend-packet.example.json").read_text())

    def test_friend_packet_uses_promoted_schema(self):
        self.assertIs(validate_friend_packet(self.packet), self.packet)
        self.assertEqual(self.packet["privacy_classification"], "PUBLIC")
        self.assertEqual(self.packet["content_authority"], "DATA_ONLY")
        self.assertEqual(self.packet["output_trust"], "PROPOSAL_UNVERIFIED")
        self.assertEqual(self.packet["ownership"], {"mode": "READ_ONLY", "paths": []})

    def test_mirror_is_interface_not_architect(self):
        m = self.roles["mirror"]
        self.assertFalse(m["architect"])
        self.assertFalse(m["worker"])
        self.assertFalse(m["authorization_granted"])

    def test_worker_definitions_never_grant_authority(self):
        self.assertEqual(self.roles["status"], "CANDIDATE_NOT_ADOPTED")
        self.assertEqual(self.roles["authority"], "HUMAN_OWNER")
        role_ids = [x["agent_id"] for x in self.roles["roles"]]
        self.assertEqual(len(role_ids), len(set(role_ids)))
        self.assertIn("QA-CHAT-001", role_ids)
        self.assertIn("ARCH-CHAT-001", role_ids)
        for role in self.roles["roles"]:
            self.assertFalse(role["automatic_authority"])
            self.assertFalse(role["merge"])
            self.assertFalse(role["deploy"])
            self.assertFalse(role["owner_data"])
            self.assertEqual(role["hine_qualification"], "NOT_ASSESSED")

    def test_qualification_is_descriptive_only(self):
        policy = self.roles["policy"]
        self.assertTrue(policy["registry_is_descriptive_only"])
        self.assertFalse(policy["hine_auto_qualifies_agent"])
        self.assertFalse(policy["role_grants_permissions"])
        self.assertFalse(policy["model_choice_grants_permissions"])
        self.assertTrue(policy["external_enforcement_required"])
        self.assertTrue(policy["release_requires_owner"])
        self.assertEqual(policy["approval_state"], "PENDING")

    def test_public_packet_does_not_grant_write_permissions(self):
        data = self.packet
        self.assertEqual(data["work_order_id"], "HOS-AGENTS-CHAT-001")
        self.assertEqual(data["baseline_commit_sha"],
                         "0fe4ea5751bb17be30656a5c95809b79d6718636")
        self.assertNotIn("merge", data["allowed_scope"][0].lower())
        self.assertTrue(any("Merge" in value for value in data["prohibited_actions"]))
        self.assertTrue(any("PRIVATE" not in x for x in data["known_evidence"]))
        self.assertIn(data["privacy_classification"], PRIVACY_CLASSES)


if __name__ == "__main__":
    unittest.main()
