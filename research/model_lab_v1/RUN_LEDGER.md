# HumanOS Model Lab v1 — Run Ledger

**Status:** PHASE 1 COMPLETE / PHASE 2 IN PROGRESS / 3 ROLE RUNS SCORED / EFFICIENCY INCOMPLETE

## Phase 1

| Run ID | Task | Model | Surface | Effort | Raw preserved | Score | Notes |
|---|---|---|---|---|---|---|---|
| MLAB-P1-T1-LUNA | 1 | GPT-5.6 Luna | Work | Light | Yes | Objective 60/60; total pending | First-pass accepted; comparative fit scored separately |
| MLAB-P1-T1-55 | 1 | GPT-5.5 | TBD | TBD | Yes | Objective 60/60; total pending | Raw frozen; model identity follows frozen sequence; surface/effort not independently verified |
| MLAB-P1-T1-SOL | 1 | GPT-5.6 Sol | TBD | TBD | Yes | Objective 60/60; total pending | Raw frozen and scored; surface/effort not independently verified |
| MLAB-P1-T1-TERRA | 1 | GPT-5.6 Terra | TBD | TBD | Yes | Objective 60/60; total pending | User corrected model identity to Terra; ingestion was briefly mislabeled Sol, then corrected before scoring |
| MLAB-P1-T1-ASTRA | 1 | GPT-6 Astra | TBD | TBD | Yes | Objective 60/60; total pending | Raw frozen and scored; Task 1 ceiling reached across all five models |
| MLAB-P1-T2-TERRA | 2 | GPT-5.6 Terra | Work | Light | Yes | Objective 59/60; total pending | Strong architectural judgment; minor deduction for composite revisit trigger with unspecified SLO threshold |
| MLAB-P1-T2-ASTRA | 2 | GPT-6 Astra | TBD | TBD | Yes | Objective 60/60; total pending | Strong staged plan and cleaner single measurable revisit trigger; model identity follows frozen sequence |
| MLAB-P1-T2-LUNA | 2 | GPT-5.6 Luna | Work | Light | Yes | Objective 59/60; total pending | Strong compact architecture judgment; quantified trigger mixes performance/reliability predicates and leaves 3× improvement dimension implicit |
| MLAB-P1-T2-SOL | 2 | GPT-5.6 Sol | TBD | TBD | Yes | Objective 60/60; total pending | Strong authority-boundary reasoning; single causal, reproducible migration trigger |
| MLAB-P1-T2-55 | 2 | GPT-5.5 | TBD | TBD | Yes | Objective 59/60; total pending | Strong trusted-surface framing; trigger is quantified but uses undefined “production-relevant” and weaker “plausibly prevented” causal bar |
| MLAB-P1-T3-55 | 3 | GPT-5.5 | TBD | TBD | Yes | Objective 55/60; total pending | Excellent real-build scoping and Jon-fit signals; acceptance-test counting is ambiguous/inconsistent (10 items, 2 duplicates, 1 malformed -> expected 8 not unambiguously supported) |
| MLAB-P1-T3-LUNA | 3 | GPT-5.6 Luna | Work | Light | Yes | Objective 60/60; total pending | Strong implementation-forward plan; coherent acceptance test; breadth/scope pressure flagged for comparative Jon-fit review |
| MLAB-P1-T3-ASTRA | 3 | GPT-6 Astra | TBD | TBD | Yes | Objective 60/60; total pending | Strong scope discipline; defers n8n/agents until intake is reliable; clean replay/failure acceptance test |
| MLAB-P1-T3-TERRA | 3 | GPT-5.6 Terra | TBD | TBD | Yes | Objective 55/60; total pending | Strong narrow polling-first plan and evidence discipline; acceptance-test first-run accounting is ambiguous around 16 valid items plus 2 transient failures |
| MLAB-P1-T3-SOL | 3 | GPT-5.6 Sol | TBD | TBD | Yes | Objective 55/60; total pending | Strong unified idempotent intake path and evidence discipline; acceptance-test fixture count is ambiguous (10 items, 2 duplicates, 1 malformed -> expected 8 not unambiguously supported) |

See `PHASE1_COMPARATIVE_RESULTS.md` for holistic provisional Jon-fit scoring, combined known-quality subtotals, and post-hoc routing interpretation.

## Phase 2 — Role Trials

| Run ID | Trial | Model | Surface | Effort | Raw preserved | Known score | Efficiency | Owner rating | Notes |
|---|---|---|---|---|---|---|---|---|---|
| MLAB-P2-A-55 | A — Thought Partner | GPT-5.5 | TBD | TBD | Yes | 90/90 known | UNKNOWN | Pending | Excellent reframing around first trustworthy local record; concrete 30-day plan; no clarification needed |
| MLAB-P2-A-SOL | A — Thought Partner | GPT-5.6 Sol | TBD | TBD | Yes | 89/90 known | UNKNOWN | Pending | Strongest acknowledgment-boundary framing so far; explicitly narrows the zero-loss guarantee to post-observation/post-commit events and handles partial turns/gaps |
| MLAB-P2-A-ASTRA | A — Thought Partner | GPT-6 Astra | TBD | TBD | Yes | 89/90 known | UNKNOWN | Pending | Strong control-vs-observation framing; surfaced streaming, revisions, device-loss, backup/restore, and synchronous-durability details. End-state usage snapshot present but no baseline. Ambient-context contamination possible from reference to an earlier preference not in frozen prompt |
| MLAB-P2-A-LUNA | A — Thought Partner | GPT-5.6 Luna | TBD | TBD | No | Pending | UNKNOWN | Pending | |

Efficiency remains incomplete when wall-clock and visible plan-usage evidence are unavailable. Do not publish a final /100 role score until the efficiency component is measured or explicitly normalized under the experiment rules.

## Per-run metadata
Record:
- run ID
- date/time
- exact model label shown by product
- surface (Work, Codex, other)
- reasoning/effort setting
- speed mode when available
- raw response file or attachment
- start/end or elapsed time
- visible usage before/after if available
- visible subagent behavior when relevant
- contamination/tool-use notes
- scorer notes
- owner rating

## Freeze rule
Never replace a raw answer. Corrections, reruns, and rescoring get new records.
