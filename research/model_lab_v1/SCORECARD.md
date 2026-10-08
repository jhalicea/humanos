# HumanOS Model Lab v1 — Scorecard

Score each task independently before comparing models.

## Objective score — 60 points

### Task completion — 20
- 20: all explicit requirements satisfied
- 15: one minor miss
- 10: material omission but still useful
- 5: major requirements missed
- 0: failed/refused/unusable

### Correctness and evidence discipline — 15
- 15: no unsupported claims; observation/inference clearly separated when relevant
- 10: small unsupported or imprecise claim
- 5: several material assumptions
- 0: fabricates or contradicts supplied evidence

### Judgment / prioritization — 10
- 10: identifies the actual decision and prioritizes well
- 7: mostly sound but diluted
- 4: generic or poorly prioritized
- 0: avoids the decision

### Instruction following — 10
- 10: format, length, and constraints followed
- 7: minor deviations
- 4: material deviations
- 0: largely ignores requested format

### Calibration — 5
- 5: confidence matches evidence; unknowns preserved
- 3: slight over/under-confidence
- 0: false certainty or excessive evasiveness

## Jon-fit score — 30 points
Rate each 0–5:
- understands intent quickly
- concise but not shallow
- decisive and useful
- challenges assumptions appropriately
- low bureaucracy / low overengineering
- natural working feel

## Efficiency score — 10 points
This score is comparative within a task.
- 4: wall-clock speed
- 3: visible plan-usage efficiency
- 2: correction burden / retries
- 1: output economy

If plan usage cannot be measured cleanly, mark that component UNKNOWN instead of guessing and normalize only among known components.

## Total
**100 points maximum**

Also record a qualitative role verdict:
- WORKER
- GENERAL ENGINEER
- ARCHITECT / REVIEWER
- LONG-HORIZON SPECIALIST
- NOT PREFERRED

A model can receive more than one role, but every role assignment must point to observed evidence.