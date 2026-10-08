"""Deterministic tests of true API output cap and fail-closed budget dispatch.

No network, credentials, user data, model invocation or paid API calls.
"""
import json
import os
import subprocess
import sys
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from budget_governor import BudgetLimits
from bounded_responses import ReplanRequired, execute


class FakeAPI:
    def __init__(self, count=100, response=None, error=None):
        self.count = count
        self.error = error
        self.calls = []
        self.response = response or {
            "status": "completed",
            "usage": {"input_tokens": 100, "output_tokens": 60,
                      "total_tokens": 160},
            "output": [{"type": "message", "content": [
                {"type": "output_text", "text": "review complete"}]}],
        }

    def post(self, path, body):
        self.calls.append((path, body))
        if path == "/responses/input_tokens":
            if self.error == "count":
                raise RuntimeError("offline count failure")
            return {"object": "response.input_tokens", "input_tokens": self.count}
        if self.error == "response":
            raise RuntimeError("offline simulated timeout")
        return self.response


class BoundedTransportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        patcher = patch("bounded_responses.Path.home", return_value=self.home)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.ledger = self.home / ".humanos" / "private" / "budgets" / "test.json"
        self.limits = BudgetLimits(max_calls=2, max_total_tokens=600,
                                   max_context_tokens=500, max_output_tokens=200)

    def go(self, fake, **kw):
        return execute(ledger_path=self.ledger, model="gpt-6-luna",
                       prompt="What changed?", instructions="Answer briefly.",
                       output_cap=200, limits=self.limits, transport=fake, **kw)

    def test_sends_low_and_provider_output_cap(self):
        api = FakeAPI()
        result = self.go(api)
        self.assertEqual("completed", result["status"])
        self.assertEqual("review complete", result["text"])
        self.assertEqual(["/responses/input_tokens", "/responses"],
                         [r[0] for r in api.calls])
        self.assertEqual(200, api.calls[1][1]["max_output_tokens"])
        self.assertEqual("low", api.calls[1][1]["reasoning"]["effort"])
        self.assertFalse(api.calls[1][1]["store"])
        self.assertEqual([], api.calls[1][1]["tools"])
        self.assertEqual(300, result["reserved_total_tokens"])

    def test_no_paid_dispatch_if_budget_exceeded(self):
        api = FakeAPI(count=500)
        with self.assertRaisesRegex(ReplanRequired, "PROJECTED_BUDGET_OVERRUN"):
            self.go(api)
        self.assertEqual(["/responses/input_tokens"], [r[0] for r in api.calls])
        saved = json.loads(self.ledger.read_text())
        self.assertEqual(0, saved["checkpoint"]["calls"])

    def test_second_call_then_sticky_stop(self):
        api = FakeAPI()
        self.go(api)
        self.go(api)
        with self.assertRaises(ReplanRequired):
            self.go(api)
        self.assertEqual(2, [name for name, _ in api.calls].count("/responses"))

    def test_crash_during_provider_request_never_autoretries(self):
        lost = FakeAPI(error="response")
        with self.assertRaisesRegex(ReplanRequired, "NO_RETRY"):
            self.go(lost)
        next_call = FakeAPI()
        with self.assertRaisesRegex(ReplanRequired, "UNCERTAIN_INFLIGHT_CALL_ON_RESTART"):
            self.go(next_call)
        self.assertEqual(0, len(next_call.calls))

    def test_missing_usage_halts_future_work(self):
        api = FakeAPI(response={"status": "completed", "output": []})
        with self.assertRaisesRegex(ReplanRequired, "USAGE_UNVERIFIED"):
            self.go(api)
        with self.assertRaises(ReplanRequired):
            self.go(FakeAPI())

    def test_actual_usage_above_reserved_halts(self):
        api = FakeAPI(response={"status": "completed", "usage": {
            "input_tokens": 101, "output_tokens": 60, "total_tokens": 161},
            "output": []})
        with self.assertRaisesRegex(ReplanRequired, "PROVIDER_TOKEN_BOUND_EXCEEDED"):
            self.go(api)

    def test_invalid_total_usage_blocks(self):
        api = FakeAPI(response={"status": "completed", "usage": {
            "input_tokens": 100, "output_tokens": 30, "total_tokens": 999},
            "output": []})
        with self.assertRaisesRegex(ReplanRequired, "USAGE_INVALID"):
            self.go(api)

    def test_count_must_be_exact_schema(self):
        class BadCount(FakeAPI):
            def post(self, path, body):
                if path == "/responses/input_tokens":
                    return {"input_tokens": 10}
                return super().post(path, body)
        with self.assertRaisesRegex(ReplanRequired, "COUNT_UNVERIFIED"):
            self.go(BadCount())
        self.assertFalse(self.ledger.exists())

    def test_model_and_limits_cannot_change_on_ledger(self):
        self.go(FakeAPI())
        with self.assertRaisesRegex(ReplanRequired, "BUDGET_POLICY_CHANGED"):
            execute(ledger_path=self.ledger, model="gpt-6-astra",
                    prompt="What changed?", instructions="Answer briefly.",
                    output_cap=200, limits=self.limits, transport=FakeAPI())

    def test_incomplete_response_never_autoretried(self):
        api = FakeAPI(response={"status": "incomplete",
            "incomplete_details": {"reason": "max_output_tokens"},
            "usage": {"input_tokens": 100, "output_tokens": 200,
                      "total_tokens": 300}, "output": []})
        value = self.go(api)
        self.assertEqual("incomplete", value["status"])
        self.assertEqual("max_output_tokens", value["incomplete_reason"])
        self.assertEqual(1, [p for p, _ in api.calls].count("/responses"))

    def test_private_state_does_not_store_prompt_or_key(self):
        self.go(FakeAPI())
        saved = self.ledger.read_text()
        self.assertNotIn("What changed?", saved)
        self.assertNotIn("Answer briefly.", saved)
        self.assertEqual(0o600, self.ledger.stat().st_mode & 0o777)

    def test_path_outside_private_humanos_rejected(self):
        with self.assertRaises(PermissionError):
            execute(ledger_path=self.home / "Developer" / "10_Repos" / "humanos" / "ledger.json",
                    model="gpt-6-luna", prompt="hello",
                    instructions="", output_cap=200,
                    limits=self.limits, transport=FakeAPI())

    def test_cli_requires_explicit_charge_consent(self):
        prompt = self.home / "prompt.txt"
        prompt.write_text("Explain one thing.")
        cli = Path(__file__).resolve().parents[1] / "scripts" / "bounded_api_run.py"
        args = [sys.executable, str(cli),
                "--model", "gpt-6-luna",
                "--prompt-file", str(prompt),
                "--ledger", str(self.ledger),
                "--budget-total", "1000",
                "--context-cap", "500",
                "--output-cap", "200"]
        env = dict(os.environ)
        env.pop("OPENAI_API_KEY", None)
        offline = subprocess.run(args + ["--dry-run"], env=env,
                                 text=True, capture_output=True, check=False)
        self.assertEqual(0, offline.returncode, offline.stderr)
        self.assertIn("no API calls", offline.stdout)
        denied = subprocess.run(args, env=env, text=True,
                                capture_output=True, check=False)
        self.assertEqual(2, denied.returncode)
        self.assertIn("API_CHARGES_NOT_AUTHORIZED", denied.stderr)
        self.assertFalse(self.ledger.exists())


if __name__ == "__main__":
    unittest.main()
