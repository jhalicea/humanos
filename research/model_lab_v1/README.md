# HumanOS Model Lab v1

**Status:** PHASE 1 COMPLETE / PHASE 2 TRIALS A-B COMPLETE / OWNER ROUTING PREFERENCE RECORDED / ROUTING POLICY V1 CANDIDATE / ROUTER + MIRROR ADAPTER + DRY RUN VERIFIED / CONTEXT-PROVENANCE EXTENSION NOT YET RE-VERIFIED

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

## Verified router stack

`model_router.py` implements the deterministic recommendation layer. `mirror_router_adapter.py` converts a recommendation into a Mirror-facing routing event and can append it to a hash-chained JSONL ledger using existing HumanOS audit primitives. `routing_dry_run.py` exercises the local path without provider execution.

None of these components dispatches a model or grants authority.

On 2026-09-15 the owner ran the full verified suite:

```text
PYTHONPATH=. python3 -m unittest \
  tests.test_model_router \
  tests.test_mirror_router_adapter \
  tests.test_routing_dry_run \
  -v
```

Result: **20/20 PASS** in 0.004s.

Verified split:
- deterministic router: **11/11**
- Mirror adapter: **6/6**
- local dry-run layer: **3/3**

## First persisted real routing recommendation

The owner ran:

```text
PYTHONPATH=. python3 routing_dry_run.py \
  --task-id HOS-MIRROR-ROUTER-DRY-001
```

HumanOS emitted and persisted a `PROPOSED` routing event with:
- `DECIDE`
- `AMBER`
- primary model `sol`
- overlay `COLLABORATIVE_REFRAMER`
- `JUDGMENT_REQUIRED` + `MODERATE_RISK`
- policy `v1-candidate`
- router mode `learning`
- ledger recorded and verified
- no model dispatch
- no automatic execution
- no execution authority
- no policy promotion

Ledger path: `var/model-routing/routing-events.jsonl`.

This is the first verified local end-to-end routing recommendation in this Model Lab sequence. It is still a recommendation path only.

## New routing-context provenance extension

After the 20-test verified run, the Mirror adapter and CLI were extended to carry descriptive provenance about **how the TaskProfile was formed**, while deliberately keeping those fields outside the routing decision itself.

The new `routing_context` can preserve:
- task description;
- classifier source;
- classifier confidence (`UNASSESSED`, `LOW`, `MEDIUM`, `HIGH`);
- evidence references;
- assumptions;
- `affects_route: false`.

This gives HumanOS a place to record why a task was classified a certain way without pretending that free-text understanding or automatic classification is implemented yet.

Two additional tests were authored for this provenance layer, so the next expected total is **22 tests**. Those newest changes are **IMPLEMENTED / NOT YET RE-VERIFIED LOCALLY**.

## Files
- `PROTOCOL.md` — experiment controls and run procedure
- `QUICKSCREEN_TASKS.md` — frozen Phase 1 prompts
- `SCORECARD.md` — capability + fit rubric
- `RUN_LEDGER.md` — run/evidence log
- `MODEL_ROUTING_HYPOTHESES.md` — pre-registered hypotheses
- `MODEL_ROUTING_WORKFLOW_V0.md` — earlier planner/worker/reviewer workflow
- `MODEL_ROUTING_POLICY_V1_CANDIDATE.md` — provisional human-readable routing policy
- `MODEL_ROUTING_POLICY_V1.yaml` — machine-readable candidate policy
- `ROUTER_TEST_EVIDENCE_2026-09-15.md` — owner-run test and dry-run evidence
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
- Mirror-facing adapter baseline: **IMPLEMENTED + TESTED — 6/6 PASS**
- Local dry-run baseline: **IMPLEMENTED + TESTED — 3/3 PASS**
- Combined verified baseline: **20/20 PASS**
- First persisted routing recommendation: **VERIFIED LOCALLY**
- Routing-context provenance extension: **IMPLEMENTED / 2 NEW TESTS AUTHORED / NOT YET RE-VERIFIED LOCALLY**
- Automatic task-text classification: **NOT IMPLEMENTED**
- Automatic model dispatch: **NOT IMPLEMENTED**
- Provider execution: **NOT IMPLEMENTED**
- Production verification/deployment: **NOT VERIFIED / NOT DEPLOYED**

Next target: re-run the expanded 22-test suite, then generate a second real routing event containing a human-readable task description, evidence references, assumptions, and explicit classifier confidence. Keep routing behavior unchanged and no-dispatch until that provenance path is verified.
