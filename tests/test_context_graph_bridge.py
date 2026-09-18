import tempfile
import unittest
from pathlib import Path

from context_graph import ContextGraph
from context_graph_bridge import (
    RegistryGraphBoundaryError,
    project_public_registry,
    public_registry_snapshot_sha256,
)
from context_registry import (
    ContextRegistry,
    Relation,
    Workspace,
    Workstream,
    load_registry,
)


def _workspace(workspace_id="WS-HUMANOS", confidentiality="INTERNAL"):
    return Workspace(
        workspace_id=workspace_id,
        workspace_type="HUMANOS_INTERNAL",
        public_alias=workspace_id,
        confidentiality=confidentiality,
        repository="jhalicea/humanos",
        topics=("context",),
        cross_workspace_policy="DENY",
    )


def _stream(workstream_id, workspace_id="WS-HUMANOS", *,
            confidentiality="INTERNAL", relations=()):
    return Workstream(
        workstream_id=workstream_id,
        workspace_id=workspace_id,
        title=workstream_id,
        project="Context",
        repository="jhalicea/humanos",
        branch=None,
        work_order=None,
        status="PROMOTED",
        confidentiality=confidentiality,
        topics=("context",),
        components=(),
        relations=tuple(relations),
        last_verified_commit=None,
        resume_point="preserved",
        next_action="none",
    )


def _registry(workspaces, workstreams, *, public_workspaces=None, public_workstreams=None):
    workspace_map = {item.workspace_id: item for item in workspaces}
    stream_map = {item.workstream_id: item for item in workstreams}
    return ContextRegistry(
        workspaces=workspace_map,
        workstreams=stream_map,
        private_metadata={},
        public_workspace_ids=frozenset(
            public_workspaces if public_workspaces is not None else workspace_map),
        public_workstream_ids=frozenset(
            public_workstreams if public_workstreams is not None else stream_map),
    )


class RegistryGraphBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.graph = ContextGraph(Path(self.tmp.name) / "graph.sqlite3")

    def tearDown(self):
        self.graph.close()
        self.tmp.cleanup()

    def test_canonical_public_registry_projects_workspace_workstreams_and_extends(self):
        source = Path(__file__).resolve().parents[1] / "config" / "context_registry.public.json"
        registry = load_registry(source)
        report = project_public_registry(registry, self.graph)

        self.assertEqual(len(report.workspace_entities), len(registry.public_workspace_ids))
        self.assertEqual(len(report.workstream_entities), len(registry.public_workstream_ids))
        self.assertEqual(len(report.membership_edges), len(registry.public_workstream_ids))
        self.assertEqual(len(report.snapshot_sha256), 64)

        entities = dict(report.workstream_entities)
        ctx9 = entities["HOS-CTX-009"]
        ctx8 = entities["HOS-CTX-008"]
        outgoing = self.graph.relationships(ctx9, "WS-HUMANOS")
        extends = [
            edge for edge in outgoing
            if edge.relation_type == "EXTENDS" and edge.target_entity_id == ctx8
        ]
        self.assertEqual(len(extends), 1)
        evidence = self.graph.edge_provenance(extends[0].edge_id, "WS-HUMANOS")
        self.assertEqual(evidence[0].provenance_kind, "REGISTRY_EVIDENCE")
        self.assertIn(report.snapshot_sha256, evidence[0].provenance_ref)

    def test_every_projected_assertion_is_bound_to_snapshot_digest(self):
        registry = _registry(
            [_workspace()],
            [_stream("HOS-A"), _stream(
                "HOS-B", relations=(Relation("EXTENDS", "HOS-A"),))],
        )
        report = project_public_registry(registry, self.graph)
        prefix = "registry:sha256:" + report.snapshot_sha256

        entity_refs = {
            row[0] for row in self.graph.db.execute(
                "SELECT provenance_ref FROM context_entity_provenance")
        }
        edge_refs = {
            row[0] for row in self.graph.db.execute(
                "SELECT provenance_ref FROM context_edge_provenance")
        }
        self.assertTrue(entity_refs)
        self.assertTrue(edge_refs)
        self.assertTrue(all(ref.startswith(prefix) for ref in entity_refs | edge_refs))

    def test_same_projection_is_idempotent(self):
        registry = _registry(
            [_workspace()],
            [_stream("HOS-A"), _stream(
                "HOS-B", relations=(Relation("EXTENDS", "HOS-A"),))],
        )
        first = project_public_registry(registry, self.graph)
        second = project_public_registry(registry, self.graph)
        self.assertEqual(first, second)

        entity_count = self.graph.db.execute(
            "SELECT COUNT(*) FROM context_entities").fetchone()[0]
        edge_count = self.graph.db.execute(
            "SELECT COUNT(*) FROM context_edges").fetchone()[0]
        entity_provenance_count = self.graph.db.execute(
            "SELECT COUNT(*) FROM context_entity_provenance").fetchone()[0]
        edge_provenance_count = self.graph.db.execute(
            "SELECT COUNT(*) FROM context_edge_provenance").fetchone()[0]
        self.assertEqual(entity_count, 3)
        self.assertEqual(edge_count, 3)
        self.assertEqual(entity_provenance_count, 3)
        self.assertEqual(edge_provenance_count, 3)

    def test_private_overlay_only_entities_are_not_projected(self):
        public_ws = _workspace("WS-HUMANOS")
        private_ws = _workspace("WS-PRIVATE", confidentiality="PERSONAL_PRIVATE")
        public_stream = _stream("HOS-PUBLIC")
        private_stream = _stream(
            "HOS-PRIVATE", workspace_id="WS-PRIVATE",
            confidentiality="PERSONAL_PRIVATE")
        registry = _registry(
            [public_ws, private_ws],
            [public_stream, private_stream],
            public_workspaces={"WS-HUMANOS"},
            public_workstreams={"HOS-PUBLIC"},
        )

        report = project_public_registry(registry, self.graph)
        self.assertEqual([item[0] for item in report.workspace_entities], ["WS-HUMANOS"])
        self.assertEqual([item[0] for item in report.workstream_entities], ["HOS-PUBLIC"])
        keys = {
            row[0] for row in self.graph.db.execute(
                "SELECT stable_key FROM context_entities")
        }
        self.assertNotIn("WS-PRIVATE", keys)
        self.assertNotIn("HOS-PRIVATE", keys)

    def test_public_relation_to_nonpublic_target_is_skipped_and_reported(self):
        registry = _registry(
            [_workspace()],
            [
                _stream("HOS-PUBLIC", relations=(Relation("RELATED_TO", "HOS-PRIVATE"),)),
                _stream("HOS-PRIVATE"),
            ],
            public_workstreams={"HOS-PUBLIC"},
        )
        report = project_public_registry(registry, self.graph)
        self.assertEqual(len(report.skipped_relations), 1)
        skipped = report.skipped_relations[0]
        self.assertEqual(skipped.reason, "TARGET_NOT_PUBLIC")
        self.assertEqual(report.relation_edges, ())

    def test_unsupported_registry_relation_is_skipped_not_coerced(self):
        registry = _registry(
            [_workspace()],
            [
                _stream("HOS-A"),
                _stream("HOS-B", relations=(Relation("SUPERSEDES", "HOS-A"),)),
            ],
        )
        report = project_public_registry(registry, self.graph)
        self.assertEqual(len(report.skipped_relations), 1)
        self.assertEqual(
            report.skipped_relations[0].reason,
            "UNSUPPORTED_GRAPH_RELATION",
        )
        relation_types = {
            row[0] for row in self.graph.db.execute(
                "SELECT relation_type FROM context_edges")
        }
        self.assertEqual(relation_types, {"BELONGS_TO"})

    def test_cross_workspace_supported_relation_fails_before_mutation(self):
        registry = _registry(
            [_workspace("WS-A"), _workspace("WS-B")],
            [
                _stream("HOS-A", workspace_id="WS-A",
                        relations=(Relation("EXTENDS", "HOS-B"),)),
                _stream("HOS-B", workspace_id="WS-B"),
            ],
        )
        with self.assertRaises(RegistryGraphBoundaryError):
            project_public_registry(registry, self.graph)
        self.assertEqual(
            self.graph.db.execute("SELECT COUNT(*) FROM context_entities").fetchone()[0],
            0,
        )

    def test_confidentiality_mismatch_fails_before_mutation(self):
        registry = _registry(
            [_workspace(confidentiality="INTERNAL")],
            [_stream("HOS-A", confidentiality="PUBLIC")],
        )
        with self.assertRaises(RegistryGraphBoundaryError):
            project_public_registry(registry, self.graph)
        self.assertEqual(
            self.graph.db.execute("SELECT COUNT(*) FROM context_entities").fetchone()[0],
            0,
        )

    def test_public_snapshot_digest_changes_with_public_registry_content(self):
        first = _registry([_workspace()], [_stream("HOS-A")])
        changed_workspace = Workspace(
            workspace_id="WS-HUMANOS",
            workspace_type="HUMANOS_INTERNAL",
            public_alias="HumanOS Changed",
            confidentiality="INTERNAL",
            repository="jhalicea/humanos",
            topics=("context",),
            cross_workspace_policy="DENY",
        )
        second = _registry([changed_workspace], [_stream("HOS-A")])
        self.assertNotEqual(
            public_registry_snapshot_sha256(first),
            public_registry_snapshot_sha256(second),
        )


if __name__ == "__main__":
    unittest.main()
