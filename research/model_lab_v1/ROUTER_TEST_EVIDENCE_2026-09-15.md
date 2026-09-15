# HumanOS Model Router — Test Evidence

**Date:** 2026-09-15
**Branch:** `research/model-lab-v1`
**Environment:** macOS system Python `/usr/bin/python3`, Python 3.9.6
**Command:** `PYTHONPATH=. python3 -m unittest tests.test_model_router -v`

## Latest result

All **11** router unit tests passed after the learning-mode and experimental-workflow changes:

- `test_amber_bounded_work_gets_sol_review` — PASS
- `test_ambiguous_work_defaults_to_sol` — PASS
- `test_astra_recommended_terra_high_is_recorded_not_promoted` — PASS
- `test_broad_red_work_escalates_to_astra` — PASS
- `test_green_bounded_work_routes_to_luna` — PASS
- `test_invalid_experiment_effort_is_rejected` — PASS
- `test_invalid_owner_override_is_rejected` — PASS
- `test_methodical_state_work_routes_to_terra` — PASS
- `test_owner_override_is_recorded_without_erasing_risk` — PASS
- `test_red_security_work_uses_sol_with_astra_review` — PASS
- `test_router_explicitly_remains_learning_and_unlocked` — PASS

Observed terminal summary:

```text
----------------------------------------------------------------------
Ran 11 tests in 0.000s

OK
```

## What this verifies

- deterministic task/risk classification covered by the test suite;
- owner overrides do not erase risk classification;
- the router remains `v1-candidate`, learning-mode, recommendation-only, unlocked, and without execution authority;
- the Astra Light -> Terra High MPC workflow can be captured as experimental provenance without promotion into default policy;
- invalid experiment effort values are rejected.

## Status interpretation

- Router implementation: **IMPLEMENTED**
- Router unit tests: **TESTED — 11/11 PASS**
- Mirror-facing adapter: **IMPLEMENTED AFTER THIS TEST RUN / NOT YET TESTED LOCALLY**
- Automatic model dispatch: **NOT IMPLEMENTED**
- Production verification/deployment: **NOT VERIFIED / NOT DEPLOYED**

This evidence establishes only the deterministic routing logic covered by `tests.test_model_router`. It does not establish end-to-end model dispatch, provider integration, production safety, or the newly added Mirror adapter tests.