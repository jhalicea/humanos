# HumanOS Model Router — Test Evidence

**Date:** 2026-09-15
**Branch:** `research/model-lab-v1`
**Environment:** macOS system Python `/usr/bin/python3`, Python 3.9.6

## Latest verified result

Owner ran:

```text
PYTHONPATH=. python3 -m unittest \
  tests.test_model_router \
  tests.test_mirror_router_adapter \
  -v
```

All **17** tests passed:

### Deterministic router — 11/11 PASS
- `test_amber_bounded_work_gets_sol_review`
- `test_ambiguous_work_defaults_to_sol`
- `test_astra_recommended_terra_high_is_recorded_not_promoted`
- `test_broad_red_work_escalates_to_astra`
- `test_green_bounded_work_routes_to_luna`
- `test_invalid_experiment_effort_is_rejected`
- `test_invalid_owner_override_is_rejected`
- `test_methodical_state_work_routes_to_terra`
- `test_owner_override_is_recorded_without_erasing_risk`
- `test_red_security_work_uses_sol_with_astra_review`
- `test_router_explicitly_remains_learning_and_unlocked`

### Mirror-facing adapter — 6/6 PASS
- `test_adapter_preserves_candidate_route`
- `test_event_is_proposal_only_and_never_dispatches`
- `test_experimental_workflow_is_preserved_but_not_promoted`
- `test_ledger_chains_multiple_events`
- `test_ledger_persists_and_verifies_one_event`
- `test_tampered_ledger_fails_verification`

Observed terminal summary:

```text
----------------------------------------------------------------------
Ran 17 tests in 0.003s

OK
```

## What this verifies

- deterministic routing behavior covered by the current test suite;
- owner overrides do not erase risk classification;
- router remains `v1-candidate`, learning-mode, recommendation-only, unlocked, and without execution authority;
- Astra Light -> Terra High MPC workflow can be recorded as experimental provenance without promotion into default policy;
- Mirror adapter preserves the recommendation without dispatching any model;
- routing events can be persisted to an append-only JSONL ledger using the HumanOS hash-chain audit primitives;
- multiple routing events chain correctly;
- tampering causes verification failure;
- failed ledger verification prevents another append.

## Current status

- Routing policy: **SPECIFIED / PROVISIONAL**
- Deterministic router: **IMPLEMENTED + TESTED — 11/11 PASS**
- Mirror-facing adapter: **IMPLEMENTED + TESTED — 6/6 PASS**
- Combined verified suite: **17/17 PASS**
- Automatic model dispatch: **NOT IMPLEMENTED**
- Provider execution: **NOT IMPLEMENTED**
- Production verification/deployment: **NOT VERIFIED / NOT DEPLOYED**

## New dry-run layer after this verified run

A local `routing_dry_run.py` CLI and `tests/test_routing_dry_run.py` were added after the 17-test verification. They are intended to exercise one real local routing event end to end: classify -> recommend -> persist -> verify -> print, while keeping dispatch and authority false.

These new dry-run tests are **AUTHORED / NOT YET RE-VERIFIED LOCALLY**. Do not count them in the 17/17 verified total until the owner runs them.
