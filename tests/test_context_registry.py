import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from context_registry import (
    ContextBoundaryError,
    RegistryError,
    assert_workspace_access,
    find_component_conflicts,
    load_registry,
    route_request,
)


class ContextRegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        source = Path(__file__).resolve().parents[1] / "config" / "context_registry.public.json"
        self.public = self.root / "public.json"
        self.public.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def load(self):
        return load_registry(self.public)

    def test_public_registry_loads_and_model_loader_routes_to_existing_stream(self):
        result = route_request(self.load(), "continue the sharded model loader manifest and weight verification work")
        self.assertEqual(result.decision, "CONTINUE")
        self.assertEqual(result.workspace_id, "WS-HUMANOS")
        self.assertEqual(result.workstream_id, "HOS-MAL-001")

    def test_related_inbox_request_extends_existing_stream(self):
        result = route_request(self.load(), "improve the email classifier")
        self.assertEqual(result.decision, "EXTEND")
        self.assertEqual(result.workstream_id, "HOS-INBOX-001")

    def test_explicit_separate_request_preserves_related_candidate(self):
        result = route_request(self.load(), "create a separate browser extension experiment")
        self.assertEqual(result.decision, "CREATE_SEPARATE")
        self.assertEqual(result.workstream_id, "HOS-BROWSER-001")
        self.assertIn("closest related stream", result.reason)

    def test_reconciliation_scoped_topics_preserve_capture_and_recall_routes(self):
        # HOS-ARCH-001 metadata adds legitimate streams, but must not hijack
        # existing exact external turn capture and local recall requests.
        registry = self.load()
        expected = {
            'continue external ChatGPT capture': 'HOS-NB-CAPTURE-001',
            'continue ChatGPT conversation capture': 'HOS-NB-CAPTURE-001',
            'continue life notebook': 'HOS-NB-CAPTURE-001',
            'continue life notebook restart and recall': 'HOS-NB-RECALL-001',
            'continue privacy and notebook hidden records': 'HOS-CTX-004',
        }
        for request, workstream in expected.items():
            with self.subTest(request=request):
                result = route_request(registry, request)
                self.assertEqual(result.decision, 'CONTINUE')
                self.assertEqual(result.workstream_id, workstream)

    def test_reconciliation_named_candidates_remain_discoverable(self):
        # New records remain routable under sufficiently specific descriptions;
        # Foundation questions must not silently route to new architecture docs.
        registry = self.load()
        expected = {
            'continue PRE-LN-1 schema integrity ADR': ('CONTINUE', 'HOS-LN-001'),
            'continue humanos life notebook semantic memory': ('CONTINUE', 'HOS-LN-002'),
            'continue the Control Room MCP boundary': ('CONTINUE', 'HOS-MCP-001'),
            'continue architecture recovery and engineering baseline': ('CONTINUE', 'HOS-ARCH-001'),
            'review Foundation Constitution September 29 conflict': ('EXTEND', 'HOS-FND-001'),
        }
        for request, (decision, workstream) in expected.items():
            with self.subTest(request=request):
                result = route_request(registry, request)
                self.assertEqual(result.decision, decision)
                self.assertEqual(result.workstream_id, workstream)

    def test_native_registry_cli_validation_and_routing_smoke(self):
        # Execute the real public registry CLI on an isolated copy of this
        # branch's fixture, without a private overlay or production paths.
        script = Path(__file__).resolve().parents[1] / "context_registry.py"
        env = os.environ.copy()
        env.pop("HUMANOS_CONTEXT_PRIVATE_REGISTRY", None)

        def run_cli(*args):
            return subprocess.run(
                [sys.executable, str(script), "--registry", str(self.public), *args],
                capture_output=True, text=True, env=env, check=False,
            )

        validated = run_cli("validate")
        self.assertEqual(validated.returncode, 0, validated.stderr)
        self.assertEqual(
            json.loads(validated.stdout),
            {"ok": True, "workspaces": 1, "workstreams": len(self.load().workstreams)},
        )

        cases = {
            "continue external ChatGPT capture": ("CONTINUE", "HOS-NB-CAPTURE-001"),
            "continue life notebook restart and recall": ("CONTINUE", "HOS-NB-RECALL-001"),
            "continue the Control Room MCP boundary": ("CONTINUE", "HOS-MCP-001"),
            "review Foundation Constitution September 29 conflict": ("EXTEND", "HOS-FND-001"),
        }
        for request, (decision, workstream) in cases.items():
            with self.subTest(request=request):
                response = run_cli("route", request)
                self.assertEqual(response.returncode, 0, response.stderr)
                result = json.loads(response.stdout)
                self.assertEqual(result["workspace_id"], "WS-HUMANOS")
                self.assertEqual(result["decision"], decision)
                self.assertEqual(result["workstream_id"], workstream)

    def test_cross_workspace_access_fails_closed_without_explicit_authorization(self):
        data = json.loads(self.public.read_text(encoding="utf-8"))
        data["workspaces"].append({
            "workspace_id": "WS-CLIENT-001",
            "workspace_type": "CLIENT",
            "public_alias": "CLIENT-001",
            "confidentiality": "CLIENT_PRIVATE",
            "repository": None,
            "topics": ["client email"],
            "cross_workspace_policy": "DENY",
        })
        self.public.write_text(json.dumps(data), encoding="utf-8")
        registry = load_registry(self.public)
        with self.assertRaises(ContextBoundaryError):
            assert_workspace_access(registry, "WS-HUMANOS", "WS-CLIENT-001")
        assert_workspace_access(registry, "WS-HUMANOS", "WS-CLIENT-001", explicit_authorization=True)

    def test_private_overlay_adds_private_workspace_without_public_leak(self):
        overlay = self.root / "private.json"
        overlay.write_text(json.dumps({
            "schema_version": 1,
            "workspace_metadata": {
                "WS-CLIENT-001": {
                    "display_name": "Private Client Name",
                    "local_roots": ["/private/client"],
                    "notes": "local only",
                }
            },
            "workspaces": [{
                "workspace_id": "WS-CLIENT-001",
                "workspace_type": "CLIENT",
                "public_alias": "CLIENT-001",
                "confidentiality": "CLIENT_PRIVATE",
                "repository": None,
                "topics": ["email", "automation"],
                "cross_workspace_policy": "DENY",
            }],
            "workstreams": [{
                "workstream_id": "CLI-EMAIL-001",
                "workspace_id": "WS-CLIENT-001",
                "title": "Email Automation",
                "project": "Private Client Work",
                "repository": None,
                "branch": None,
                "work_order": None,
                "status": "READY",
                "confidentiality": "CLIENT_PRIVATE",
                "topics": ["email", "classifier", "automation"],
                "components": [],
                "relations": [],
                "last_verified_commit": None,
                "resume_point": "Private overlay only.",
                "next_action": "Confirm client context before implementation.",
            }],
        }), encoding="utf-8")
        registry = load_registry(self.public, overlay)
        self.assertIn("WS-CLIENT-001", registry.workspaces)
        self.assertEqual(registry.private_metadata["WS-CLIENT-001"]["display_name"], "Private Client Name")
        snapshot = json.dumps(registry.public_snapshot())
        self.assertNotIn("Private Client Name", snapshot)
        self.assertNotIn("/private/client", snapshot)
        self.assertNotIn("CLIENT-001", snapshot)
        self.assertNotIn("CLI-EMAIL-001", snapshot)

    def test_private_overlay_cannot_redefine_public_workspace(self):
        overlay = self.root / "private.json"
        public_workspace = json.loads(self.public.read_text(encoding="utf-8"))["workspaces"][0]
        overlay.write_text(json.dumps({
            "schema_version": 1,
            "workspace_metadata": {},
            "workspaces": [public_workspace],
            "workstreams": [],
        }), encoding="utf-8")
        with self.assertRaisesRegex(RegistryError, "may not redefine public workspaces"):
            load_registry(self.public, overlay)

    def test_ambiguous_workspace_routing_requires_confirmation(self):
        data = json.loads(self.public.read_text(encoding="utf-8"))
        data["workspaces"] = [
            {"workspace_id": "WS-CLIENT-001", "workspace_type": "CLIENT", "public_alias": "CLIENT-001", "confidentiality": "CLIENT_PRIVATE", "repository": None, "topics": ["email"], "cross_workspace_policy": "DENY"},
            {"workspace_id": "WS-CLIENT-002", "workspace_type": "CLIENT", "public_alias": "CLIENT-002", "confidentiality": "CLIENT_PRIVATE", "repository": None, "topics": ["email"], "cross_workspace_policy": "DENY"},
        ]
        data["workstreams"] = []
        self.public.write_text(json.dumps(data), encoding="utf-8")
        routed = route_request(load_registry(self.public), "email")
        self.assertEqual(routed.decision, "AMBIGUOUS")
        self.assertIsNone(routed.workspace_id)

    def test_relation_to_unknown_workstream_is_rejected(self):
        data = json.loads(self.public.read_text(encoding="utf-8"))
        data["workstreams"][0]["relations"].append({"relation": "DEPENDS_ON", "target_workstream_id": "HOS-NOT-REAL"})
        self.public.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(RegistryError, "unknown relation target"):
            load_registry(self.public)

    def test_component_conflict_detects_overlapping_active_streams(self):
        data = json.loads(self.public.read_text(encoding="utf-8"))
        data["workstreams"].append({
            "workstream_id": "HOS-CTX-TEST",
            "workspace_id": "WS-HUMANOS",
            "title": "Overlapping Foundation Test",
            "project": "Foundation",
            "repository": "jhalicea/humanos",
            "branch": "test/overlap",
            "work_order": None,
            "status": "REVIEW",
            "confidentiality": "INTERNAL",
            "topics": ["test"],
            "components": ["docs/foundation/WORKFLOW_STANDARD.md"],
            "relations": [],
            "last_verified_commit": None,
            "resume_point": "Synthetic conflict fixture.",
            "next_action": "None.",
        })
        self.public.write_text(json.dumps(data), encoding="utf-8")
        conflicts = find_component_conflicts(load_registry(self.public), "HOS-CTX-001", ["docs/foundation"])
        self.assertIn("HOS-CTX-TEST", conflicts)

    def test_unknown_request_with_workspace_hint_creates_separate_stream(self):
        result = route_request(self.load(), "quantum gardening telemetry", workspace_hint="WS-HUMANOS")
        self.assertEqual(result.decision, "CREATE_SEPARATE")
        self.assertEqual(result.workspace_id, "WS-HUMANOS")
        self.assertIsNone(result.workstream_id)


if __name__ == "__main__":
    unittest.main()
