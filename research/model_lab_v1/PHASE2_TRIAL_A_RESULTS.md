# HumanOS Model Lab v1 — Phase 2 Trial A Results

**Trial:** Thought Partner / Problem Framing  
**Status:** ALL MODEL RUNS COMPLETE / OWNER RATINGS PENDING / EFFICIENCY INCOMPLETE

## Known-score result

| Model | Known subtotal /90 | Efficiency | Owner rating | Long-term routing status |
|---|---:|---|---|---|
| GPT-5.5 | **90** | UNKNOWN | Pending | Transitional benchmark only |
| GPT-5.6 Sol | **89** | UNKNOWN | Pending | Continuing candidate |
| GPT-6 Astra | **89** | UNKNOWN | Pending | Continuing candidate |
| GPT-5.6 Luna | **89** | UNKNOWN | Pending | Continuing candidate |
| GPT-5.6 Terra | **89** | UNKNOWN | Pending | Continuing candidate |

The one-point spread is not sufficient to claim a universal winner. Trial A is much more informative as a style/routing discriminator than as a leaderboard.

GPT-5.5 remains useful as a temporary behavioral benchmark because it produced the strongest natural reframing in this trial, but it is leaving ChatGPT in October 2026. HumanOS must therefore preserve the *qualities* that worked rather than create a long-term routing dependency on 5.5.

## Distinctive thought-partner behavior

### GPT-5.5 — collaborative reframer / transitional benchmark
Reframed the problem around the first trustworthy local record of a visible conversation turn. Strongest natural problem-framing and conversational flow in the current scoring. Moved quickly from the invariant to a small durable-journal architecture and a 30-day plan.

**Research use now:** benchmark natural reframing, concise depth, low bureaucracy, and useful challenge. Do not make it a required long-term runtime route.

### GPT-5.6 Sol — truth-boundary architect
Reframed the problem around what HumanOS may truthfully claim it has captured and what durable acknowledgment makes that claim valid. Strongest emphasis on guarantee boundaries, partial/streaming turns, observation gaps, and the distinction between provider success and local evidence.

**Provisional best use:** architecture, authority, provenance, security, and decisions where the exact boundary of a claim matters.

### GPT-6 Astra — edge-case / failure-model expander
Added the strongest treatment of control versus observation, device destruction versus process failure, backups, revisions/regenerations, streaming preservation, and the possibility that asynchronous projection may be unnecessary if the raw store already satisfies the notebook requirement.

**Provisional best use:** high-risk reviews, broad failure analysis, and situations where overlooked edge cases matter enough to justify additional compute.

**Experiment caveat:** the run referenced an earlier preference not present in the frozen prompt, suggesting possible ambient-context contamination. Preserve but do not treat as a strict clean-room result.

### GPT-5.6 Luna — compressed practical synthesizer
Reached essentially the same core architecture with the least ceremony. Framed the decision around the minimum local write that makes a visible turn recoverable, then produced a narrow implementation path, explicit failure states, and measurable tests without expanding scope.

**Provisional best use:** fast practical thinking and implementation planning when the problem is already bounded enough that extensive edge-case exploration is unnecessary.

### GPT-5.6 Terra — methodical state/reconciliation engineer
Reframed the problem around the smallest durability boundary required before HumanOS may call a turn captured. Its most distinctive contribution was an explicit three-stage model: `Captured`, `Projected`, and `Reconciled`. It also emphasized provider adapters as imperfect sources, immutable source events, backup/restore qualification, and privacy/noise tradeoffs around token-level streaming capture.

**Provisional best use:** steady systems planning, state modeling, reconciliation workflows, and maintainable engineering where a conventional, explicit process is preferable to broader exploratory reasoning.

## Comparison of the five answers

All five converged on the same core architecture:

`visible turn -> small synchronous durable local write -> recoverable journal/event record -> asynchronous/rebuildable notebook projection`

The differentiator was not the architecture itself but the lens each model used:

- **GPT-5.5:** What is the real problem and the simplest useful framing?
- **Sol:** Exactly when is a claim true, and where does the guarantee begin/end?
- **Astra:** What failure surface or edge case are we overlooking?
- **Luna:** What is the minimum mechanism that works cleanly and quickly?
- **Terra:** What explicit state model and maintainable process will keep this reliable over time?

## 5.5 succession question

Based on answer content alone, no single continuing model is a drop-in replacement for 5.5's role.

- **Sol** inherits the strongest formal reasoning around truth/authority boundaries.
- **Astra** inherits the strongest broad exploratory/failure-analysis depth.
- **Luna** inherits the strongest low-ceremony practical synthesis.
- **Terra** inherits the strongest steady state/reconciliation process orientation.

A later owner-preference pass can judge conversational similarity separately, but it must not be mixed into answer-quality scoring. The owner's prior comment that Astra *feels* more like GPT-5.5 was deliberately excluded from the numerical score.

## Current routing implication

For thought-partner work, route by the type of uncertainty rather than by a single global winner:

- **Truth, authority, provenance, or guarantee boundary is unclear:** Sol.
- **Failure surface is broad/high-risk and missing an edge case would be costly:** Astra.
- **Problem is mostly understood and a fast, clean decision is needed:** Luna.
- **State transitions, reconciliation, maintainability, or operational process dominate:** Terra.
- **Natural conversational reframing / figuring out the real problem:** GPT-5.5 remains the temporary benchmark; the continuing successor may be a role split rather than one model.

Owner ratings and efficiency evidence are still required before locking the production routing policy.
