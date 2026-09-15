# HumanOS Model Lab v1

**Status:** PHASE 1 COMPLETE / OWNER PREFERENCE RECORDED / PHASE 2 ROLE TRIALS PLANNED / ROUTING WORKFLOW V0 SPECIFIED / EFFICIENCY INCOMPLETE

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
**Complete.** Three short, bounded tasks were run across all five models. Raw answers are preserved and objective scores are complete. Owner qualitative preference has been recorded. Efficiency is still incomplete because timing and visible plan usage were not captured consistently.

### Phase 2 — Role Trials
**Planned.** Test models by specific job rather than as a global leaderboard. Current planned roles:
- Thought Partner / Problem Framing
- PDF / Document Creation and Conversation Feel
- Fast Implementation / General Engineering
- Architecture / Security / Authority Review
- Debugging / Failure Analysis
- Agentic Orchestration / Subagent Value

Each role uses likely finalists plus a deliberate cross-over model, with elapsed time, visible usage, correction burden, and subagent behavior captured where available.

### Phase 3 — Real HumanOS Work
Run role finalists on controlled copies of real HumanOS tasks and measure correction burden, execution quality, and plan usage.

## Core rule

Do not decide that one model is 'best.' The goal is a routing policy:

`task characteristics -> cheapest model that reliably achieves the required quality`

## Files
- `PROTOCOL.md` — experiment controls and run procedure
- `QUICKSCREEN_TASKS.md` — frozen Phase 1 prompts
- `SCORECARD.md` — capability + fit rubric
- `RUN_LEDGER.md` — run/evidence log
- `MODEL_ROUTING_HYPOTHESES.md` — pre-registered hypotheses; do not rewrite after seeing results
- `MODEL_ROUTING_WORKFLOW_V0.md` — specified planner/worker/reviewer model routing workflow; not implemented in runtime
- `PHASE1_COMPARATIVE_RESULTS.md` — post-hoc objective + owner-fit analysis and routing interpretation
- `PHASE2_ROLE_TRIALS.md` — job-specific trials, including PDF collaboration and agentic-orchestration tests

This is research documentation only. It does not alter HumanOS model routing or production behavior.
