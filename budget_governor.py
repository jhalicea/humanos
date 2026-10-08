"""Deterministic token/attempt gate for a future trusted model dispatcher.

A recommendation is not permission to dispatch. A caller must separately enforce
owner authorization and provider controls. This gate fails closed for unmetered
or uncertain inference and never silently elevates effort or budgets.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class BudgetLimits:
    max_calls: int = 4
    max_total_tokens: int = 16000
    max_context_tokens: int = 8000
    max_output_tokens: int = 2000
    warning_percent: int = 80

    def __post_init__(self):
        for name in ("max_calls", "max_total_tokens", "max_context_tokens", "max_output_tokens"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError("budget limits must be positive integers")
        if (type(self.warning_percent) is not int or not 1 <= self.warning_percent <= 100
                or self.max_context_tokens > self.max_total_tokens):
            raise ValueError("invalid warning threshold or context limit")


class BudgetGovernor:
    """Per-task conservative reservation ledger. One in-flight call maximum.

    Used token count represents worst-case reservations, never an optimistic
    reported spend. Persist checkpoint externally before dispatch; restoring an
    in-flight checkpoint stops rather than replaying an uncertain call.
    """

    REPLAN_ACTIONS = ("reduce context", "split the task into independent slices",
                      "reuse prior verified evidence", "prefer deterministic tools",
                      "request a new explicit bounded authorization")

    def __init__(self, limits=None):
        self.limits = limits or BudgetLimits()
        self.calls = 0
        self.reserved_tokens = 0
        self.pending = None
        self.halted_reason = None

    def checkpoint(self):
        return {"schema": "humanos.budget.v1", "calls": self.calls,
                "reserved_tokens": self.reserved_tokens,
                "pending": list(self.pending) if self.pending else None,
                "halted_reason": self.halted_reason}

    @classmethod
    def restore(cls, checkpoint, limits=None):
        if not isinstance(checkpoint, dict) or set(checkpoint) != {
                "schema", "calls", "reserved_tokens", "pending", "halted_reason"}:
            raise ValueError("invalid budget checkpoint")
        if checkpoint["schema"] != "humanos.budget.v1":
            raise ValueError("unsupported budget checkpoint")
        guard = cls(limits)
        calls, tokens, pending = checkpoint["calls"], checkpoint["reserved_tokens"], checkpoint["pending"]
        if (type(calls) is not int or type(tokens) is not int or calls < 0
                or tokens < 0 or calls > guard.limits.max_calls
                or tokens > guard.limits.max_total_tokens):
            raise ValueError("invalid saved budget usage")
        if pending is not None and (not isinstance(pending, list) or len(pending) != 2
                or any(type(v) is not int or v < 0 for v in pending)):
            raise ValueError("invalid pending reservation")
        reason = checkpoint["halted_reason"]
        if reason is not None and (not isinstance(reason, str) or not reason):
            raise ValueError("invalid halt reason")
        guard.calls, guard.reserved_tokens = calls, tokens
        guard.pending = tuple(pending) if pending is not None else None
        guard.halted_reason = reason
        if guard.pending is not None:
            guard.halted_reason = "UNCERTAIN_INFLIGHT_CALL_ON_RESTART"
        return guard

    def _decision(self):
        if self.halted_reason:
            return {"status": "REPLAN_REQUIRED", "reason": self.halted_reason,
                    "usage": self.checkpoint(), "suggestions": list(self.REPLAN_ACTIONS),
                    "dispatch_allowed_by_budget": False}
        warn = (self.calls * 100 >= self.limits.max_calls * self.limits.warning_percent
                or self.reserved_tokens * 100 >= self.limits.max_total_tokens * self.limits.warning_percent)
        return {"status": "BUDGET_WARNING" if warn else "WITHIN_BUDGET",
                "usage": self.checkpoint(), "dispatch_allowed_by_budget": True}

    def _stop(self, reason):
        if not self.halted_reason:
            self.halted_reason = reason
        return self._decision()

    def reserve(self, *, effort, input_token_bound, output_token_cap,
                provider_enforces_low, provider_enforces_output_cap):
        if self.halted_reason:
            return self._decision()
        if self.pending is not None:
            return self._stop("CONCURRENT_OR_UNRECONCILED_CALL")
        if effort != "low":
            return self._stop("EFFORT_NOT_LOW")
        if provider_enforces_low is not True or provider_enforces_output_cap is not True:
            return self._stop("PROVIDER_LIMIT_UNVERIFIED")
        if (type(input_token_bound) is not int or type(output_token_cap) is not int
                or input_token_bound < 0 or output_token_cap < 1):
            return self._stop("TOKEN_BOUNDS_UNVERIFIED")
        if input_token_bound > self.limits.max_context_tokens:
            return self._stop("CONTEXT_LIMIT")
        if output_token_cap > self.limits.max_output_tokens:
            return self._stop("OUTPUT_LIMIT")
        reserved = input_token_bound + output_token_cap
        if self.calls + 1 > self.limits.max_calls or self.reserved_tokens + reserved > self.limits.max_total_tokens:
            return self._stop("PROJECTED_BUDGET_OVERRUN")
        self.calls += 1
        self.reserved_tokens += reserved
        self.pending = (input_token_bound, output_token_cap)
        return self._decision()

    def complete(self, *, input_tokens, output_tokens):
        if self.halted_reason:
            return self._decision()
        if self.pending is None:
            return self._stop("NO_INFLIGHT_CALL")
        if (type(input_tokens) is not int or type(output_tokens) is not int
                or input_tokens < 0 or output_tokens < 0):
            return self._stop("UNMETERED_MODEL_RESPONSE")
        input_bound, output_cap = self.pending
        if input_tokens > input_bound or output_tokens > output_cap:
            return self._stop("PROVIDER_TOKEN_BOUND_EXCEEDED")
        self.pending = None
        return self._decision()
