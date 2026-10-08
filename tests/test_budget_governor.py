import unittest
from budget_governor import BudgetGovernor, BudgetLimits


class BudgetGovernorTests(unittest.TestCase):
    def reserve(self, guard, input_tokens=1000, output_tokens=500, effort="low",
                low_supported=True, cap_supported=True):
        return guard.reserve(effort=effort, input_token_bound=input_tokens,
                             output_token_cap=output_tokens,
                             provider_enforces_low=low_supported,
                             provider_enforces_output_cap=cap_supported)

    def test_low_effort_allows_a_bounded_call(self):
        guard = BudgetGovernor()
        result = self.reserve(guard)
        self.assertTrue(result["dispatch_allowed_by_budget"])
        self.assertEqual("WITHIN_BUDGET", result["status"])
        self.assertEqual(1500, guard.reserved_tokens)
        self.assertEqual("WITHIN_BUDGET", guard.complete(input_tokens=800, output_tokens=300)["status"])
        self.assertEqual(1500, guard.reserved_tokens)  # conservative reservation, not optimistic usage

    def test_high_effort_never_auto_escalates(self):
        guard = BudgetGovernor()
        self.assertEqual("EFFORT_NOT_LOW", self.reserve(guard, effort="high")["reason"])
        self.assertEqual("REPLAN_REQUIRED", self.reserve(guard)["status"])
        self.assertEqual(0, guard.calls)

    def test_unknown_provider_enforcement_fails_closed(self):
        for kwargs in ({"low_supported": False}, {"cap_supported": False}):
            guard = BudgetGovernor()
            self.assertEqual("PROVIDER_LIMIT_UNVERIFIED", self.reserve(guard, **kwargs)["reason"])

    def test_projected_overrun_stops_without_an_extra_call(self):
        guard = BudgetGovernor(BudgetLimits(max_calls=1, max_total_tokens=2000,
                                             max_context_tokens=1600, max_output_tokens=500))
        self.assertEqual("WITHIN_BUDGET", self.reserve(guard)["status"])
        guard.complete(input_tokens=1000, output_tokens=500)
        stopped = self.reserve(guard)
        self.assertEqual("PROJECTED_BUDGET_OVERRUN", stopped["reason"])
        self.assertEqual(1, guard.calls)
        self.assertFalse(stopped["dispatch_allowed_by_budget"])

    def test_context_and_output_bounds_stop(self):
        self.assertEqual("CONTEXT_LIMIT", self.reserve(BudgetGovernor(), input_tokens=9000)["reason"])
        self.assertEqual("OUTPUT_LIMIT", self.reserve(BudgetGovernor(), output_tokens=2500)["reason"])

    def test_warning_at_eighty_percent(self):
        guard = BudgetGovernor(BudgetLimits(max_calls=2, max_total_tokens=20000))
        self.assertEqual("BUDGET_WARNING", self.reserve(guard)["status"])

    def test_unknown_usage_and_provider_overrun_stop(self):
        guard = BudgetGovernor()
        self.reserve(guard)
        self.assertEqual("UNMETERED_MODEL_RESPONSE", guard.complete(input_tokens=None, output_tokens=None)["reason"])
        other = BudgetGovernor()
        self.reserve(other)
        self.assertEqual("PROVIDER_TOKEN_BOUND_EXCEEDED", other.complete(input_tokens=1001, output_tokens=400)["reason"])

    def test_restart_is_conservative_and_no_retry_occurs(self):
        guard = BudgetGovernor()
        self.reserve(guard)
        restored = BudgetGovernor.restore(guard.checkpoint())
        self.assertEqual("UNCERTAIN_INFLIGHT_CALL_ON_RESTART", self.reserve(restored)["reason"])
        self.assertEqual(1, restored.calls)

    def test_completed_checkpoint_restores_accounting(self):
        guard = BudgetGovernor()
        self.reserve(guard)
        guard.complete(input_tokens=600, output_tokens=200)
        restored = BudgetGovernor.restore(guard.checkpoint())
        self.assertEqual(1, restored.calls)
        self.assertEqual(1500, restored.reserved_tokens)
        self.assertTrue(self.reserve(restored)["dispatch_allowed_by_budget"])

    def test_invalid_checkpoint_fails_closed(self):
        snapshot = BudgetGovernor().checkpoint()
        snapshot["reserved_tokens"] = -1
        with self.assertRaises(ValueError):
            BudgetGovernor.restore(snapshot)


if __name__ == "__main__":
    unittest.main()
