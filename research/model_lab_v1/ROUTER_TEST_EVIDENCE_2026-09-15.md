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
  tests.test_routing_dry_run \
  -v
```

All **20** tests passed in **0.004s**.

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

### Local routing dry run — 3/3 PASS
- `test_ambiguous_task_dry_run_records_sol_recommendation`
- `test_no_persist_mode_never_writes_ledger`
- `test_red_dry_run_preserves_review_without_dispatch`

Observed terminal summary:

```text
----------------------------------------------------------------------
Ran 20 tests in 0.004s

OK
```

## First real persisted no-dispatch routing event

Owner then ran:

```text
PYTHONPATH=. python3 routing_dry_run.py \
  --task-id HOS-MIRROR-ROUTER-DRY-001
```

Observed result:
- event type: `MODEL_ROUTING_RECOMMENDATION`
- schema: `routing-event-v0`
- task class: `DECIDE`
- risk lane: `AMBER`
- primary model: `sol`
- behavior overlay: `COLLABORATIVE_REFRAMER`
- reason codes: `JUDGMENT_REQUIRED`, `MODERATE_RISK`
- policy version: `v1-candidate`
- router mode: `learning`
- event status: `PROPOSED`
- ledger path: `var/model-routing/routing-events.jsonl`
- ledger recorded: **true**
- ledger verified: **true**
- model dispatched: **false**
- automatic execution: **false**
- authority granted: **false**
- policy promotion: **false**

This is the first locally persisted end-to-end routing recommendation in this Model Lab sequence: task profile -> deterministic route -> Mirror event -> append-only hash-chained ledger -> verification -> printed result. It does **not** establish provider execution or automatic model switching.

## What this verifies

- deterministic routing behavior covered by the current verified suite;
- owner overrides do not erase risk classification;
- router remains `v1-candidate`, learning-mode, recommendation-only, unlocked, and without execution authority;
- Astra Light -> Terra High MPC workflow can be recorded as experimental provenance without promotion into default policy;
- Mirror adapter preserves recommendations without model dispatch;
- routing events persist and hash-chain correctly;
- multiple events chain correctly;
- tampering causes verification failure and blocks another append;
- the local dry-run CLI can generate, persist, and verify a real routing recommendation without dispatch.

## Current verified status

- Routing policy: **SPECIFIED / PROVISIONAL**
- Deterministic router: **IMPLEMENTED + TESTED — 11/11 PASS**
- Mirror-facing adapter: **IMPLEMENTED + TESTED — 6/6 PASS**
- Local dry-run layer: **IMPLEMENTED + TESTED — 3/3 PASS**
- Combined verified suite: **20/20 PASS**
- First persisted real routing recommendation: **VERIFIED LOCALLY**
- Automatic model dispatch: **NOT IMPLEMENTED**
- Provider execution: **NOT IMPLEMENTED**
- Production verification/deployment: **NOT VERIFIED / NOT DEPLOYED**

## New provenance-context changes after this verified run

After the 20-test verification, the adapter and dry-run CLI were extended to preserve task-description/classifier provenance without changing routing behavior. New fields include:
- task description;
- classifier source;
- classifier confidence (`UNASSESSED`, `LOW`, `MEDIUM`, `HIGH`);
- evidence references;
- explicit assumptions;
- `affects_route: false` in the context record.

Two additional tests were authored after the 20-test verification, bringing the next expected suite to **22 tests**. These newest context-provenance changes are **IMPLEMENTED / TESTS AUTHORED / NOT YET RE-VERIFIED LOCALLY**.
