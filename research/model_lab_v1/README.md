# HumanOS Model Lab v1

**Status:** PHASE 1 COMPLETE / PHASE 2 TRIALS A-B COMPLETE / OWNER ROUTING PREFERENCE RECORDED / ROUTING POLICY V1 CANDIDATE SPECIFIED / RUNTIME ROUTER NOT IMPLEMENTED

Purpose: determine which OpenAI model is best for which HumanOS task using Jon's actual working preferences rather than vendor positioning alone.

Initial comparison cohort:
- GPT-5.6 Luna
- GPT-5.6 Terra
- GPT-5.6 Sol
- GPT-5.5
- GPT-6 Astra

The lab separates three questions that are often incorrectly collapsed into one:
1. **Capability** — did the model solve the task correctly?
2. **Efficiency** — how much time/plan usage did the task consume?
3. **Working fit** — was the model useful, natural, decisive, appropriately skeptical, and easy for Jon to work with?

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
Run role finalists on controlled copies of real HumanOS tasks and measure correction burden, execution quality, plan usage, and routing-regret cases.

## Current routing direction

The current v1 candidate uses a simple role hierarchy:

- **Sol** — default lead / thought partner / architecture / important synthesis
- **Luna** — fast bounded worker
- **Terra** — methodical systems engineer
- **Astra** — senior escalation / high-risk review / broad failure analysis
- **GPT-5.5** — transitional behavior benchmark only; never a durable production dependency

Core rule:

`use the least expensive continuing model that reliably meets the quality/risk requirement; default to Sol when judgment is still required`

## Files
- `PROTOCOL.md` — experiment controls and run procedure
- `QUICKSCREEN_TASKS.md` — frozen Phase 1 prompts
- `SCORECARD.md` — capability + fit rubric
- `RUN_LEDGER.md` — run/evidence log
- `MODEL_ROUTING_HYPOTHESES.md` — pre-registered hypotheses; do not rewrite after seeing results
- `MODEL_ROUTING_WORKFLOW_V0.md` — earlier specified planner/worker/reviewer workflow; preserved for provenance
- `MODEL_ROUTING_POLICY_V1_CANDIDATE.md` — evidence-based human-readable routing policy after Trials A-B
- `MODEL_ROUTING_POLICY_V1.yaml` — machine-readable candidate policy for a future deterministic runtime router
- `PHASE1_COMPARATIVE_RESULTS.md` — post-hoc Phase 1 analysis
- `PHASE2_ROLE_TRIALS.md` — job-specific trial protocol
- `PHASE2_TRIAL_A_RESULTS.md` — thought-partner results
- `PHASE2_TRIAL_B_RESULTS.md` — artifact/document results
- `OWNER_RATINGS_TRIAL_B.md` — owner preferences kept separate from correctness scoring
- `RAW_USAGE_OBSERVATIONS.md` — immutable observed plan-meter provenance and later attribution updates

## Status boundary

The routing policy is **SPECIFIED** and can be followed manually during Model Lab / HumanOS work. Automatic model selection, dispatch, review chaining, and routing-event persistence are **NOT IMPLEMENTED IN THE HUMANOS RUNTIME** yet.

Next implementation target: a local deterministic router that reads `MODEL_ROUTING_POLICY_V1.yaml`, emits a routing recommendation/event, and is validated against recorded Model Lab cases before any automatic execution authority is considered.
