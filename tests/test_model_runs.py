import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from model_runs import create_run, finish_run, inspect_run, record_review


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
            self.assertEqual(metadata["state"], "CREATED")
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
            self.assertEqual(metadata["state"], "RESPONDED")
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
            metadata = json.loads((run_dir / "metadata.json").read_text())
            self.assertEqual(review["status"], "PASS")
            self.assertEqual(review["bound_response_sha256"], metadata["response_sha256"])
            self.assertEqual(metadata["state"], "REVIEWED")
            self.assertEqual(inspect_run(run_dir)["integrity"], "PASS")

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

    def test_job_id_traversal_is_rejected_before_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "ledger"
            outside = Path(tmp) / "escape"
            with self.assertRaises(ValueError):
                create_run(
                    root,
                    job_id="../../../escape",
                    provider="test",
                    model="unknown",
                    role="worker",
                    request="x",
                )
            self.assertFalse(outside.exists())

    def test_extra_metadata_is_namespaced_and_cannot_clobber_truth(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = create_run(
                tmp,
                job_id="HOS-TEST-EXTRA",
                provider="trusted-provider",
                model="trusted-model",
                role="worker",
                request="x",
                extra_metadata={"provider": "forged", "response_sha256": "forged", "tag": "research"},
            )
            metadata = json.loads((run_dir / "metadata.json").read_text())
            self.assertEqual(metadata["provider"], "trusted-provider")
            self.assertIsNone(metadata["response_sha256"])
            self.assertEqual(metadata["extra"]["provider"], "forged")
            self.assertEqual(metadata["extra"]["response_sha256"], "forged")
            self.assertEqual(metadata["extra"]["tag"], "research")

    def test_permissions_are_owner_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = create_run(
                tmp,
                job_id="HOS-TEST-MODE",
                provider="test",
                model="unknown",
                role="worker",
                request="private request",
            )
            finish_run(run_dir, response="private response")
            record_review(run_dir, status="PASS", reviewer="test")
            self.assertEqual(stat.S_IMODE(os.stat(run_dir).st_mode), 0o700)
            for name in ("request.json", "metadata.json", "response.txt", "review.json"):
                self.assertEqual(stat.S_IMODE(os.stat(run_dir / name).st_mode), 0o600)

    def test_second_finish_cannot_overwrite_response(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = create_run(
                tmp,
                job_id="HOS-TEST-IMMUTABLE",
                provider="test",
                model="unknown",
                role="worker",
                request="x",
            )
            finish_run(run_dir, response="first")
            with self.assertRaises(ValueError):
                finish_run(run_dir, response="second")
            self.assertEqual((run_dir / "response.txt").read_text(), "first")

    def test_review_detects_response_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = create_run(
                tmp,
                job_id="HOS-TEST-BIND",
                provider="test",
                model="unknown",
                role="reviewer",
                request="x",
            )
            finish_run(run_dir, response="original")
            record_review(run_dir, status="PASS", reviewer="test")
            (run_dir / "response.txt").write_text("mutated", encoding="utf-8")
            state = inspect_run(run_dir)
            self.assertEqual(state["state"], "INTEGRITY_ERROR")
            self.assertEqual(state["integrity"], "FAIL")
            self.assertEqual(state["error"], "response digest mismatch")

    def test_partial_response_write_is_classified_not_mistaken_for_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = create_run(
                tmp,
                job_id="HOS-TEST-PARTIAL",
                provider="test",
                model="unknown",
                role="worker",
                request="x",
            )
            # Simulate crash after response.txt became durable but before metadata update.
            (run_dir / "response.txt").write_text("orphan response", encoding="utf-8")
            state = inspect_run(run_dir)
            self.assertEqual(state["state"], "RESPONSE_PENDING_METADATA")
            self.assertEqual(state["integrity"], "UNVERIFIED")

    def test_review_requires_completed_response_except_unverified(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = create_run(
                tmp,
                job_id="HOS-TEST-NORESPONSE",
                provider="test",
                model="unknown",
                role="reviewer",
                request="x",
            )
            with self.assertRaises(ValueError):
                record_review(run_dir, status="PASS", reviewer="test")
            record_review(run_dir, status="UNVERIFIED", reviewer="test", notes="No response captured")
            review = json.loads((run_dir / "review.json").read_text())
            self.assertIsNone(review["bound_response_sha256"])
            self.assertEqual(inspect_run(run_dir)["state"], "REVIEWED_INCOMPLETE")


if __name__ == "__main__":
    unittest.main()
