# HumanOS Model Lab v1

**Status:** PHASE 1 QUICK SCREEN COMPLETE / JON-FIT PROVISIONALLY SCORED / EFFICIENCY INCOMPLETE

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
**Complete.** Three short, bounded tasks were run across all five models. Raw answers are preserved and objective scores are complete. Holistic Jon-fit has been provisionally scored. Efficiency is still incomplete because timing and visible plan usage were not captured consistently.

### Phase 2 — Role Trials
Next. Give models tasks matched to likely roles: worker, engineer, architect/reviewer, and long-horizon specialist, with at least one cross-over challenge to test the routing hypothesis.

### Phase 3 — Real HumanOS Work
Run the finalists on controlled copies of real HumanOS tasks and measure correction burden, execution quality, and plan usage.

## Core rule

Do not decide that one model is 'best.' The goal is a routing policy:

`task characteristics -> cheapest model that reliably achieves the required quality`

## Files
- `PROTOCOL.md` — experiment controls and run procedure
- `QUICKSCREEN_TASKS.md` — frozen Phase 1 prompts
- `SCORECARD.md` — capability + fit rubric
- `RUN_LEDGER.md` — run/evidence log
- `MODEL_ROUTING_HYPOTHESES.md` — pre-registered hypotheses; do not rewrite after seeing results
- `PHASE1_COMPARATIVE_RESULTS.md` — post-hoc objective + provisional Jon-fit analysis and routing interpretation

This is research documentation only. It does not alter HumanOS model routing or production behavior.
