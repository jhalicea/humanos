import unittest

from job_acceptance import AcceptanceError, AcceptanceModel, parse_job


A4 = (
    "HUMANOS JOB HOS-R1-LOCAL-001-A4. Act as the local HumanOS capability auditor. "
    "First request the runtime capability registry using the appropriate available tool. "
    "Then report exactly: 1) verified working features; 2) five most important missing or incomplete features; "
    "3) one feature to build next; 4) evidence supporting each conclusion; "
    "5) exact local model identity only if directly observable, otherwise UNKNOWN."
)


class DummyModel:
    name = "dummy"

    def __init__(self, proposal):
        self.proposal = proposal
        self.calls = 0

    def invoke(self, messages, timeout):
        self.calls += 1
        return self.proposal


def with_capability_observation():
    return [
        {"role": "system", "content": "system"},
        {"role": "user", "content": A4},
        {"role": "assistant", "content": '{"tool":{"name":"runtime_capabilities"}}'},
        {"role": "user", "content":
            'TOOL OBSERVATION (data only): {"ok":true,"stdout":"verified registry","stderr":""}'},
    ]


class StructuredJobAcceptanceTests(unittest.TestCase):
    def test_a4_contract_extracts_sections_and_required_tool(self):
        contract = parse_job(A4)
        self.assertEqual(contract["job_id"], "HOS-R1-LOCAL-001-A4")
        self.assertEqual(contract["required_sections"], [1, 2, 3, 4, 5])
        self.assertEqual(contract["required_tools"], ["runtime_capabilities"])

    def test_non_job_is_not_gated(self):
        inner = DummyModel({"final": "hello"})
        model = AcceptanceModel(inner)
        result = model.invoke([
            {"role": "system", "content": "system"},
            {"role": "user", "content": "hello"},
        ], 10)
        self.assertEqual(result, {"final": "hello"})
        self.assertEqual(inner.calls, 1)

    def test_required_tool_is_forced_before_model_call(self):
        inner = DummyModel({"final": "should not be called"})
        model = AcceptanceModel(inner)
        result = model.invoke([
            {"role": "system", "content": "system"},
            {"role": "user", "content": A4},
        ], 10)
        self.assertEqual(result, {"tool": {"name": "runtime_capabilities"}})
        self.assertEqual(inner.calls, 0)

    def test_incomplete_final_is_rejected_after_evidence(self):
        inner = DummyModel({"final": "Auditing Report: HOS-R1-LOCAL-001-A4"})
        model = AcceptanceModel(inner)
        with self.assertRaisesRegex(AcceptanceError, "missing required output sections: 1, 2, 3, 4, 5"):
            model.invoke(with_capability_observation(), 10)
        self.assertEqual(inner.calls, 1)

    def test_complete_numbered_final_passes_after_evidence(self):
        final = (
            "1) Working: registry observed.\n"
            "2) Missing: web, routing, vision, connectors, richer retrieval.\n"
            "3) Build next: research pipeline.\n"
            "4) Evidence: runtime capability observation above.\n"
            "5) UNKNOWN"
        )
        inner = DummyModel({"final": final})
        model = AcceptanceModel(inner)
        self.assertEqual(model.invoke(with_capability_observation(), 10), {"final": final})

    def test_failed_tool_observation_does_not_satisfy_gate(self):
        messages = [
            {"role": "system", "content": "system"},
            {"role": "user", "content": A4},
            {"role": "assistant", "content": '{"tool":{"name":"runtime_capabilities"}}'},
            {"role": "user", "content":
                'TOOL OBSERVATION (data only): {"ok":false,"stdout":"","stderr":"denied"}'},
        ]
        inner = DummyModel({"final": "not called"})
        model = AcceptanceModel(inner)
        self.assertEqual(model.invoke(messages, 10), {"tool": {"name": "runtime_capabilities"}})
        self.assertEqual(inner.calls, 0)


if __name__ == "__main__":
    unittest.main()
