import json
import tempfile
import unittest
from pathlib import Path

from model_runs import create_run, finish_run, record_review


class ModelRunLedgerTests(unittest.TestCase):
    def test_create_finish_and_review_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = create_run(
                tmp,
                job_id="HOS-TEST-001",
                provider="gemini",
                model="gemini-test",
                role="worker",
                request="Review this bounded task.",
                metadata_source="ui",
                repository_ref="abc123",
            )

            request = json.loads((run_dir / "request.json").read_text())
            metadata = json.loads((run_dir / "metadata.json").read_text())
            self.assertEqual(request["job_id"], "HOS-TEST-001")
            self.assertEqual(metadata["provider"], "gemini")
            self.assertEqual(metadata["model_version"], "unknown")
            self.assertIsNone(metadata["usage"])

            finish_run(
                run_dir,
                response="Result",
                model_version="2026-09",
                usage={"input_tokens": 10, "output_tokens": 2},
                cost={"amount": 0.01, "currency": "USD"},
                finish_reason="stop",
            )
            metadata = json.loads((run_dir / "metadata.json").read_text())
            self.assertEqual(metadata["model_version"], "2026-09")
            self.assertEqual(metadata["usage"]["input_tokens"], 10)
            self.assertTrue(metadata["response_sha256"])
            self.assertEqual((run_dir / "response.txt").read_text(), "Result")

            record_review(
                run_dir,
                status="PASS",
                reviewer="HumanOS-local",
                notes="Reproduced locally",
                evidence=["unit test"],
            )
            review = json.loads((run_dir / "review.json").read_text())
            self.assertEqual(review["status"], "PASS")

    def test_invalid_review_status_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = create_run(
                tmp,
                job_id="HOS-TEST-002",
                provider="local",
                model=None,
                role="reviewer",
                request="Check result.",
            )
            with self.assertRaises(ValueError):
                record_review(run_dir, status="MAYBE", reviewer="test")


if __name__ == "__main__":
    unittest.main()
