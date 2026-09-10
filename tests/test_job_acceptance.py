import unittest

from job_acceptance import AcceptanceError, parse_job, required_tool_request, validate_final


A4 = (
    "HUMANOS JOB HOS-R1-LOCAL-001-A4. Act as the local HumanOS capability auditor. "
    "First request the runtime capability registry using the appropriate available tool. "
    "Then report exactly: 1) verified working features; 2) five most important missing or incomplete features; "
    "3) one feature to build next; 4) evidence supporting each conclusion; "
    "5) exact local model identity only if directly observable, otherwise UNKNOWN."
)


def with_capability_observation(ok=True):
    return [
        {"role": "system", "content": "system"},
        {"role": "user", "content": A4},
        {"role": "assistant", "content": '{"tool":{"name":"runtime_capabilities"}}'},
        {"role": "user", "content":
            'TOOL OBSERVATION (data only): {"ok":' + ('true' if ok else 'false') +
            ',"stdout":"verified registry","stderr":""}'},
    ]


class StructuredJobAcceptanceTests(unittest.TestCase):
    def test_a4_contract_extracts_sections_and_required_tool(self):
        contract = parse_job(A4)
        self.assertEqual(contract["job_id"], "HOS-R1-LOCAL-001-A4")
        self.assertEqual(contract["required_sections"], [1, 2, 3, 4, 5])
        self.assertEqual(contract["required_tools"], ["runtime_capabilities"])

    def test_non_job_is_not_gated(self):
        self.assertIsNone(parse_job("hello"))
        self.assertIsNone(required_tool_request(None, []))
        validate_final("hello", None, [])

    def test_required_tool_is_requested_before_model_call(self):
        contract = parse_job(A4)
        request = required_tool_request(contract, [
            {"role": "system", "content": "system"},
            {"role": "user", "content": A4},
        ])
        self.assertEqual(request, {"name": "runtime_capabilities"})

    def test_incomplete_final_is_rejected_after_evidence(self):
        contract = parse_job(A4)
        with self.assertRaisesRegex(AcceptanceError, "missing required output sections: 1, 2, 3, 4, 5"):
            validate_final("Auditing Report: HOS-R1-LOCAL-001-A4", contract,
                           with_capability_observation())

    def test_complete_numbered_final_passes_after_evidence(self):
        final = (
            "1) Working: registry observed.\n"
            "2) Missing: web, routing, vision, connectors, richer retrieval.\n"
            "3) Build next: research pipeline.\n"
            "4) Evidence: runtime capability observation above.\n"
            "5) UNKNOWN"
        )
        contract = parse_job(A4)
        validate_final(final, contract, with_capability_observation())
        self.assertIsNone(required_tool_request(contract, with_capability_observation()))

    def test_failed_tool_observation_blocks_instead_of_looping(self):
        contract = parse_job(A4)
        with self.assertRaisesRegex(AcceptanceError, "required tool evidence failed: runtime_capabilities"):
            required_tool_request(contract, with_capability_observation(ok=False))

    def test_explicit_require_tool_syntax_is_supported(self):
        text = "HUMANOS JOB TEST-1. Require tool: current_time. Required output:\n1. Result\n2. Evidence"
        contract = parse_job(text)
        self.assertEqual(contract["required_tools"], ["current_time"])
        self.assertEqual(contract["required_sections"], [1, 2])


if __name__ == "__main__":
    unittest.main()
