# HumanOS Model Lab v1 — Run Ledger

**Status:** PHASE 1 COMPLETE / PHASE 2 IN PROGRESS / TRIAL A COMPLETE / TRIAL B TERRA COMPLETE EXCEPT EFFICIENCY DELTA / EFFICIENCY INCOMPLETE

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

## Phase 2 — Trial A: Thought Partner

| Run ID | Model | Raw preserved | Known score | Efficiency | Owner rating | Notes |
|---|---|---|---|---|---|---|
| MLAB-P2-A-55 | GPT-5.5 | Yes | 90/90 known | UNKNOWN | Pending | Transitional benchmark; strongest collaborative reframing in this trial. |
| MLAB-P2-A-SOL | GPT-5.6 Sol | Yes | 89/90 known | UNKNOWN | Pending | Strong truth/acknowledgment boundary reasoning. |
| MLAB-P2-A-ASTRA | GPT-6 Astra | Yes | 89/90 known | UNKNOWN | Pending | Strong failure-model expansion; possible ambient-context contamination noted. |
| MLAB-P2-A-LUNA | GPT-5.6 Luna | Yes | 89/90 known | UNKNOWN | Pending | Fast practical synthesis with low ceremony. |
| MLAB-P2-A-TERRA | GPT-5.6 Terra | Yes | 89/90 known | UNKNOWN | Pending | Strong operational state/reconciliation framing. Owner comment about Astra resembling 5.5 was not used in scoring. |

## Phase 2 — Trial B: PDF / Document Creation and Conversation Feel

Frozen prompt: `PHASE2_TRIAL_B_FROZEN_PROMPT.md` v1.0.

| Run ID | Model | Stage 1 artifact preserved | Stage 2 artifact preserved | Surface | Effort | Efficiency | Score | Owner rating | Notes |
|---|---|---|---|---|---|---|---|---|---|
| MLAB-P2-B-TERRA | GPT-5.6 Terra | Yes | Yes | Work | Light | Baseline captured; delta pending | **82/90 known; efficiency pending** | Pending | Stage 2 materially improved editorial storytelling and layout. Persistent quantitative defect remains: page 3 says four-point range although 180→174 spans six points. Pre-Stage-2 usage: 87% left (5-hour), 58% left (weekly). Stage 1 SHA `78cf683b...`; Stage 2 SHA `6c984ed6...`. |
| MLAB-P2-B-55 | GPT-5.5 | No | No | Work planned | Light planned | Pending | Pending | Pending | Transitional benchmark only; not a long-term routing dependency. |
| MLAB-P2-B-ASTRA | GPT-6 Astra | No | No | Work planned | Light planned | Pending | Pending | Pending | Tests whether extra depth improves editorial/artifact quality enough to justify usage. |
| MLAB-P2-B-LUNA | GPT-5.6 Luna | No | No | Work planned | Light planned | Pending | Pending | Pending | Tests speed/value on a real artifact task. |
| MLAB-P2-B-SOL | GPT-5.6 Sol | No | No | Work planned | Light planned | Pending | Pending | Pending | Durable continuing-model crossover. |

Efficiency remains incomplete whenever wall-clock and visible plan-usage evidence are unavailable. Do not invent efficiency.

## Continuity rule

Retiring models may remain as benchmark evidence, but HumanOS routing decisions must identify a continuing successor model or a deliberate role split across continuing models.

## Per-run metadata
Record:
- run ID
- date/time
- exact model label shown by product
- surface (Work, Codex, other)
- reasoning/effort setting
- speed mode when available
- raw response file or attachment
- first artifact reference
- revised artifact reference
- start/end or elapsed time
- visible usage before/after if available
- visible subagent behavior when relevant
- contamination/tool-use notes
- scorer notes
- owner rating

## Freeze rule
Never replace a raw answer or artifact. Corrections, reruns, and rescoring get new records.