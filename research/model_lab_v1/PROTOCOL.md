# HumanOS Model Lab v1 — Protocol

**Experiment ID:** HOS-MLAB-V1
**Status:** SPECIFIED / EXECUTION IN PROGRESS

## Objective
Measure model capability, efficiency, and Jon-fit under controlled prompts, then derive a practical routing policy for HumanOS.

## Surfaces
Prefer the same surface for all compared models. For the initial OpenAI cohort, use Work or Codex when all five models are available there. If a model is unavailable on the same surface, record the surface difference as a confound rather than pretending the comparison is identical.

## Controls
For each task/model pair:
- start a fresh session/thread;
- use the exact frozen task text;
- do not expose another model's answer;
- do not add HumanOS context beyond what the task includes;
- use the same reasoning/effort setting where the surface permits;
- do not use web, plugins, repo browsing, or memory unless the task explicitly permits them;
- preserve the full raw answer before scoring;
- record model, surface, effort, start/end time, and any visible usage change;
- do not edit a model answer before preservation.

## Raw telemetry provenance rule

Visible usage readings are evidence even when they are delayed, rounded, contaminated by another run, or later shown to be poor causal attribution.

For every usage observation:
- preserve the exact displayed values and approximate timestamp;
- preserve the screenshot or its hash/reference when practical;
- never overwrite or delete a raw reading because later interpretation changes;
- record raw **observed delta** separately from **causal attribution**;
- if attribution is uncertain, label it `UNKNOWN`, `MIXED`, or `CONTAMINATED` rather than erasing the observation;
- a later meter drop may revise attribution confidence, but must not revise history about what the UI showed earlier.

Canonical raw meter timeline: `RAW_USAGE_OBSERVATIONS.md`.

## Order
To reduce expectation bias, rotate model order between tasks rather than always running strongest-to-weakest. Suggested Phase 1 order:
- Task 1: Luna -> 5.5 -> Sol -> Terra -> Astra
- Task 2: Terra -> Astra -> Luna -> Sol -> 5.5
- Task 3: 5.5 -> Luna -> Astra -> Terra -> Sol

## Output limits
The Quick Screen deliberately asks for bounded outputs. A model that ignores a clear length constraint loses instruction-following points. Do not ask models to be more verbose after the first answer.

## Scoring sequence
1. Freeze all raw answers for a task.
2. Blind model identity if practical.
3. Score objective/task-specific criteria first.
4. Jon scores working fit separately, before seeing aggregate rankings.
5. Record time and plan usage separately from quality.
6. Only then compare models.

## Metrics
### Capability
- correctness / factual fidelity
- task completion
- instruction following
- reasoning quality visible in the answer
- error detection
- prioritization
- calibration / uncertainty

### Efficiency
- wall-clock time
- visible plan usage delta when measurable
- answer length
- number of follow-up corrections needed
- retries required

### Jon-fit
- understands intent quickly
- concise without becoming shallow
- decisive when evidence supports a decision
- challenges bad assumptions without derailing
- avoids unnecessary bureaucracy/overengineering
- useful initiative
- natural conversational feel
- produces something Jon would actually use

## Stop rules
Stop a run if the model gains access to another participant's answer, uses an unauthorized tool, or receives materially different context. Mark the run contaminated and rerun fresh.

A contaminated **quality** run may require rerun. Contaminated **telemetry** does not get deleted: preserve the raw observation and mark attribution uncertainty.

## Interpretation rule
A model may win one role and lose another. The desired output is not a global rank; it is a task-routing matrix.

## Evidence status
A completed UI response without raw preservation is OBSERVED, not FROZEN. A preserved raw answer plus metadata is RAW FROZEN. A scored result is SCORED. A routing recommendation becomes ADOPTED only after repeated real-work validation.
