"""Cross-V tests for the TEST-ONLY REFERENCE COMPOSITION HARNESS.

These tests are separate composition qualification evidence. They do not modify or
relabel accepted V-01 through V-05 fixture/test evidence and do not exercise Runtime
0.1 or owner Notebook data.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from experiments.ln0_composition_harness import (
    CompositionDenied,
    CompiledPacket,
    ContextCore,
    IngestionConflict,
    KernelCheckpointBoundary,
    KernelStore,
    RecoveryRequired,
    StalePacket,
    migrated_legacy_event,
    sqlcipher_seal_snapshot,
)


class LN0CrossVCompositionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="ln0-composition-")
        self.root = Path(self.tmp.name)
        self.path = self.root / "governed.sqlite"
        self.checkpoint = KernelCheckpointBoundary(b"synthetic-test-erasure-secret-32")
        self.store = KernelStore(self.path, checkpoint=self.checkpoint)
        self.core = ContextCore(self.store)

    def tearDown(self):
        self.tmp.cleanup()

    def seed(self):
        # V-01 identity mapping is reused through its accepted deterministic helper;
        # both source rows have equal content but distinct legacy keys/identities.
        legacy_a = migrated_legacy_event("legacy-row-A", "duplicate legacy text")
        legacy_b = migrated_legacy_event("legacy-row-B", "duplicate legacy text")
        mapped_a = self.store.import_legacy(legacy_a, capability=self.store.migration_capability)
        mapped_b = self.store.import_legacy(legacy_b, capability=self.store.migration_capability)
        source_claims = {"provider": "HOSTED_ALLOWED", "privacy": "STANDARD",
                         "classification": "PUBLIC"}
        target = self.store.ingest("connector-token", "ingest-target", b"Jon", claims=source_claims,
                                   provenance="authenticated connector")
        survivor = self.store.ingest("connector-token", "ingest-survivor", b"still authorized evidence", claims=source_claims,
                                     provenance="authenticated connector")
        denied = self.store.ingest("connector-token", "ingest-local", b"private Brain-like content", claims=source_claims,
                                   provenance="authenticated connector")
        claimed = self.store.ingest("connector-token", "ingest-claim", b"source claim", claims={"source_authority": "OWNER"},
                                    provenance="untrusted connector")
        # The source claims above do not set provider/privacy policy. Core grants only
        # the two records deliberately selected for hosted use.
        self.core.authorize_hosted(target[0])
        self.core.authorize_hosted(survivor[0])
        return mapped_a, mapped_b, target, survivor, denied, claimed

    def test_cross_v_lifecycle_shared_store_stale_context_erasure_and_restore(self):
        legacy_a, legacy_b, target, survivor, denied, claimed = self.seed()
        self.assertNotEqual(legacy_a, legacy_b)
        self.assertNotEqual(legacy_a[0], legacy_b[0])
        self.assertEqual(self.store.read_payload(legacy_a[0]), b"duplicate legacy text")
        self.assertEqual(self.store.read_payload(legacy_b[0]), b"duplicate legacy text")
        self.assertEqual(self.store.read_event(legacy_a[0])[2], "LEGACY_EVIDENCE")
        self.assertEqual(self.store.read_event(legacy_b[0])[2], "LEGACY_EVIDENCE")
        self.assertEqual(self.store.list_events()[0]["provider"], "PROVIDER_DENIED")
        self.assertEqual(self.store.list_events()[0]["privacy"], "UNCLASSIFIED")

        # V-03 idempotent retry and conflict behavior survive the shared-store seam.
        retry = self.store.ingest("connector-token", "ingest-target", b"Jon",
                                  claims={"provider": "HOSTED_ALLOWED", "privacy": "STANDARD",
                                          "classification": "PUBLIC"},
                                  provenance="authenticated connector")
        self.assertEqual(retry, target)
        with self.assertRaises(IngestionConflict):
            self.store.ingest("connector-token", "ingest-target", b"different",
                              claims={"provider": "HOSTED_ALLOWED", "privacy": "STANDARD",
                                      "classification": "PUBLIC"},
                              provenance="authenticated connector")
        self.assertEqual(self.store.read_event(claimed[0])[2], "OBSERVED_EVIDENCE")
        self.assertNotEqual(self.store.read_event(claimed[0])[2], "OWNER")

        # Every derivative is in the same store and linked to authoritative IDs.
        self.store.add_derivative("cache-embedded", [target[0]], b"PREFIX-Jon-SUFFIX")
        self.store.add_derivative("multi-source", [target[0], survivor[0]], b"Jon + still authorized evidence")
        self.store.add_derivative("local-cache", [denied[0]], b"private Brain-like content")
        old_packet = self.core.compile_packet([target[0], survivor[0]])
        old_payload = old_packet.payload
        decoded = json.loads(old_payload)
        self.assertEqual({item["event_id"] for item in decoded["items"]}, {target[0], survivor[0]})
        self.assertNotIn(denied[0], {item["event_id"] for item in decoded["items"]})
        self.assertEqual(self.core.adapter.calls, [])  # compiled but deliberately not dispatched

        # A backup predating ERASE contains governed bytes but remains quarantined on restore.
        backup = self.root / "pre-erase-backup.sqlite"
        self.store.backup_to(backup)

        self.assertFalse(self.store.request_erase(target[0], token="owner-token", interrupt_after_tombstone=True))
        self.assertEqual(self.store.erase_state(target[0]), "ERASING")
        with self.assertRaises(CompositionDenied):
            self.store.authorized_retrieval([target[0]], "hosted-fixture")

        # Simulated restart: V-04 checkpoint plus the one shared governed DB recovers.
        restarted = KernelStore(self.path, checkpoint=self.checkpoint,
                                core_authority=self.core.policy_authority)
        self.core.store = restarted
        restarted.replay_or_recover()
        self.assertEqual(restarted.erase_state(target[0]), "ERASED")
        self.assertEqual(restarted.ingest("connector-token", "ingest-survivor", b"still authorized evidence",
                                          claims={"provider": "HOSTED_ALLOWED", "privacy": "STANDARD",
                                                  "classification": "PUBLIC"},
                                          provenance="authenticated connector"), survivor)

        # Owner decision: a compiled, not-yet-sent packet is revoked at dispatch.
        with self.assertRaises(StalePacket):
            self.core.dispatch(old_packet, "hosted-fixture")
        self.assertEqual(self.core.adapter.calls, [])
        with restarted._connect() as db:
            purged = db.execute("SELECT body,state FROM derivatives WHERE derivative_id=?", (old_packet.packet_id,)).fetchone()
        self.assertEqual(purged, (None, "REVOKED"))
        with self.assertRaises(CompositionDenied):
            restarted.read_payload(target[0])
        self.assertTrue(restarted.verify_chain())
        self.assertFalse(restarted.scan_bytes([b"Jon", hashlib.sha256(b"Jon").hexdigest().encode()]))
        self.assertEqual(restarted.read_event(target[0])[0], target[0])
        with restarted._connect() as db:
            deletion = db.execute("SELECT event_id,payload_object_id,state FROM tombstones").fetchone()
            receipt = db.execute("SELECT event_id,payload_object_id,state FROM deletion_receipts").fetchone()
            mixed = db.execute("SELECT lineage,body,state FROM derivatives WHERE kind='multi-source'").fetchone()
        self.assertEqual(deletion, (target[0], target[1], "ERASED"))
        self.assertEqual(receipt, (target[0], target[1], "ERASED"))
        self.assertNotIn(target[0], json.loads(mixed[0]))
        self.assertIn(survivor[0], json.loads(mixed[0]))
        self.assertIn(b"still authorized evidence", mixed[1])

        # Pre-erase backup must not become LIVE before tombstone/deletion replay.
        restored = KernelStore.restore_from(backup, self.root / "restored.sqlite", self.checkpoint,
                                            self.core.policy_authority)
        with self.assertRaises(RecoveryRequired) as restore_error:
            restored.read_payload(target[0])
        self.assertIn("RESTORE_NOT_READY", str(restore_error.exception))
        restored.replay_or_recover()
        self.assertEqual(restored.erase_state(target[0]), "ERASED")
        self.assertTrue(restored.verify_chain())
        self.assertFalse(restored.scan_bytes([b"Jon", hashlib.sha256(b"Jon").hexdigest().encode()]))
        with restored._connect() as db:
            restored_packet = db.execute("SELECT body,state FROM derivatives WHERE derivative_id=?", (old_packet.packet_id,)).fetchone()
        self.assertEqual(restored_packet[1], "LIVE")
        self.assertNotIn(b"Jon", restored_packet[0])
        self.assertIn(b"still authorized evidence", restored_packet[0])

        # CoreRequest cannot retrieve erased or provider-denied sources; a new packet
        # from current state can still use the unaffected authorized event.
        before = len(self.core.adapter.calls)
        erase_request = self.core.issue_context_request("hosted-fixture", [target[0]])
        with self.assertRaises(CompositionDenied):
            self.core.handle_context_request(erase_request)
        denied_request = self.core.issue_context_request("hosted-fixture", [denied[0]])
        with self.assertRaises(CompositionDenied):
            self.core.handle_context_request(denied_request)
        self.assertEqual(len(self.core.adapter.calls), before)
        fresh = self.core.compile_packet([survivor[0]])
        self.core.dispatch(fresh, "hosted-fixture")
        self.assertEqual(len(self.core.adapter.calls), before + 1)
        self.assertIn(b"still authorized evidence", self.core.adapter.calls[-1][0])
        self.assertNotIn(b"Jon", self.core.adapter.calls[-1][0])
        with self.assertRaises(StalePacket):
            self.core.dispatch(fresh, "hosted-fixture")

        # SQLCipher encrypts the serialized current KernelStore state separately;
        # this is a CLI snapshot proof, not an in-process production binding.
        serialized = restarted.serialized_state()
        sealed = sqlcipher_seal_snapshot(serialized, self.root / "sealed-kernel-snapshot.db")
        self.assertTrue(sealed["create_readback"])
        self.assertTrue(sealed["wrong_key_rejected"])
        self.assertTrue(sealed["no_key_rejected"])
        self.assertTrue(sealed["standard_sqlite_rejected"])
        encrypted = Path(sealed["encrypted_db_path"]).read_bytes()
        self.assertNotIn(b"still authorized evidence", encrypted)

    def test_old_packet_rejected_when_provider_or_privacy_authority_changes(self):
        _, _, target, _, _, _ = self.seed()
        packet = self.core.compile_packet([target[0]])
        self.core.set_provider_permission(target[0], "PROVIDER_DENIED")
        with self.assertRaises(StalePacket):
            self.core.dispatch(packet, "hosted-fixture")
        self.assertEqual(self.core.adapter.calls, [])
        self.assertTrue(self.store.verify_chain())

        self.core.authorize_hosted(target[0])
        packet = self.core.compile_packet([target[0]])
        self.core.set_privacy_classification(target[0], "PRIVATE")
        with self.assertRaises(StalePacket):
            self.core.dispatch(packet, "hosted-fixture")
        self.assertEqual(self.core.adapter.calls, [])
        self.assertTrue(self.store.verify_chain())

    def test_migration_capability_and_owner_erase_authority_fail_closed(self):
        legacy = migrated_legacy_event("legacy-auth", "safe synthetic")
        with self.assertRaises(CompositionDenied):
            self.store.import_legacy(legacy, capability=object())
        _, _, target, _, _, claimed = self.seed()
        with self.assertRaises(CompositionDenied):
            self.store.request_erase(target[0], token="connector-token")
        with self.assertRaises(CompositionDenied):
            self.store.request_erase(claimed[0], token="unknown")

    def test_connector_claims_cannot_authorize_or_classify_for_hosting(self):
        record, _ = self.store.ingest(
            "connector-token", "connector-self-authorize", b"synthetic credential-like text",
            claims={"provider": "HOSTED_ALLOWED", "privacy": "STANDARD",
                    "classification": "PUBLIC", "source_authority": "OWNER"},
            provenance="untrusted connector")
        with self.assertRaises(CompositionDenied):
            self.core.compile_packet([record])
        self.assertEqual(self.core.adapter.calls, [])
        state = next(item for item in self.store.list_events() if item["event_id"] == record)
        self.assertEqual(state["provider"], "PROVIDER_DENIED")
        self.assertEqual(state["privacy"], "UNCLASSIFIED")
        self.assertEqual(state["authority"], "OBSERVED_EVIDENCE")

    def test_migration_hosted_claim_is_not_authorization_and_core_grant_is(self):
        legacy = migrated_legacy_event("legacy-hosted-claim", "synthetic migrated evidence")
        legacy = type(legacy)(legacy.event_id, legacy.payload_object_id, legacy.payload,
                             legacy.provenance, provider="HOSTED_ALLOWED")
        event_id, _ = self.store.import_legacy(legacy, capability=self.store.migration_capability)
        with self.assertRaises(CompositionDenied):
            self.core.compile_packet([event_id])
        self.assertEqual(self.core.adapter.calls, [])

        self.core.authorize_hosted(event_id)
        packet = self.core.compile_packet([event_id])
        self.core.dispatch(packet, "hosted-fixture")
        self.assertEqual(len(self.core.adapter.calls), 1)

    def test_lineage_drives_transformed_derivative_fanout(self):
        erased, _ = self.store.ingest("connector-token", "lineage-erased", b"low entropy secret",
                                      claims={}, provenance="synthetic")
        survivor, _ = self.store.ingest("connector-token", "lineage-survivor", b"surviving source",
                                        claims={}, provenance="synthetic")
        sole = self.store.add_derivative("transformed-sole", [erased], b"abstract transformed summary")
        multi = self.store.add_derivative("transformed-multi", [erased, survivor], b"combined abstract summary")

        self.assertTrue(self.store.request_erase(erased, token="owner-token"))
        with self.store._connect() as db:
            sole_state = db.execute("SELECT body,state FROM derivatives WHERE derivative_id=?", (sole,)).fetchone()
            multi_row = db.execute("SELECT lineage,body,state FROM derivatives WHERE derivative_id=?", (multi,)).fetchone()
        self.assertEqual(sole_state, (None, "INVALIDATED"))
        self.assertEqual(json.loads(multi_row[0]), [survivor])
        self.assertEqual(multi_row[1], b"surviving source")
        self.assertEqual(multi_row[2], "LIVE")
        self.assertTrue(self.store.verify_chain())

    def test_unidentified_exact_duplicate_payload_is_not_exempt(self):
        erased, _ = self.store.ingest("connector-token", "duplicate-erased", b"low entropy secret",
                                      claims={}, provenance="synthetic")
        duplicate, _ = self.store.ingest(
            "connector-token", "duplicate-unidentified", b"low entropy secret",
            claims={"independent_source_authorized": True},
            provenance="core authorized independent source")
        self.assertNotEqual(erased, duplicate)
        with self.assertRaises(RecoveryRequired):
            self.store.request_erase(erased, token="owner-token")
        self.assertEqual(self.store.erase_state(erased), "ERASING")

    def test_core_named_independent_exact_payload_cell_may_survive(self):
        erased, _ = self.store.ingest("connector-token", "authorized-erased", b"low entropy secret",
                                      claims={}, provenance="synthetic")
        independent, _ = self.store.ingest("connector-token", "authorized-independent", b"low entropy secret",
                                           claims={}, provenance="untrusted source claim")
        self.core.authorize_independent_source_exemption(independent)
        self.assertTrue(self.store.request_erase(erased, token="owner-token"))
        self.assertEqual(self.store.read_payload(independent), b"low entropy secret")

    def test_core_named_independent_embedded_copy_is_not_exempt(self):
        erased, _ = self.store.ingest("connector-token", "embedded-erased", b"low entropy secret",
                                      claims={}, provenance="synthetic")
        independent, _ = self.store.ingest(
            "connector-token", "embedded-independent", b"PREFIX-low entropy secret-SUFFIX",
            claims={}, provenance="synthetic")
        self.core.authorize_independent_source_exemption(independent)
        with self.assertRaises(RecoveryRequired):
            self.store.request_erase(erased, token="owner-token")
        self.assertEqual(self.store.erase_state(erased), "ERASING")

    def test_unlineaged_erased_bytes_fail_closed_even_after_lineage_fanout(self):
        erased, _ = self.store.ingest("connector-token", "unlineaged-erased", b"secret",
                                      claims={}, provenance="synthetic")
        survivor, _ = self.store.ingest("connector-token", "unlineaged-survivor", b"survivor",
                                        claims={}, provenance="synthetic")
        self.store.add_derivative("transformed-multi", [erased, survivor], b"opaque summary")
        self.store.add_derivative("unlineaged-leak", [survivor], b"prefix-secret-suffix")

        with self.assertRaises(RecoveryRequired):
            self.store.request_erase(erased, token="owner-token")
        self.assertEqual(self.store.erase_state(erased), "ERASING")
        self.assertEqual(self.core.adapter.calls, [])

    def test_all_store_scan_covers_auxiliary_content_field(self):
        erased, _ = self.store.ingest("connector-token", "aux-leak-erased", b"secret",
                                      claims={}, provenance="synthetic")
        self.store.put_auxiliary_content("model-cache", b"PREFIX-secret-SUFFIX")
        with self.assertRaises(RecoveryRequired):
            self.store.request_erase(erased, token="owner-token")
        self.assertEqual(self.store.erase_state(erased), "ERASING")

    def test_restore_rechecks_erased_receipt_and_stays_quarantined_on_resurrection(self):
        erased, _ = self.store.ingest("connector-token", "restore-resurrection", b"replay secret",
                                      claims={}, provenance="synthetic")
        self.assertTrue(self.store.request_erase(erased, token="owner-token"))
        backup = self.root / "post-erase-with-receipt.sqlite"
        self.store.backup_to(backup)
        with sqlite3.connect(backup) as db:
            receipt = db.execute("SELECT state FROM deletion_receipts").fetchone()
            self.assertEqual(receipt, ("ERASED",))
            db.execute("INSERT INTO auxiliary_content VALUES(?,?)",
                       ("tampered-cache", b"prefix-replay secret-suffix"))

        restored = KernelStore.restore_from(backup, self.root / "resurrected.sqlite", self.checkpoint,
                                            self.core.policy_authority)
        with self.assertRaises(RecoveryRequired):
            restored.read_payload(erased)
        with self.assertRaises(RecoveryRequired):
            restored.replay_or_recover()
        self.assertEqual(restored._get_meta("restore_state"), "RESTORING")
        with self.assertRaises(RecoveryRequired):
            restored.read_event(erased)

        restored.remove_auxiliary_content_during_recovery("tampered-cache")
        restored.replay_or_recover()
        self.assertEqual(restored._get_meta("restore_state"), "LIVE")
        self.assertEqual(restored.unresolved_count(), 0)
        with self.assertRaises(CompositionDenied):
            restored.read_payload(erased)
        self.assertTrue(restored.verify_chain())

    def test_packet_issuer_provider_one_shot_and_expiry_are_core_checked(self):
        _, _, target, _, _, _ = self.seed()
        packet = self.core.compile_packet([target[0]])
        forged = CompiledPacket(packet.packet_id, packet.payload, packet.provider_id,
                                packet.lease, object())
        with self.assertRaises(CompositionDenied):
            self.core.dispatch(forged, "hosted-fixture")
        with self.assertRaises(StalePacket):
            self.core.dispatch(packet, "local-fixture")
        self.assertEqual(self.core.adapter.calls, [])

        fresh = self.core.compile_packet([target[0]])
        self.core.dispatch(fresh, "hosted-fixture")
        self.assertEqual(len(self.core.adapter.calls), 1)
        with self.assertRaises(StalePacket):
            self.core.dispatch(fresh, "hosted-fixture")
        self.assertEqual(len(self.core.adapter.calls), 1)

        expiring_core = ContextCore(self.store, lease_seconds=0)
        expired = expiring_core.compile_packet([target[0]])
        with self.assertRaises(StalePacket):
            expiring_core.dispatch(expired, "hosted-fixture")
        self.assertEqual(expiring_core.adapter.calls, [])

    def test_context_request_is_single_use_and_provider_bound(self):
        _, _, _target, survivor, _denied, _claimed = self.seed()
        request = self.core.issue_context_request("hosted-fixture", [survivor[0]])
        with self.assertRaises(CompositionDenied):
            self.core.handle_context_request(request, "local-fixture")
        valid = self.core.issue_context_request("hosted-fixture", [survivor[0]])
        self.core.handle_context_request(valid)
        self.assertEqual(len(self.core.adapter.calls), 1)
        with self.assertRaises(CompositionDenied):
            self.core.handle_context_request(valid)
        self.assertEqual(len(self.core.adapter.calls), 1)

    def test_sqlcipher_snapshot_scans_serialized_kernel_state(self):
        *_, target, survivor, _denied, _claimed = self.seed()
        self.store.request_erase(target[0], token="owner-token")
        serialized = self.store.serialized_state()
        sealed = sqlcipher_seal_snapshot(serialized, self.root / "sealed-snapshot.db")
        db_bytes = Path(sealed["encrypted_db_path"]).read_bytes()
        self.assertNotIn(b"Jon", db_bytes)
        self.assertNotIn(hashlib.sha256(b"Jon").hexdigest().encode(), db_bytes)
        self.assertTrue(self.store.read_payload(survivor[0]))


if __name__ == "__main__":
    unittest.main()
