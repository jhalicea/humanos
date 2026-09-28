import json
import dataclasses
import unittest

from experiments.ln0_v05_context_boundary import *


class V05BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.core = CoreBoundary()

    def test_positive_local_and_hosted_receive_identical_bytes(self):
        local = self.core.invoke(provider_id="local-fixture", record_ids=["safe-1"])
        packet = self.core.local.calls[-1][0]
        hosted = self.core.invoke(provider_id="hosted-fixture", record_ids=["safe-1"])
        self.assertEqual(packet, self.core.hosted.calls[-1][0]); self.assertEqual(local.kind, hosted.kind)
        self.assertEqual(self.core.brain_digest(), self.core._state_digest)

    def test_s3_hosted_denied_before_call_and_no_disclosure(self):
        with self.assertRaises(PolicyDenied): self.core.invoke(provider_id="hosted-fixture", record_ids=["s3-hostile"])
        self.assertEqual(self.core.hosted.calls, [])
        self.assertNotIn(b"SYNTHETIC_SECRET", repr(self.core.hosted.calls).encode())
        local_packet = self.core.compile_packet(provider_id="local-fixture", record_ids=["s3-hostile"])
        self.assertNotIn(b"SYNTHETIC_SECRET", local_packet)

    def test_empty_retrieval_compiles_no_records(self):
        core = CoreBoundary()
        core.local.next_response = {"schema": REQUEST_SCHEMA, "kind": "context_request", "topics": ["does-not-match"], "reason": "refresh"}
        request = core.invoke(record_ids=["safe-1"])
        core.handle_context_request(request)
        packet = core.local.calls[-1][0]
        self.assertEqual(json.loads(packet)["items"], [])
        for marker in (b"SYNTHETIC_SECRET", b"/private/fixture", b"s3-hostile"):
            self.assertNotIn(marker, packet)

    def test_packet_byte_boundary_unicode_and_cumulative_overflow(self):
        for size in range(16384, 0, -1):
            try:
                candidate = CoreBoundary([{"record_id": "safe", "content": "x" * size, "provenance": "fixture"}]).compile_packet(record_ids=["safe"])
            except BoundaryError:
                continue
            if len(candidate) == MAX_PACKET_BYTES:
                self.assertEqual(len(validate_packet(candidate)), MAX_PACKET_BYTES)
                break
        else:
            self.fail("could not construct exact packet boundary")
        with self.assertRaises(BoundaryError):
            validate_packet(candidate + b"x")
        unicode_packet = CoreBoundary([{"record_id": "safe", "content": "é" * 100, "provenance": "fixture"}]).compile_packet(record_ids=["safe"])
        self.assertIn("é".encode(), unicode_packet)

    def test_nested_secret_markers_and_mutable_source_aliasing(self):
        source = {"record_id": "safe", "content": "ordinary", "provenance": "fixture"}
        core = CoreBoundary([source]); packet = core.compile_packet(record_ids=["safe"]); source["content"] = "SYNTHETIC_SECRET /private"
        self.assertNotIn(b"SYNTHETIC_SECRET", packet); self.assertNotIn(b"/private", packet)

    def test_hostile_provider_output_and_config_fail_closed(self):
        for config in ({"provider_id": "unknown", "timeout_seconds": 1}, {"provider_id": "local-fixture", "timeout_seconds": 0}, {"provider_id": "local-fixture", "timeout_seconds": 1, "endpoint": "x"}, {"provider_id": "local-fixture", "timeout_seconds": 1, "credential": "x"}):
            with self.assertRaises(BoundaryError): validate_invocation_config(config)
        self.core.local.next_response = {"schema": OUTPUT_SCHEMA, "kind": "proposal", "content": "x", "extra": 1}
        with self.assertRaises(BoundaryError): self.core.invoke(record_ids=["safe-1"])

    def test_context_wrapper_event_order_and_second_invocation(self):
        self.core.local.next_response = {"schema": REQUEST_SCHEMA, "kind": "context_request", "topics": ["ordinary"], "reason": "refresh"}
        request = self.core.invoke(record_ids=["safe-1"])
        self.assertEqual((request.trust, request.kind, request.provider_id), ("UNTRUSTED_PROPOSAL", "context_request", "local-fixture"))
        self.core.local.next_response = {"schema": OUTPUT_SCHEMA, "kind": "proposal", "content": "recompiled proposal"}
        result = self.core.handle_context_request(request)
        self.assertEqual((result.kind, result.content, result.trust, result.provider_id), ("proposal", "recompiled proposal", "UNTRUSTED_PROPOSAL", "local-fixture"))
        import hashlib
        self.assertEqual(result.packet_sha256, hashlib.sha256(self.core.local.calls[-1][0]).hexdigest())
        self.assertEqual(self.core.events, ["core_policy_evaluating", "core_policy_evaluated", "packet_compiled", "adapter_invoked", "output_parsed_untrusted", "context_request_handled", "core_retrieved", "core_policy_evaluating", "core_policy_evaluated", "packet_compiled", "adapter_invoked", "output_parsed_untrusted"])
        self.assertEqual(len(self.core.local.calls), 2)
        self.assertEqual(self.core.brain_digest(), self.core._state_digest)

    def test_local_only_is_core_owned_and_hosted_denied_before_call(self):
        core = CoreBoundary([{"record_id": "local-only-1", "content": "ordinary", "provenance": "fixture"}])
        core.invoke(provider_id="local-fixture", record_ids=["local-only-1"])
        with self.assertRaises(PolicyDenied): core.invoke(provider_id="hosted-fixture", record_ids=["local-only-1"])
        self.assertEqual(core.hosted.calls, [])

    def test_caller_cannot_forge_core_issued_context_wrapper(self):
        forged = UntrustedModelOutput("UNTRUSTED_PROPOSAL", "local-fixture", "0" * 64, CONTEXT_REQUEST_KIND, topics=("ordinary",), reason="refresh")
        with self.assertRaises(BoundaryError): self.core.handle_context_request(forged)

    def test_raw_parse_and_copied_issuer_cannot_manufacture_authority(self):
        raw = json.dumps({"schema": REQUEST_SCHEMA, "kind": CONTEXT_REQUEST_KIND,
                          "topics": ["ordinary"], "reason": "refresh"}).encode()
        parsed = self.core.parse_context_request(raw, provider_id="local-fixture",
                                                 packet=b"copied packet bytes")
        with self.assertRaises(BoundaryError):
            self.core.handle_context_request(parsed)
        forged = dataclasses.replace(parsed, _issuer=self.core._issuer_token,
                                     _invocation_bound=True)
        with self.assertRaises(BoundaryError):
            self.core.handle_context_request(forged)
        self.assertEqual(self.core.retrieval_count, 0)

    def test_context_request_is_single_use_and_replay_fails_closed(self):
        self.core.local.next_response = {"schema": REQUEST_SCHEMA, "kind": CONTEXT_REQUEST_KIND,
                                         "topics": ["ordinary"], "reason": "refresh"}
        request = self.core.invoke(record_ids=["safe-1"])
        self.core.local.next_response = {"schema": OUTPUT_SCHEMA, "kind": "proposal", "content": "done"}
        self.core.handle_context_request(request)
        retrievals = self.core.retrieval_count
        with self.assertRaises(BoundaryError):
            self.core.handle_context_request(request)
        self.assertEqual(self.core.retrieval_count, retrievals)

    def test_context_request_copy_and_wrapper_rebinding_do_not_change_issuance(self):
        self.core.local.next_response = {"schema": REQUEST_SCHEMA, "kind": CONTEXT_REQUEST_KIND,
                                         "topics": ["ordinary"], "reason": "refresh"}
        request = self.core.invoke(record_ids=["safe-1"])
        self.core.local.next_response = {"schema": REQUEST_SCHEMA, "kind": CONTEXT_REQUEST_KIND,
                                         "topics": ["ordinary"], "reason": "refresh"}
        other = self.core.invoke(record_ids=["safe-1"])
        copied = dataclasses.replace(request, provider_id="hosted-fixture",
                                     packet_sha256=other.packet_sha256, topics=("hostile",),
                                     _issuer=object(), _invocation_bound=False)
        self.core.local.next_response = {"schema": OUTPUT_SCHEMA, "kind": "proposal", "content": "done"}
        result = self.core.handle_context_request(copied)
        self.assertEqual(result.provider_id, "local-fixture")
        self.assertEqual(self.core.retrieval_count, 1)
        self.assertEqual(self.core.local.calls[-1][1]["provider_id"], "local-fixture")
        with self.assertRaises(BoundaryError): self.core.handle_context_request(request)
        with self.assertRaises(BoundaryError): self.core.handle_context_request(copied)

    def test_context_request_copy_then_original_replay_and_raw_request_have_no_authority(self):
        self.core.local.next_response = {"schema": REQUEST_SCHEMA, "kind": CONTEXT_REQUEST_KIND,
                                         "topics": ["ordinary"], "reason": "refresh"}
        request = self.core.invoke(record_ids=["safe-1"])
        copied = dataclasses.replace(request)
        self.core.local.next_response = {"schema": OUTPUT_SCHEMA, "kind": "proposal", "content": "done"}
        self.core.handle_context_request(copied)
        with self.assertRaises(BoundaryError): self.core.handle_context_request(request)
        raw = json.dumps({"schema": REQUEST_SCHEMA, "kind": CONTEXT_REQUEST_KIND,
                          "topics": ["ordinary"], "reason": "refresh"}).encode()
        parsed = self.core.parse_context_request(raw)
        with self.assertRaises(BoundaryError): self.core.handle_context_request(parsed)

    def test_provider_switch_and_unknown_provider_fail_before_retrieval(self):
        self.core.local.next_response = {"schema": REQUEST_SCHEMA, "kind": CONTEXT_REQUEST_KIND,
                                         "topics": ["ordinary"], "reason": "refresh"}
        local_request = self.core.invoke(record_ids=["safe-1"])
        for provider in ("hosted-fixture", "unknown-provider"):
            with self.assertRaises(BoundaryError):
                self.core.handle_context_request(local_request, provider_id=provider)
            self.assertEqual(self.core.retrieval_count, 0)

    def test_unknown_provider_is_rejected_before_any_record_access(self):
        class AccessTrap(dict):
            def __getitem__(self, key):
                raise AssertionError("record accessed before provider validation")
            def __iter__(self):
                raise AssertionError("records iterated before provider validation")
        self.core._records = AccessTrap(self.core._records)
        with self.assertRaises(BoundaryError):
            self.core.invoke(provider_id="unknown-provider", record_ids=["safe-1"])

    def test_empty_core_and_omitted_selection_remain_empty(self):
        empty = CoreBoundary([])
        self.assertEqual(json.loads(empty.compile_packet(record_ids=[]))["items"], [])
        self.assertEqual(json.loads(empty.compile_packet())["items"], [])
        default = CoreBoundary()
        self.assertEqual(json.loads(default.compile_packet())["items"], [])

    def test_adapter_direct_config_and_provider_mismatch_fail_closed(self):
        packet = self.core.compile_packet(record_ids=[])
        for config in ({"provider_id": "unknown", "timeout_seconds": 1},
                       {"provider_id": "local-fixture", "timeout_seconds": 1, "extra": True},
                       {"provider_id": "hosted-fixture", "timeout_seconds": 1}):
            with self.assertRaises(BoundaryError):
                self.core.local.invoke(packet, config)

    def test_duplicate_packet_items_and_lone_surrogate_fail_closed(self):
        packet = json.loads(self.core.compile_packet(record_ids=["safe-1"]))
        packet["items"].append(dict(packet["items"][0]))
        with self.assertRaises(BoundaryError):
            validate_packet(json.dumps(packet, sort_keys=True, separators=(",", ":")).encode())
        with self.assertRaises(BoundaryError):
            CoreBoundary([{"record_id": "safe", "content": "\ud800", "provenance": "fixture"}])
        self.core.local.next_response = {"schema": REQUEST_SCHEMA, "kind": CONTEXT_REQUEST_KIND,
                                         "topics": ["\ud800"], "reason": "refresh"}
        with self.assertRaises(BoundaryError):
            self.core.invoke(record_ids=[])

    def test_core_classification_denies_adversarial_content_and_recompile(self):
        seed = {"record_id": "seed", "content": "ordinary", "provenance": "fixture"}
        denied = {"record_id": "adversarial", "content": "/private/path credential=SYNTHETIC_SECRET", "provenance": "fixture"}
        core = CoreBoundary([seed, denied], classifications={
            "seed": {"sensitivity": "S1", "provider": "HOSTED_ALLOWED"},
            "adversarial": {"sensitivity": "S1", "provider": "PROVIDER_DENIED"},
        })
        with self.assertRaises(PolicyDenied): core.invoke(provider_id="hosted-fixture", record_ids=["adversarial"])
        self.assertEqual(core.hosted.calls, [])
        core.hosted.next_response = {"schema": REQUEST_SCHEMA, "kind": CONTEXT_REQUEST_KIND, "topics": ["adversarial"], "reason": "refresh"}
        request = core.invoke(provider_id="hosted-fixture", record_ids=["seed"])
        self.assertEqual(len(core.hosted.calls), 1)
        with self.assertRaises(PolicyDenied): core.handle_context_request(request)
        self.assertEqual(len(core.hosted.calls), 1)
        self.assertTrue(all(b"SYNTHETIC_SECRET" not in packet and b"/private/path" not in packet for packet, _ in core.hosted.calls))

    def test_classification_cannot_name_unknown_record(self):
        with self.assertRaises(BoundaryError):
            CoreBoundary([], classifications={"missing": {"sensitivity": "S1", "provider": "PROVIDER_DENIED"}})

    def test_core_explicit_hosted_allowed_does_not_apply_dlp(self):
        values = {"record_id": "allowed", "content": "/private/path credential=SYNTHETIC_SECRET", "provenance": "fixture"}
        core = CoreBoundary([values], classifications={"allowed": {"sensitivity": "S1", "provider": "HOSTED_ALLOWED"}})
        core.invoke(provider_id="hosted-fixture", record_ids=["allowed"])
        self.assertIn(b"SYNTHETIC_SECRET", core.hosted.calls[-1][0])

    def test_hosted_denies_unclassified_custom_record_before_call(self):
        core = CoreBoundary([{"record_id": "ordinary-id", "content": "/private/path credential=SYNTHETIC_SECRET", "provenance": "fixture"}])
        with self.assertRaises(PolicyDenied):
            core.invoke(provider_id="hosted-fixture", record_ids=["ordinary-id"])
        self.assertEqual(core.hosted.calls, [])

    def test_custom_safe_id_cannot_self_upgrade_to_hosted(self):
        core = CoreBoundary([{"record_id": "safe-1", "content": "ordinary", "provenance": "fixture"}])
        with self.assertRaises(PolicyDenied):
            core.invoke(provider_id="hosted-fixture", record_ids=["safe-1"])
        self.assertEqual(core.hosted.calls, [])

    def test_fake_handles_and_capabilities_never_enter_records_or_config(self):
        class FakeDB: pass
        for field, value in (("database", FakeDB()), ("notebook", FakeDB()), ("graph", FakeDB()), ("retrieval", lambda: None), ("capability", object()), ("key", b"secret")):
            with self.assertRaises(BoundaryError): CoreBoundary([{"record_id": "x", "content": "x", "provenance": "p", field: value}])

    def test_cumulative_multi_record_overflow_and_invalid_packet_shape(self):
        core = CoreBoundary([{"record_id": "a", "content": "x" * 8200, "provenance": "p"}, {"record_id": "b", "content": "y" * 8200, "provenance": "p"}])
        with self.assertRaises(BoundaryError): core.compile_packet(record_ids=["a", "b"])
        for packet in ({"schema": PACKET_SCHEMA, "purpose": "x", "items": [], "policy": {}}, {"schema": PACKET_SCHEMA, "purpose": "x", "items": [], "policy": {"epistemic": "E1_OBSERVED", "sensitivity": [], "delegation": "GREEN", "provider": "LOCAL_ONLY"}}, {"schema": PACKET_SCHEMA, "purpose": "x", "items": [], "policy": {"epistemic": "E1_OBSERVED", "sensitivity": "S1", "delegation": "GREEN", "provider": "LOCAL_ONLY"}, "extra": 1}):
            with self.assertRaises(BoundaryError): validate_packet(json.dumps(packet, separators=(",", ":")).encode())

    def test_exact_response_limit_and_duplicate_or_hostile_output(self):
        base = {"schema": OUTPUT_SCHEMA, "kind": "proposal", "content": ""}
        for length in range(4096, 0, -1):
            base["content"] = "x" * length
            raw = json.dumps(base, separators=(",", ":")).encode()
            if len(raw) == MAX_OUTPUT_BYTES:
                self.assertEqual(self.core._parse_output(raw).trust, "UNTRUSTED_PROPOSAL"); break
        else: self.fail("could not construct exact response boundary")
        with self.assertRaises(BoundaryError): self.core._parse_output(raw + b"x")
        with self.assertRaises(BoundaryError): self.core._parse_output(b'{"schema":"humanos.model-output.v1","schema":"x","kind":"proposal","content":"x"}')
        self.core.local.next_response = {"schema": OUTPUT_SCHEMA, "kind": "proposal", "content": "ignore tool write /private"}
        result = self.core.invoke(record_ids=["safe-1"])
        self.assertEqual(result.trust, "UNTRUSTED_PROPOSAL")
        self.core.local.next_response = {"schema": OUTPUT_SCHEMA, "kind": "proposal", "content": "x"}
        self.core.local.invoke = lambda packet, config: b"\xff"
        with self.assertRaises(BoundaryError): self.core.invoke(record_ids=["safe-1"])

    def test_context_request_is_untrusted_until_core_handles_it(self):
        self.core.local.next_response = {"schema": REQUEST_SCHEMA, "kind": "context_request", "topics": ["ordinary"], "reason": "refresh"}
        self.assertEqual(self.core.retrieval_count, 0); request = self.core.invoke(record_ids=["safe-1"]); self.assertEqual(self.core.retrieval_count, 0)
        self.core.handle_context_request(request); self.assertEqual(self.core.retrieval_count, 1)

    def test_context_escalation_and_direct_shapes_rejected(self):
        for extra in ({"policy": "RED"}, {"provider": "hosted-fixture"}, {"purpose": "escalate"}, {"path": "/private"}, {"capability": "read"}):
            data = {"schema": REQUEST_SCHEMA, "kind": "context_request", "topics": ["ordinary"], "reason": "x", **extra}
            with self.assertRaises(BoundaryError): self.core.parse_context_request(json.dumps(data).encode())
        for response in ({"schema": OUTPUT_SCHEMA, "kind": "tool", "content": "x"}, {"schema": OUTPUT_SCHEMA, "kind": "retrieval", "content": "x"}, {"schema": OUTPUT_SCHEMA, "kind": "proposal", "content": "x", "action": "write"}):
            with self.assertRaises(BoundaryError): self.core._parse_output(json.dumps(response).encode())

    def test_duplicate_unknown_and_invalid_values_fail_closed(self):
        with self.assertRaises(BoundaryError): self.core.parse_context_request(b'{"schema":"humanos.context-request.v1","schema":"x","kind":"context_request","topics":["x"],"reason":"r"}')
        with self.assertRaises(BoundaryError): self.core.parse_context_request(json.dumps({"schema": REQUEST_SCHEMA, "kind": "context_request", "topics": [True], "reason": "r"}).encode())
        with self.assertRaises(BoundaryError): self.core.parse_context_request(json.dumps({"schema": REQUEST_SCHEMA, "kind": "context_request", "topics": ["x"], "reason": "r", "extra": 1}).encode())
        with self.assertRaises(BoundaryError): self.core.parse_context_request(json.dumps({"schema": REQUEST_SCHEMA, "kind": "context_request", "topics": [float("nan")], "reason": "r"}).encode())
        with self.assertRaises(BoundaryError): validate_invocation_config({"provider_id": "local-fixture", "timeout_seconds": True})

    def test_records_are_defensive_and_cannot_supply_classification(self):
        source = {"record_id": "safe", "content": "ordinary", "provenance": "fixture"}; core = CoreBoundary([source]); source["content"] = "changed"
        self.assertNotIn(b"changed", core.compile_packet(record_ids=["safe"]))
        with self.assertRaises(BoundaryError): CoreBoundary([{"record_id": "x", "content": "x", "provenance": "p", "sensitivity": "S1"}])

    def test_context_request_recompile_denied_without_second_invocation(self):
        self.core.local.next_response = {"schema": REQUEST_SCHEMA, "kind": "context_request", "topics": ["hostile"], "reason": "refresh"}
        request = self.core.invoke(record_ids=["safe-1"])
        with self.assertRaises(BoundaryError): self.core.handle_context_request(request, provider_id="hosted-fixture")
        self.assertEqual(self.core.hosted.calls, [])
        self.assertEqual(self.core.events, ["core_policy_evaluating", "core_policy_evaluated", "packet_compiled", "adapter_invoked", "output_parsed_untrusted"])
        self.assertNotIn("SYNTHETIC_SECRET", repr(self.core.hosted.calls))


if __name__ == "__main__": unittest.main()
