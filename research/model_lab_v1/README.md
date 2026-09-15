# HumanOS Model Lab v1

**Status:** PHASE 1 COMPLETE / PHASE 2 TRIALS A-B COMPLETE / OWNER ROUTING PREFERENCE RECORDED / ROUTING POLICY V1 CANDIDATE / DETERMINISTIC ROUTER TESTED / MIRROR INTEGRATION NOT IMPLEMENTED

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

On 2026-09-15 the original router test suite ran under macOS `/usr/bin/python3` 3.9.6 and passed 8/8 tests.

The latest revision keeps the router explicitly in **learning mode**:
- policy version: `v1-candidate`
- recommendation only: true
- policy locked: false
- authority granted: false

It also supports recording an `ExperimentWorkflow` containing advisor model/effort, worker model/effort, whether the owner accepted the recommendation, and an experiment ID. Recording experimental provenance does not change the default policy.

## Files
- `PROTOCOL.md` — experiment controls and run procedure
- `QUICKSCREEN_TASKS.md` — frozen Phase 1 prompts
- `SCORECARD.md` — capability + fit rubric
- `RUN_LEDGER.md` — run/evidence log
- `MODEL_ROUTING_HYPOTHESES.md` — pre-registered hypotheses; do not rewrite after seeing results
- `MODEL_ROUTING_WORKFLOW_V0.md` — earlier specified planner/worker/reviewer workflow; preserved for provenance
- `MODEL_ROUTING_POLICY_V1_CANDIDATE.md` — evidence-based human-readable routing policy after Trials A-B
- `MODEL_ROUTING_POLICY_V1.yaml` — machine-readable candidate policy
- `ROUTER_TEST_EVIDENCE_2026-09-15.md` — owner-run unit-test evidence for the original deterministic router
- `PHASE1_COMPARATIVE_RESULTS.md` — post-hoc Phase 1 analysis
- `PHASE2_ROLE_TRIALS.md` — job-specific trial protocol
- `PHASE2_TRIAL_A_RESULTS.md` — thought-partner results
- `PHASE2_TRIAL_B_RESULTS.md` — artifact/document results
- `OWNER_RATINGS_TRIAL_B.md` — owner preferences kept separate from correctness scoring
- `RAW_USAGE_OBSERVATIONS.md` — immutable observed plan-meter provenance and later attribution updates
- `MPC_WORKFLOW_USAGE_OBSERVATIONS_2026-09-15.md` — combined Astra-Light + Terra-High workflow usage provenance

## Status boundary

- Routing policy: **SPECIFIED / PROVISIONAL**
- Deterministic router: **IMPLEMENTED**
- Original router unit tests: **TESTED — 8/8 PASS**
- Latest learning-mode / experiment-provenance changes: **IMPLEMENTED / NEW TESTS AUTHORED / NOT YET RE-VERIFIED LOCALLY**
- Mirror integration: **NOT IMPLEMENTED**
- Automatic model dispatch: **NOT IMPLEMENTED**
- Routing-event persistence: **NOT IMPLEMENTED**
- Production verification/deployment: **NOT VERIFIED / NOT DEPLOYED**

Next target: re-run the expanded router test suite, then add a Mirror-facing adapter that emits routing recommendations and experiment provenance without automatic execution authority.
