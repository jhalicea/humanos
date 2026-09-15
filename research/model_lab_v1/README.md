# HumanOS Model Lab v1

**Status:** PHASE 1 COMPLETE / PHASE 2 TRIALS A-B COMPLETE / OWNER ROUTING PREFERENCE RECORDED / ROUTING POLICY V1 CANDIDATE / ROUTER + MIRROR ADAPTER TESTED / DRY-RUN LAYER IMPLEMENTED, NOT YET RE-VERIFIED

Purpose: determine which model is best for which HumanOS task using Jon's actual working preferences and measured work, while keeping routing recommendations provisional until enough evidence accumulates.

Initial comparison cohort:
- GPT-5.6 Luna
- GPT-5.6 Terra
- GPT-5.6 Sol
- GPT-5.5
- GPT-6 Astra

The lab separates questions that are often incorrectly collapsed:
1. **Capability** — did the model solve the task correctly?
2. **Efficiency** — how much time/plan usage did the task consume?
3. **Working fit** — was the model useful, natural, decisive, appropriately skeptical, and easy for Jon to work with?
4. **Workflow fit** — which model + role + effort combination works best in a multi-model chain?

## Phases

### Phase 1 — Quick Screen
**Complete.** Three short, bounded tasks were run across all five models. Raw answers are preserved and objective scores are complete. Owner qualitative preference has been recorded.

### Phase 2 — Role Trials
**In progress.** Trial A (Thought Partner / Problem Framing) and Trial B (PDF / Document Creation and Conversation Feel) are complete. Remaining planned roles:
- Fast Implementation / General Engineering
- Architecture / Security / Authority Review
- Debugging / Failure Analysis
- Agentic Orchestration / Subagent Value

Trial B also produced a first usable owner-routing preference and a refreshed-page usage-calibration procedure. Usage percentages remain UI telemetry, not exact token/compute accounting.

### Phase 3 — Real HumanOS Work
Run role finalists and experimental workflows on controlled copies of real HumanOS tasks. Measure correction burden, execution quality, plan usage, elapsed time, owner fit, and routing-regret cases.

## Current routing direction — provisional

- **Sol** — default lead / thought partner / architecture / important synthesis
- **Luna** — fast bounded worker
- **Terra** — methodical systems engineer / implementation candidate
- **Astra** — senior escalation / high-risk review / broad failure analysis
- **GPT-5.5** — transitional behavior benchmark only; never a durable production dependency

Core rule:

`use the least expensive continuing model that reliably meets the quality/risk requirement; default to Sol when judgment is still required`

This is not locked. Model Lab evidence can change roles, effort defaults, workflow order, and reviewer choices.

## Experimental workflow evidence

Current example:
- Astra / Light — engineer/advisor
- Terra / High — coder/implementer

The owner followed Astra's recommendation to use Terra High. That recommendation is preserved as provenance and experiment evidence; it is **not automatically promoted into policy**.

## Router + Mirror adapter status

`model_router.py` implements the deterministic recommendation layer. `mirror_router_adapter.py` converts a recommendation into a Mirror-facing routing event and can append it to a hash-chained JSONL ledger using existing HumanOS audit primitives.

Neither module executes a model or grants authority.

On 2026-09-15 the owner ran:

```text
PYTHONPATH=. python3 -m unittest \
  tests.test_model_router \
  tests.test_mirror_router_adapter \
  -v
```

Result: **17/17 PASS** in 0.003s.

Verified properties include:
- router remains `v1-candidate`, learning-mode, recommendation-only, and unlocked;
- experimental workflows are recorded without promotion;
- no model dispatch or authority is granted;
- routing events persist and hash-chain correctly;
- multiple events chain correctly;
- tampering is detected and blocks another append.

## Local dry-run layer

`routing_dry_run.py` now provides the next local integration step:

`task profile -> route -> Mirror event -> optional ledger append -> hash-chain verification -> printed result`

It does **not** dispatch a model.

`tests/test_routing_dry_run.py` adds three tests covering an ambiguous Sol recommendation with persistence, no-persist mode, and a RED Sol+Astra-review recommendation with no dispatch.

These dry-run tests were authored **after** the verified 17-test run and are therefore **NOT YET RE-VERIFIED LOCALLY**.

## Files
- `PROTOCOL.md` — experiment controls and run procedure
- `QUICKSCREEN_TASKS.md` — frozen Phase 1 prompts
- `SCORECARD.md` — capability + fit rubric
- `RUN_LEDGER.md` — run/evidence log
- `MODEL_ROUTING_HYPOTHESES.md` — pre-registered hypotheses
- `MODEL_ROUTING_WORKFLOW_V0.md` — earlier planner/worker/reviewer workflow
- `MODEL_ROUTING_POLICY_V1_CANDIDATE.md` — provisional human-readable routing policy
- `MODEL_ROUTING_POLICY_V1.yaml` — machine-readable candidate policy
- `ROUTER_TEST_EVIDENCE_2026-09-15.md` — owner-run test evidence
- `PHASE1_COMPARATIVE_RESULTS.md`
- `PHASE2_ROLE_TRIALS.md`
- `PHASE2_TRIAL_A_RESULTS.md`
- `PHASE2_TRIAL_B_RESULTS.md`
- `OWNER_RATINGS_TRIAL_B.md`
- `RAW_USAGE_OBSERVATIONS.md`
- `MPC_WORKFLOW_USAGE_OBSERVATIONS_2026-09-15.md`
- `/model_router.py`
- `/mirror_router_adapter.py`
- `/routing_dry_run.py`
- `/tests/test_model_router.py`
- `/tests/test_mirror_router_adapter.py`
- `/tests/test_routing_dry_run.py`

## Status boundary

- Routing policy: **SPECIFIED / PROVISIONAL**
- Deterministic router: **IMPLEMENTED + TESTED — 11/11 PASS**
- Mirror-facing adapter: **IMPLEMENTED + TESTED — 6/6 PASS**
- Combined verified suite: **17/17 PASS**
- Local dry-run CLI: **IMPLEMENTED**
- Dry-run tests: **AUTHORED / NOT YET RE-VERIFIED LOCALLY**
- Automatic model dispatch: **NOT IMPLEMENTED**
- Provider execution: **NOT IMPLEMENTED**
- Production verification/deployment: **NOT VERIFIED / NOT DEPLOYED**

Next target: run the expanded suite including the dry-run tests, then execute one real local no-dispatch routing dry run and inspect the persisted event plus ledger verification result.
