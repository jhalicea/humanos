# HumanOS Model Lab v1 — Run Ledger

**Status:** PHASE 1 COMPLETE / PHASE 2 IN PROGRESS / TRIAL A COMPLETE / TRIAL B TERRA + GPT-5.5 + ASTRA COMPLETE / LUNA STAGE 1 SCORED + STAGE 2 ARTIFACT RECEIVED / RAW USAGE PROVENANCE PRESERVED / PRE-LUNA BASELINE CONFIRMED

## Phase 1

| Run ID | Task | Model | Surface | Effort | Raw preserved | Score | Notes |
|---|---|---|---|---|---|---|---|
| MLAB-P1-T1-LUNA | 1 | GPT-5.6 Luna | Work | Light | Yes | Objective 60/60; total pending | First-pass accepted; comparative fit scored separately |
| MLAB-P1-T1-55 | 1 | GPT-5.5 | TBD | TBD | Yes | Objective 60/60; total pending | Raw frozen; model identity follows frozen sequence; surface/effort not independently verified |
| MLAB-P1-T1-SOL | 1 | GPT-5.6 Sol | TBD | TBD | Yes | Objective 60/60; total pending | Raw frozen and scored; surface/effort not independently verified |
| MLAB-P1-T2-TERRA | 2 | GPT-5.6 Terra | Work | Light | Yes | Objective 59/60; total pending | Strong architectural judgment; minor deduction for composite revisit trigger with unspecified SLO threshold |
| MLAB-P1-T2-ASTRA | 2 | GPT-6 Astra | TBD | TBD | Yes | Objective 60/60; total pending | Strong staged plan and cleaner single measurable revisit trigger; model identity follows frozen sequence |
| MLAB-P1-T2-LUNA | 2 | GPT-5.6 Luna | Work | Light | Yes | Objective 59/60; total pending | Strong compact architecture judgment; quantified trigger mixes performance/reliability predicates and leaves 3× improvement dimension implicit |
| MLAB-P1-T2-SOL | 2 | GPT-5.6 Sol | TBD | TBD | Yes | Objective 60/60; total pending | Strong authority-boundary reasoning; single causal, reproducible migration trigger |
| MLAB-P1-T2-55 | 2 | GPT-5.5 | TBD | TBD | Yes | Objective 59/60; total pending | Strong trusted-surface framing; trigger is quantified but uses undefined “production-relevant” and weaker “plausibly prevented” causal bar |
| MLAB-P1-T3-55 | 3 | GPT-5.5 | TBD | TBD | Yes | Objective 55/60; total pending | Excellent real-build scoping and Jon-fit signals; acceptance-test counting is ambiguous/inconsistent |
| MLAB-P1-T3-LUNA | 3 | GPT-5.6 Luna | Work | Light | Yes | Objective 60/60; total pending | Strong implementation-forward plan; coherent acceptance test |
| MLAB-P1-T3-ASTRA | 3 | GPT-6 Astra | TBD | TBD | Yes | Objective 60/60; total pending | Strong scope discipline; clean replay/failure acceptance test |
| MLAB-P1-T3-TERRA | 3 | GPT-5.6 Terra | TBD | TBD | Yes | Objective 55/60; total pending | Strong narrow polling-first plan and evidence discipline |
| MLAB-P1-T3-SOL | 3 | GPT-5.6 Sol | TBD | TBD | Yes | Objective 55/60; total pending | Strong unified idempotent intake path and evidence discipline |

See `PHASE1_COMPARATIVE_RESULTS.md` for holistic provisional Jon-fit scoring, combined known-quality subtotals, and post-hoc routing interpretation.

## Phase 2 — Trial A: Thought Partner

| Run ID | Model | Raw preserved | Known score | Efficiency | Owner rating | Notes |
|---|---|---|---|---|---|---|
| MLAB-P2-A-55 | GPT-5.5 | Yes | 90/90 known | UNKNOWN | Pending | Transitional benchmark; strongest collaborative reframing in this trial. |
| MLAB-P2-A-SOL | GPT-5.6 Sol | Yes | 89/90 known | UNKNOWN | Pending | Strong truth/acknowledgment boundary reasoning. |
| MLAB-P2-A-ASTRA | GPT-6 Astra | Yes | 89/90 known | UNKNOWN | Pending | Strong failure-model expansion; possible ambient-context contamination noted. |
| MLAB-P2-A-LUNA | GPT-5.6 Luna | Yes | 89/90 known | UNKNOWN | Pending | Fast practical synthesis with low ceremony. |
| MLAB-P2-A-TERRA | GPT-5.6 Terra | Yes | 89/90 known | UNKNOWN | Pending | Strong operational state/reconciliation framing. |

## Phase 2 — Trial B: PDF / Document Creation and Conversation Feel

Frozen prompt: `PHASE2_TRIAL_B_FROZEN_PROMPT.md` v1.0.

| Run ID | Model | Stage 1 artifact preserved | Stage 2 artifact preserved | Surface | Effort | Efficiency evidence | Score | Owner rating | Notes |
|---|---|---|---|---|---|---|---|---|---|
| MLAB-P2-B-TERRA | GPT-5.6 Terra | Yes | Yes | Work | Light | **Raw Stage 2 observed: 4 pp 5-hour + 1 pp weekly**; attribution originally strong but later meter-lag discovery reduces confidence in exact compute attribution | **82/90 known; efficiency pending** | Pending | Stage 2 materially improved editorial storytelling and layout. Persistent quantitative defect remains: page 3 says four-point range although 180→174 spans six points. Stage 1 SHA `78cf683b...`; Stage 2 SHA `6c984ed6...`. |
| MLAB-P2-B-55 | GPT-5.5 | Yes | Yes | Work | Light | **Raw Stage 2 observed: 9 pp 5-hour + 2 pp weekly**; preserved as UI telemetry, not token accounting | **86/90 known; efficiency pending** | Pending | Strong authored brief, correct quantitative values, strong uncertainty handling, no detected range defect. Stage 1 SHA `3cbaa2e4...`; Stage 2 SHA `c4a5fa9a...`. GPT-5.5 remains a transitional benchmark only. |
| MLAB-P2-B-ASTRA | GPT-6 Astra | Yes | Yes | Work | Light | **Immediate Stage 1/2: 0/0 visible; later PRE-LUNA screenshot: 71/55 -> 55/53 = 16/2 delayed block before Luna began. Astra is strongest likely source; exact decomposition unavailable.** | **89/90 known; efficiency pending** | Pending | Strongest revised artifact so far. Preserve both immediate zero-movement screenshots and delayed pre-Luna block. Luna is ruled out as cause of that visible 16/2 drop. Stage 1 SHA `bc5e0e2e...`; Stage 2 SHA `6bf4d2c5...`. |
| MLAB-P2-B-LUNA | GPT-5.6 Luna | Yes | **Received / scoring pending** | Work | Light | **Confirmed Stage 1 visible pre/post: 55/53 -> 55/53 = 0/0. Later revised-artifact snapshot also 55/53. Do not interpret as zero compute.** | **Stage 1: 73/85 known; Stage 2 pending** | Pending | Clean six-page brief, but repeated `two-point band` wording conflicts with source's one-point Trial A spread; page-1 `2 trial task` tile is ambiguous. Initial response did not surface the PDF; owner had to ask, then received a local `/Users/...` path. Stage 2 artifact receipt SHA `f36f69dd...`. |
| MLAB-P2-B-SOL | GPT-5.6 Sol | No | No | Work planned | Light planned | Pending | Pending | Pending | Durable continuing-model crossover. |

## Raw usage provenance

Canonical raw timeline: `RAW_USAGE_OBSERVATIONS.md`.

**Rule:** never erase a meter reading because it later appears delayed, contaminated, or incorrectly attributed. Preserve the displayed value and timestamp as observed evidence. Store causal interpretation separately and allow that interpretation to change.

Current important lesson: the Work plan meter has demonstrated delayed posting. Astra showed no immediate visible movement after controlled runs, but a later **pre-Luna** screenshot already showed 55/53. Therefore the 16 pp / 2 pp visible drop from the last immediate Astra reading occurred before Luna began. Luna's confirmed Stage 1 visible interval is 55/53 -> 55/53.

UI percentages must not be converted to tokens or compute.

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
- **every visible usage reading, even if later judged contaminated**
- raw observed usage delta
- causal attribution confidence / confounds
- visible subagent behavior when relevant
- contamination/tool-use notes
- scorer notes
- owner rating

## Freeze rule
Never replace a raw answer, artifact, screenshot reading, or telemetry observation. Corrections, reruns, reinterpretations, and rescoring get new records or annotations.
