# HumanOS Model Router v1 — SDLC Checkpoint

Status: PLANNING / IMPLEMENTATION CANDIDATE
Owner: Jon Alicea
Date: 2026-09-15

## Problem

HumanOS needs a deterministic, auditable way to recommend which model should handle a task without granting execution authority, locking an experimental model policy, or confusing research evidence with production behavior.

## Scope

This increment is limited to:

- deterministic task/risk classification;
- a recommendation-only model route;
- explicit learning/provisional policy state;
- preservation of owner overrides without erasing risk;
- preservation of experimental multi-model workflows without policy promotion;
- a Mirror-facing routing event;
- append-only, hash-chained routing-event persistence using existing HumanOS audit primitives;
- a local no-dispatch dry-run CLI;
- automated tests for the above.

## Non-goals

This increment does not:

- call Sol, Luna, Terra, Astra, or any provider;
- automatically switch models;
- grant tool or external-action authority;
- promote Model Lab observations into permanent routing policy;
- classify arbitrary natural-language tasks automatically;
- write to the active Life Notebook;
- modify canonical personal state;
- deploy to production.

## Foundation / governance constraints

- Human owner remains final authority.
- Model outputs are proposals, not authorization.
- Routing must remain provider-neutral and auditable.
- Experimental workflows must be preserved as provenance, not silently promoted.
- No production execution authority is created by this branch.
- Tests must use isolated temporary ledgers and must not operate on the owner's active Notebook.
- Recovery, provenance, and rollback must remain explicit.

## Observable acceptance criteria

1. A bounded GREEN task can produce a provisional recommendation without dispatching a model.
2. An ambiguous task routes to the current candidate lead model while preserving `recommendation_only=true`, `policy_locked=false`, and `authority_granted=false`.
3. RED security/privacy/authority work preserves senior-review requirements.
4. Owner override changes the selected model but does not erase the risk lane.
5. An Astra-Light -> Terra-High experimental workflow can be recorded with `promoted_to_policy=false`.
6. Mirror routing events are `PROPOSED` and explicitly set dispatch, automatic execution, authority, and policy promotion to false.
7. Routing events can be appended to an isolated JSONL ledger and the hash chain verifies.
8. Tampering causes verification failure and blocks a subsequent append.
9. A local dry run can perform classify -> recommend -> persist -> verify -> print with no model dispatch.
10. Targeted router/adapter/dry-run tests pass.
11. The repository-wide test suite passes before merge.
12. The implementation diff is reviewed for regressions, privacy leakage, authority changes, idempotency, recovery, data-format impact, and accidental private data.

## Evidence baseline

The implementation candidate is being reconstructed from the locally verified Model Lab checkpoint `d932808409ddec353341bb769b5e45d21d7596d7` rather than from later unverified experimental edits.

At that checkpoint the owner observed:

- 20 targeted tests passing locally;
- a real no-dispatch routing dry run with `ledger_recorded=true`, `ledger_verified=true`, `model_dispatched=false`, and `authority_granted=false`;
- GitHub Actions regression and encrypted-backup workflows reporting success for that commit.

These observations establish a useful baseline but do not substitute for re-running the full suite on this focused implementation branch.

## Rollback

This work is isolated from `runtime-0.1` on a focused feature branch. Rollback is therefore to leave `runtime-0.1` unchanged and close the feature PR. No migration or canonical-state mutation is part of this increment.

## Review gate

Before merge:

- run the repository-wide test command required by `AGENTS.md`;
- capture exact commit SHA and commands/results;
- review the focused diff;
- record known limitations and defects;
- perform independent review against the same immutable commit;
- obtain owner approval for merge/release.
