# HumanOS Model Lab v1

**Status:** PHASE 1 COMPLETE / PHASE 2 TRIALS A-B COMPLETE / OWNER ROUTING PREFERENCE RECORDED / ROUTING POLICY V1 CANDIDATE / IMPLEMENTATION MOVED TO FOCUSED FEATURE PR

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

This is not locked. Model Lab evidence can change roles, effort defaults, workflow order, reviewer choices, or the rule itself.

## Experimental workflow evidence

Current example:
- Astra / Light — engineer/advisor
- Terra / High — coder/implementer

The owner followed Astra's recommendation to use Terra High. That recommendation is preserved as provenance and experiment evidence; it is **not automatically promoted into policy**.

## Implementation boundary

The Model Lab branch is research/evaluation only.

A router prototype was developed here during experimentation and reached a locally verified 20-test baseline plus a real no-dispatch dry run. To restore the established HumanOS SDLC boundary, runtime implementation has now been moved to the focused branch:

`feature/model-router-v1`

Draft implementation PR:

`#63 — Model Router v1 — recommendation-only runtime slice`

PR #63 is based directly on `runtime-0.1` and reconstructs the locally verified checkpoint `d932808409ddec353341bb769b5e45d21d7596d7`. The research branch no longer carries the runtime router/adapter/dry-run files at its head.

The implementation PR must independently satisfy the repository SDLC: focused scope, acceptance criteria, full test suite, local interaction checks, diff review, evidence, independent review, rollback, and owner approval before merge.

## Research evidence from the router prototype

Historical evidence remains preserved in this research branch because it informed the routing hypothesis:

- deterministic router baseline: 11/11 targeted tests passed locally;
- Mirror adapter baseline: 6/6 targeted tests passed locally;
- dry-run baseline: 3/3 targeted tests passed locally;
- combined targeted baseline: 20/20 passed locally;
- one real local routing recommendation was persisted and hash-chain verified;
- no model dispatch, automatic execution, authority grant, or policy promotion occurred;
- later unverified routing-context provenance experiments remain branch-history evidence only and were not promoted into the focused implementation baseline.

These observations are research/provenance evidence, not production certification.

## Files
- `PROTOCOL.md` — experiment controls and run procedure
- `QUICKSCREEN_TASKS.md` — frozen Phase 1 prompts
- `SCORECARD.md` — capability + fit rubric
- `RUN_LEDGER.md` — run/evidence log
- `MODEL_ROUTING_HYPOTHESES.md` — pre-registered hypotheses
- `MODEL_ROUTING_WORKFLOW_V0.md` — earlier planner/worker/reviewer workflow
- `MODEL_ROUTING_POLICY_V1_CANDIDATE.md` — provisional human-readable routing policy
- `MODEL_ROUTING_POLICY_V1.yaml` — machine-readable candidate policy
- `ROUTER_TEST_EVIDENCE_2026-09-15.md` — historical owner-run router test and dry-run evidence
- `PHASE1_COMPARATIVE_RESULTS.md`
- `PHASE2_ROLE_TRIALS.md`
- `PHASE2_TRIAL_A_RESULTS.md`
- `PHASE2_TRIAL_B_RESULTS.md`
- `OWNER_RATINGS_TRIAL_B.md`
- `RAW_USAGE_OBSERVATIONS.md`
- `MPC_WORKFLOW_USAGE_OBSERVATIONS_2026-09-15.md`

## Status boundary

- Model Lab research: **ACTIVE**
- Routing policy: **SPECIFIED / PROVISIONAL / NOT LOCKED**
- Runtime implementation on this branch: **REMOVED FROM HEAD / MOVED TO FEATURE PR #63**
- Focused implementation branch: **feature/model-router-v1**
- Focused implementation status: **DRAFT / REQUIRES FRESH SDLC VERIFICATION**
- Automatic task-text classification: **NOT IMPLEMENTED IN VERIFIED BASELINE**
- Automatic model dispatch: **NOT IMPLEMENTED**
- Provider execution: **NOT IMPLEMENTED**
- Production verification/deployment: **NOT VERIFIED / NOT DEPLOYED**

Next research target: continue model/role/effort testing and record evidence without changing the focused runtime implementation unless a new SDLC increment is explicitly opened.
