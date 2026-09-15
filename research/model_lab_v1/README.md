# HumanOS Model Lab v1

**Status:** PHASE 1 COMPLETE / PHASE 2 TRIALS A-B COMPLETE / OWNER ROUTING PREFERENCE RECORDED / ROUTING POLICY V1 CANDIDATE / DETERMINISTIC ROUTER TESTED / MIRROR ADAPTER IMPLEMENTED / MIRROR ADAPTER TESTS NOT YET RUN

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

The current candidate uses a simple role hierarchy:

- **Sol** — default lead / thought partner / architecture / important synthesis
- **Luna** — fast bounded worker
- **Terra** — methodical systems engineer / implementation candidate
- **Astra** — senior escalation / high-risk review / broad failure analysis
- **GPT-5.5** — transitional behavior benchmark only; never a durable production dependency

Core rule:

`use the least expensive continuing model that reliably meets the quality/risk requirement; default to Sol when judgment is still required`

This is not locked. Model Lab evidence can change roles, effort defaults, workflow order, and reviewer choices.

## Experimental workflow evidence

HumanOS records tested combinations separately from routing defaults. Current example:

- Astra / Light — engineer/advisor
- Terra / High — coder/implementer

The owner followed Astra's recommendation to use Terra High. That recommendation is preserved as provenance and experiment evidence; it is **not automatically promoted into policy**.

## Router implementation status

`model_router.py` implements the deterministic recommendation layer. It does not execute models or grant authority.

On 2026-09-15 the expanded router suite ran under macOS `/usr/bin/python3` 3.9.6 and passed **11/11 tests**.

The current router remains explicitly in **learning mode**:
- policy version: `v1-candidate`
- recommendation only: true
- policy locked: false
- authority granted: false

It supports recording an `ExperimentWorkflow` containing advisor model/effort, worker model/effort, whether the owner accepted the recommendation, and an experiment ID. Recording experimental provenance does not change the default policy.

## Mirror adapter status

`mirror_router_adapter.py` is now implemented as a thin learning-mode adapter around the router.

It can:
- convert a `TaskProfile` into a Mirror-consumable routing event;
- preserve the full provisional recommendation and experimental-workflow provenance;
- explicitly mark every event as `PROPOSED`;
- force `dispatch_allowed: false`, `automatic_execution: false`, `authority_granted: false`, and `policy_promotion: false`;
- optionally append the event to a small JSONL ledger using the existing HumanOS audit hash-chain functions;
- refuse further append if the existing ledger fails verification.

It does **not** dispatch Sol/Luna/Terra/Astra, invoke a provider, grant authority, or promote a workflow into policy.

A six-test adapter suite has been authored in `tests/test_mirror_router_adapter.py`, covering no-dispatch guarantees, route preservation, experiment preservation, single-event persistence, multi-event chaining, and tamper detection. Those tests have **not yet been run locally by the owner**.

## Files
- `PROTOCOL.md` — experiment controls and run procedure
- `QUICKSCREEN_TASKS.md` — frozen Phase 1 prompts
- `SCORECARD.md` — capability + fit rubric
- `RUN_LEDGER.md` — run/evidence log
- `MODEL_ROUTING_HYPOTHESES.md` — pre-registered hypotheses; do not rewrite after seeing results
- `MODEL_ROUTING_WORKFLOW_V0.md` — earlier specified planner/worker/reviewer workflow; preserved for provenance
- `MODEL_ROUTING_POLICY_V1_CANDIDATE.md` — evidence-based human-readable routing policy after Trials A-B
- `MODEL_ROUTING_POLICY_V1.yaml` — machine-readable candidate policy
- `ROUTER_TEST_EVIDENCE_2026-09-15.md` — owner-run unit-test evidence for the deterministic router
- `PHASE1_COMPARATIVE_RESULTS.md` — post-hoc Phase 1 analysis
- `PHASE2_ROLE_TRIALS.md` — job-specific trial protocol
- `PHASE2_TRIAL_A_RESULTS.md` — thought-partner results
- `PHASE2_TRIAL_B_RESULTS.md` — artifact/document results
- `OWNER_RATINGS_TRIAL_B.md` — owner preferences kept separate from correctness scoring
- `RAW_USAGE_OBSERVATIONS.md` — immutable observed plan-meter provenance and later attribution updates
- `MPC_WORKFLOW_USAGE_OBSERVATIONS_2026-09-15.md` — combined Astra-Light + Terra-High workflow usage provenance
- `/model_router.py` — deterministic learning-mode router
- `/mirror_router_adapter.py` — Mirror-facing recommendation/event adapter
- `/tests/test_model_router.py` — router tests
- `/tests/test_mirror_router_adapter.py` — Mirror adapter tests

## Status boundary

- Routing policy: **SPECIFIED / PROVISIONAL**
- Deterministic router: **IMPLEMENTED**
- Router unit tests: **TESTED — 11/11 PASS**
- Mirror-facing routing adapter: **IMPLEMENTED**
- Mirror adapter tests: **AUTHORED / NOT YET RUN LOCALLY**
- Automatic model dispatch: **NOT IMPLEMENTED**
- Provider execution: **NOT IMPLEMENTED**
- Routing-event persistence primitive: **IMPLEMENTED IN ADAPTER / NOT YET TESTED LOCALLY**
- Production verification/deployment: **NOT VERIFIED / NOT DEPLOYED**

Next target: run the six Mirror adapter tests. If they pass, test one real routing event locally without dispatching a model, inspect the persisted evidence, and only then consider any provider/model execution bridge.