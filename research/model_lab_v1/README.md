# HumanOS Model Lab v1

**Status:** IMPLEMENTED RESEARCH HARNESS / NOT YET RUN

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
Three short, bounded tasks. Run the exact same prompts in fresh sessions for all available models. No web, repository inspection, memory, or tools unless the task explicitly allows them.

### Phase 2 — Role Trials
Only after Phase 1. Give models tasks matched to likely roles: worker, engineer, architect/reviewer, and long-horizon specialist.

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

This is research documentation only. It does not alter HumanOS model routing or production behavior.