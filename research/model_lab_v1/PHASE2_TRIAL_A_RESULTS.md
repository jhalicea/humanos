# HumanOS Model Lab v1 — Phase 2 Trial A Results

**Trial:** Thought Partner / Problem Framing  
**Status:** MODEL RUNS COMPLETE / OWNER RATINGS PENDING / EFFICIENCY INCOMPLETE

## Known-score result

| Model | Known subtotal /90 | Efficiency | Owner rating |
|---|---:|---|---|
| GPT-5.5 | **90** | UNKNOWN | Pending |
| GPT-5.6 Sol | **89** | UNKNOWN | Pending |
| GPT-6 Astra | **89** | UNKNOWN | Pending |
| GPT-5.6 Luna | **89** | UNKNOWN | Pending |

The one-point spread is not sufficient to claim a universal winner. Trial A is more informative as a style/routing discriminator than as a leaderboard.

## Distinctive thought-partner behavior

### GPT-5.5 — collaborative reframer
Reframed the problem around the first trustworthy local record of a visible conversation turn. Strongest natural problem-framing and conversational flow in the current scoring. Moved quickly from the invariant to a small durable-journal architecture and a 30-day plan.

**Provisional best use:** ambiguous problems where the owner wants to think through what the real problem is before formalizing architecture.

### GPT-5.6 Sol — truth-boundary architect
Reframed the problem around what HumanOS may truthfully claim it has captured and what durable acknowledgment makes that claim valid. Strongest emphasis on guarantee boundaries, partial/streaming turns, observation gaps, and the distinction between provider success and local evidence.

**Provisional best use:** architecture, authority, provenance, security, and decisions where the exact boundary of a claim matters.

### GPT-6 Astra — edge-case / failure-model expander
Added the strongest treatment of control versus observation, device destruction versus process failure, backups, revisions/regenerations, streaming preservation, and the possibility that asynchronous projection may be unnecessary if the raw store already satisfies the notebook requirement.

**Provisional best use:** high-risk reviews, wide failure analysis, and situations where overlooked edge cases matter enough to justify additional compute.

**Experiment caveat:** the run referenced an earlier preference not present in the frozen prompt, suggesting possible ambient-context contamination. Preserve but do not treat as a strict clean-room result.

### GPT-5.6 Luna — compressed practical synthesizer
Reached essentially the same core architecture with the least ceremony. Framed the decision around the minimum local write that makes a visible turn recoverable, then produced a narrow implementation path, explicit failure states, and measurable tests without expanding scope.

**Provisional best use:** fast practical thinking and implementation planning when the problem is already bounded enough that extensive edge-case exploration is unnecessary.

## Current routing implication

For thought-partner work, routing should depend on the kind of uncertainty:

- **Problem itself is unclear / owner wants to think aloud:** GPT-5.5
- **Truth, authority, provenance, or guarantee boundary is unclear:** Sol
- **Failure surface is broad/high-risk and missing an edge case would be costly:** Astra
- **Problem is mostly understood and a fast, clean decision is needed:** Luna

This is a working hypothesis only. Owner ratings and efficiency evidence are still required before locking the role routing policy.
