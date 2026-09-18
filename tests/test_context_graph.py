import sqlite3
import tempfile
import unittest
from pathlib import Path

from context_graph import (
    ContextGraph,
    ContextGraphBoundaryError,
    ContextGraphError,
    stable_entity_id,
)


class ContextGraphTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "context-graph.sqlite3"
        self.graph = ContextGraph(self.path)

    def tearDown(self):
        self.graph.close()
        self.tmp.cleanup()

    def _entity(self, key, *, workspace="WS-HUMANOS", kind="SYSTEM",
                label=None, confidentiality="INTERNAL", provenance_ref=None):
        return self.graph.add_entity(
            workspace_id=workspace,
            entity_type=kind,
            stable_key=key,
            label=label or key,
            confidentiality=confidentiality,
            provenance_kind="OWNER_ASSERTION",
            provenance_ref=provenance_ref or ("owner:" + key.replace(" ", "-")),
        )

    def test_entity_ids_are_deterministic_and_workspace_scoped(self):
        first = stable_entity_id("WS-HUMANOS", "SYSTEM", "humanos")
        second = stable_entity_id("WS-HUMANOS", "SYSTEM", "humanos")
        other = stable_entity_id("WS-PRIVATE", "SYSTEM", "humanos")
        self.assertEqual(first, second)
        self.assertNotEqual(first, other)

    def test_entity_is_idempotent_and_accumulates_provenance(self):
        first = self._entity("humanos", provenance_ref="owner:assertion-1")
        second = self.graph.add_entity(
            workspace_id="WS-HUMANOS",
            entity_type="SYSTEM",
            stable_key="humanos",
            label="humanos",
            confidentiality="INTERNAL",
            provenance_kind="REPOSITORY_EVIDENCE",
            provenance_ref="github:commit:abc123",
        )
        self.assertEqual(first.entity_id, second.entity_id)
        evidence = self.graph.entity_provenance(first.entity_id, "WS-HUMANOS")
        self.assertEqual(
            {(item.provenance_kind, item.provenance_ref) for item in evidence},
            {
                ("OWNER_ASSERTION", "owner:assertion-1"),
                ("REPOSITORY_EVIDENCE", "github:commit:abc123"),
            },
        )

    def test_model_output_cannot_be_canonical_provenance(self):
        with self.assertRaises(ContextGraphError):
            self.graph.add_entity(
                workspace_id="WS-HUMANOS",
                entity_type="SYSTEM",
                stable_key="untrusted",
                label="untrusted",
                confidentiality="INTERNAL",
                provenance_kind="MODEL_OUTPUT",
                provenance_ref="model:claim:1",
            )

    def test_relationships_are_typed_directional_and_provenance_bearing(self):
        owner = self._entity("owner", kind="PERSON", label="Owner")
        system = self._entity("humanos", kind="SYSTEM", label="HumanOS")
        edge = self.graph.add_edge(
            source_entity_id=owner.entity_id,
            relation_type="OWNS",
            target_entity_id=system.entity_id,
            workspace_id="WS-HUMANOS",
            provenance_kind="OWNER_ASSERTION",
            provenance_ref="owner:relationship-1",
        )
        self.assertEqual(
            [item.edge_id for item in self.graph.relationships(
                owner.entity_id, "WS-HUMANOS", direction="outgoing")],
            [edge.edge_id],
        )
        self.assertEqual(
            [item.edge_id for item in self.graph.relationships(
                system.entity_id, "WS-HUMANOS", direction="incoming")],
            [edge.edge_id],
        )
        self.assertEqual(
            self.graph.relationships(system.entity_id, "WS-HUMANOS", direction="outgoing"),
            (),
        )
        evidence = self.graph.edge_provenance(edge.edge_id, "WS-HUMANOS")
        self.assertEqual(evidence[0].provenance_ref, "owner:relationship-1")

    def test_same_edge_can_accumulate_independent_provenance(self):
        left = self._entity("ctx-008", kind="WORKSTREAM", label="CTX-008")
        right = self._entity("ctx-007", kind="WORKSTREAM", label="CTX-007")
        first = self.graph.add_edge(
            source_entity_id=left.entity_id,
            relation_type="EXTENDS",
            target_entity_id=right.entity_id,
            workspace_id="WS-HUMANOS",
            provenance_kind="REGISTRY_EVIDENCE",
            provenance_ref="registry:HOS-CTX-008",
        )
        second = self.graph.add_edge(
            source_entity_id=left.entity_id,
            relation_type="EXTENDS",
            target_entity_id=right.entity_id,
            workspace_id="WS-HUMANOS",
            provenance_kind="REPOSITORY_EVIDENCE",
            provenance_ref="work-order:HOS-CTX-008",
        )
        self.assertEqual(first.edge_id, second.edge_id)
        evidence = self.graph.edge_provenance(first.edge_id, "WS-HUMANOS")
        self.assertEqual(len(evidence), 2)

    def test_cross_workspace_relationship_fails_closed(self):
        left = self._entity("left", workspace="WS-HUMANOS")
        right = self._entity("right", workspace="WS-PRIVATE")
        with self.assertRaises(ContextGraphBoundaryError):
            self.graph.add_edge(
                source_entity_id=left.entity_id,
                relation_type="RELATED_TO",
                target_entity_id=right.entity_id,
                workspace_id="WS-HUMANOS",
                provenance_kind="OWNER_ASSERTION",
                provenance_ref="owner:cross-workspace-attempt",
            )

    def test_mixed_confidentiality_relationship_fails_closed(self):
        left = self._entity("left", confidentiality="INTERNAL")
        right = self._entity("right", confidentiality="PERSONAL_PRIVATE")
        with self.assertRaises(ContextGraphBoundaryError):
            self.graph.add_edge(
                source_entity_id=left.entity_id,
                relation_type="RELATED_TO",
                target_entity_id=right.entity_id,
                workspace_id="WS-HUMANOS",
                provenance_kind="OWNER_ASSERTION",
                provenance_ref="owner:mixed-confidentiality-attempt",
            )

    def test_wrong_workspace_read_is_denied(self):
        entity = self._entity("private-to-workspace")
        with self.assertRaises(ContextGraphBoundaryError):
            self.graph.get_entity(entity.entity_id, "WS-PRIVATE")

    def test_graph_persists_across_reopen(self):
        entity = self._entity("persistent")
        self.graph.close()
        self.graph = ContextGraph(self.path)
        loaded = self.graph.get_entity(entity.entity_id, "WS-HUMANOS")
        self.assertEqual(loaded.label, "persistent")

    def test_canonical_graph_rows_are_append_only(self):
        entity = self._entity("append-only")
        with self.assertRaises(sqlite3.IntegrityError):
            with self.graph.db:
                self.graph.db.execute(
                    "UPDATE context_entities SET label='changed' WHERE entity_id=?",
                    (entity.entity_id,),
                )
        self.assertEqual(
            self.graph.get_entity(entity.entity_id, "WS-HUMANOS").label,
            "append-only",
        )

    def test_unknown_graph_schema_version_fails_closed(self):
        with self.graph.db:
            self.graph.db.execute(
                "UPDATE context_graph_meta SET value='99' WHERE key='schema_version'")
        self.graph.close()
        with self.assertRaises(ContextGraphError):
            ContextGraph(self.path)

    def test_future_schema_is_rejected_before_any_graph_ddl(self):
        future = Path(self.tmp.name) / "future-graph.sqlite3"
        db = sqlite3.connect(future)
        with db:
            db.execute("CREATE TABLE context_graph_meta(key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            db.execute(
                "INSERT INTO context_graph_meta(key,value) VALUES('schema_version','99')")
            db.execute("CREATE TABLE future_only(marker TEXT)")
        db.close()

        with self.assertRaises(ContextGraphError):
            ContextGraph(future)

        db = sqlite3.connect(future)
        try:
            names = {
                row[0] for row in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")
            }
        finally:
            db.close()
        self.assertIn("future_only", names)
        self.assertNotIn("context_entities", names)
        self.assertNotIn("context_edges", names)

    def test_invalid_relation_is_rejected(self):
        left = self._entity("left")
        right = self._entity("right")
        with self.assertRaises(ContextGraphError):
            self.graph.add_edge(
                source_entity_id=left.entity_id,
                relation_type="MODEL_GUESSES",
                target_entity_id=right.entity_id,
                workspace_id="WS-HUMANOS",
                provenance_kind="OWNER_ASSERTION",
                provenance_ref="owner:invalid-relation",
            )


if __name__ == "__main__":
    unittest.main()
