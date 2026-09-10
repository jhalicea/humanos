import io
import json
import os
import stat
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import model_runs_cli


class ModelRunsCliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "model-runs"
        self.request_text = '{"prompt":"hello","n":1}\n'
        self.request_file = Path(self.tmp.name) / "request.txt"
        self.request_file.write_text(self.request_text, encoding="utf-8")
        self.response_file = Path(self.tmp.name) / "response.txt"
        self.response_file.write_text("TEST_RESPONSE", encoding="utf-8")

    def run_cli(self, argv):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            rc = model_runs_cli.main(argv)
        return rc, stdout.getvalue(), stderr.getvalue()

    def start_run(self, job_id="HOS-TEST-CLI-001"):
        rc, out, err = self.run_cli([
            "start",
            "--root", str(self.root),
            "--job-id", job_id,
            "--provider", "deepseek",
            "--model", "UNKNOWN",
            "--role", "worker",
            "--request-file", str(self.request_file),
            "--metadata-source", "unknown",
            "--repository-ref", "abc123",
        ])
        self.assertEqual(rc, 0, err)
        return Path(out.strip())

    def test_start_preserves_exact_request_envelope_and_private_permissions(self):
        run_dir = self.start_run()
        request = json.loads((run_dir / "request.json").read_text(encoding="utf-8"))
        metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(request["request"], self.request_text)
        self.assertEqual(request["job_id"], "HOS-TEST-CLI-001")
        self.assertEqual(metadata["provider"], "deepseek")
        self.assertEqual(metadata["model"], "UNKNOWN")
        self.assertEqual(metadata["metadata_source"], "unknown")
        self.assertEqual(stat.S_IMODE(os.stat(run_dir).st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(os.stat(run_dir / "request.json").st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(os.stat(run_dir / "metadata.json").st_mode), 0o600)

    def test_complete_review_and_inspect_flow(self):
        run_dir = self.start_run()
        rc, _, err = self.run_cli([
            "finish",
            "--root", str(self.root),
            "--run-dir", str(run_dir),
            "--response-file", str(self.response_file),
            "--model-version", "UNKNOWN",
            "--usage", '{"input_tokens":10,"output_tokens":5}',
            "--cost", '{"amount":0.0,"currency":"USD"}',
            "--quota-observation", "not exposed",
            "--finish-reason", "stop",
            "--tool-summary", '{"tools":[]}',
        ])
        self.assertEqual(rc, 0, err)
        self.assertEqual((run_dir / "response.txt").read_text(encoding="utf-8"), "TEST_RESPONSE")
        metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["usage"]["input_tokens"], 10)
        self.assertEqual(metadata["quota_observation"], "not exposed")
        self.assertEqual(stat.S_IMODE(os.stat(run_dir / "response.txt").st_mode), 0o600)

        rc, _, err = self.run_cli([
            "review",
            "--root", str(self.root),
            "--run-dir", str(run_dir),
            "--status", "PARTIAL",
            "--reviewer", "GPT-5.6-Sol",
            "--notes", "Useful structure; corrected contract violations.",
            "--evidence", '["tests/test_model_runs_cli.py"]',
        ])
        self.assertEqual(rc, 0, err)
        review = json.loads((run_dir / "review.json").read_text(encoding="utf-8"))
        self.assertEqual(review["status"], "PARTIAL")
        self.assertEqual(review["evidence"], ["tests/test_model_runs_cli.py"])

        rc, out, err = self.run_cli([
            "inspect",
            "--root", str(self.root),
            "--run-dir", str(run_dir),
            "--json",
        ])
        self.assertEqual(rc, 0, err)
        inspected = json.loads(out)
        self.assertTrue(inspected["response_present"])
        self.assertNotIn("response", inspected)
        self.assertEqual(inspected["review"]["status"], "PARTIAL")

    def test_finish_from_stdin_preserves_exact_response(self):
        run_dir = self.start_run()
        with mock.patch("sys.stdin", io.StringIO("STDIN_RESPONSE\n")):
            rc, _, err = self.run_cli([
                "finish",
                "--root", str(self.root),
                "--run-dir", str(run_dir),
                "--response-stdin",
            ])
        self.assertEqual(rc, 0, err)
        self.assertEqual((run_dir / "response.txt").read_text(encoding="utf-8"), "STDIN_RESPONSE\n")

    def test_start_from_stdin_preserves_raw_text_not_parsed_json(self):
        raw = '{"prompt":"still exact text"}'
        with mock.patch("sys.stdin", io.StringIO(raw)):
            rc, out, err = self.run_cli([
                "start",
                "--root", str(self.root),
                "--job-id", "HOS-TEST-STDIN",
                "--provider", "UNKNOWN",
                "--model", "UNKNOWN",
                "--role", "worker",
                "--request-stdin",
            ])
        self.assertEqual(rc, 0, err)
        run_dir = Path(out.strip())
        request = json.loads((run_dir / "request.json").read_text(encoding="utf-8"))
        self.assertEqual(request["request"], raw)

    def test_invalid_job_id_rejects_path_traversal(self):
        rc, _, err = self.run_cli([
            "start",
            "--root", str(self.root),
            "--job-id", "../escape",
            "--provider", "UNKNOWN",
            "--model", "UNKNOWN",
            "--role", "worker",
            "--request-file", str(self.request_file),
        ])
        self.assertNotEqual(rc, 0)
        self.assertIn("job-id", err)

    def test_run_dir_outside_root_is_rejected(self):
        outside = Path(self.tmp.name) / "outside"
        outside.mkdir()
        rc, _, err = self.run_cli([
            "inspect",
            "--root", str(self.root),
            "--run-dir", str(outside),
        ])
        self.assertNotEqual(rc, 0)
        self.assertIn("beneath ledger root", err)

    def test_usage_must_be_json_object(self):
        run_dir = self.start_run()
        rc, _, err = self.run_cli([
            "finish",
            "--root", str(self.root),
            "--run-dir", str(run_dir),
            "--response-file", str(self.response_file),
            "--usage", '[1,2,3]',
        ])
        self.assertNotEqual(rc, 0)
        self.assertIn("usage must be a JSON object", err)

    def test_second_finish_refuses_to_overwrite_completion_evidence(self):
        run_dir = self.start_run()
        first = self.run_cli([
            "finish", "--root", str(self.root), "--run-dir", str(run_dir),
            "--response-file", str(self.response_file),
        ])
        self.assertEqual(first[0], 0, first[2])
        original = (run_dir / "response.txt").read_text(encoding="utf-8")
        second = self.run_cli([
            "finish", "--root", str(self.root), "--run-dir", str(run_dir),
            "--response-stdin",
        ])
        self.assertNotEqual(second[0], 0)
        self.assertIn("already has completion evidence", second[2])
        self.assertEqual((run_dir / "response.txt").read_text(encoding="utf-8"), original)

    def test_second_review_refuses_to_overwrite_review_evidence(self):
        run_dir = self.start_run()
        first = self.run_cli([
            "review", "--root", str(self.root), "--run-dir", str(run_dir),
            "--status", "UNVERIFIED", "--reviewer", "first",
        ])
        self.assertEqual(first[0], 0, first[2])
        second = self.run_cli([
            "review", "--root", str(self.root), "--run-dir", str(run_dir),
            "--status", "PASS", "--reviewer", "second",
        ])
        self.assertNotEqual(second[0], 0)
        review = json.loads((run_dir / "review.json").read_text(encoding="utf-8"))
        self.assertEqual(review["reviewer"], "first")

    def test_evidence_must_be_string_array(self):
        run_dir = self.start_run()
        rc, _, err = self.run_cli([
            "review", "--root", str(self.root), "--run-dir", str(run_dir),
            "--status", "PARTIAL", "--reviewer", "test", "--evidence", '{"bad":true}',
        ])
        self.assertNotEqual(rc, 0)
        self.assertIn("JSON array of strings", err)


if __name__ == "__main__":
    unittest.main()
