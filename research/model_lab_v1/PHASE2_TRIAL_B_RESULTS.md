# HumanOS Model Lab v1 — Phase 2 Trial B Comparative Results

**Trial:** PDF / Document Creation and Conversation Feel  
**Status:** COMPLETE / OWNER RATINGS PENDING / EFFICIENCY NOT CLEANLY RANKED  
**Frozen brief:** `PHASE2_TRIAL_B_FROZEN_PROMPT.md` v1.0

## Purpose

Test whether model differences show up in a real artifact workflow: first-draft PDF creation, response to identical creative steering, factual/evidence discipline, conversation feel, and visible usage provenance.

## First-draft result

| Rank | Model | Stage 1 known | Signal |
|---:|---|---:|---|
| 1 | GPT-5.6 Sol | **82/85** | Strongest first draft; excellent evidence labeling and data-visualization discipline. |
| 2 | GPT-6 Astra | **80/85** | Strong authored/publication feel and excellent narrative framing. |
| 3 | GPT-5.5 | **77/85** | Strong editorial thought-partner behavior and factual discipline. |
| 4 | GPT-5.6 Terra | **74/85** | Competent, controlled, methodical, but initially flatter and retained an arithmetic defect. |
| 5 | GPT-5.6 Luna | **73/85** | Useful, clear, and practical, but more template-like with factual/workflow defects. |

## Final known result after identical steering

| Rank | Model | Final known | Change from Stage 1* | Main signal |
|---:|---|---:|---:|---|
| 1= | GPT-6 Astra | **89/90** | +9 known points on expanded rubric | Premium authored feel; strongest creative/editorial interpretation. |
| 1= | GPT-5.6 Sol | **89/90** | +7 known points on expanded rubric | Strongest first draft; best evidence discipline; corrected visualization risk during steering. |
| 3 | GPT-5.5 | **86/90** | +9 | Strong benchmark for editorial collaboration and natural reframing. |
| 4 | GPT-5.6 Terra | **82/90** | +8 | Steering improved design substantially, but factual self-correction was incomplete. |
| 5 | GPT-5.6 Luna | **75/90** | +2 | Smaller steering gain; retained factual defects and delivery friction. |

\*Stage 1 is scored out of 85 because steering responsiveness is not yet observable. Stage 2 adds the 5-point steering/correction category; raw arithmetic deltas are therefore descriptive rather than normalized percentage gains.

## Model-by-model interpretation

### GPT-6 Astra
- Best premium/editorial feel in the final artifact review.
- Strong narrative authorship and creative interpretation without unsupported facts.
- Excellent evidence discipline.
- Immediate usage screenshots showed no change, followed by a large delayed block before Luna began; Astra is the strongest likely source, but exact usage is not recoverable from the UI.
- Provisional role: **premium editorial strategist / failure-aware synthesizer**.

### GPT-5.6 Sol
- Strongest first draft in the cohort.
- Excellent at separating measured evidence, interpretation, and provisional decisions.
- Correctly disclosed a truncated chart baseline and accurately handled six-point and one-point score spreads.
- Under steering, replaced a potentially exaggerating Trial A bar visualization with an explicit 89–90 dot scale and added the supplied GPT-5.5 October 2026 transition date.
- Stage 2 same-window raw meter pair: **96/52 -> 92/52 = 4 pp five-hour / 0 pp weekly**.
- Provisional role: **truth-boundary architect / evidence-disciplined editorial synthesizer**.

### GPT-5.5
- Strong natural editorial collaboration and framing.
- Final artifact was polished and factually disciplined.
- Remains a **transitional benchmark only**, not a future routing dependency.
- Raw Stage 2 meter observation: **80/57 -> 71/55 = 9 pp / 2 pp**, preserved as UI telemetry rather than exact compute accounting.

### GPT-5.6 Terra
- Methodical and maintainable design instincts.
- Responded well to explicit creative criticism and materially improved the document.
- Failed to catch its own arithmetic defect: described the 180-to-174 Phase 1 spread as four points rather than six while claiming verification.
- Raw Stage 2 meter observation: **87/58 -> 83/57 = 4 pp / 1 pp**.
- Provisional role remains **ordinary engineering / operational refinement**, not premium editorial lead.

### GPT-5.6 Luna
- Fast, practical, and capable of producing a useful finished artifact.
- Lowest final known artifact score in this trial because it retained a `two-point band` description for a 89–90 result, an ambiguous `2 trial task` tile, and required owner follow-up to surface the PDF.
- Confirmed pre/post displayed usage stayed **55/53 -> 55/53**, including later revision snapshot; this is zero displayed whole-percentage movement, **not zero compute**.
- Provisional role remains **fast bounded execution**, not first-choice premium document author.

## What Trial B actually supports

1. **No universal winner.** Astra and Sol tie on final known quality but win in different ways.
2. **Sol is the strongest first-draft document model in this trial.**
3. **Astra is the strongest premium/editorial interpreter in the final artifact review.**
4. **GPT-5.5 remains a useful behavioral benchmark, but continuing routing must move elsewhere.**
5. **Terra is competent and steerable, but its methodical style did not automatically produce stronger editorial judgment or self-verification.**
6. **Luna is useful for economical bounded execution, but this trial gives evidence against routing premium artifact creation to Luna by default.**
7. **Usage UI telemetry is too delayed, rounded, and reset-sensitive for exact model-cost accounting. Preserve it as provenance, not as token math.**

## Provisional document-routing hypothesis

- **High-stakes / evidence-sensitive executive brief:** Sol first.
- **Premium editorial transformation / broad synthesis:** Astra.
- **Routine or bounded document production where cost/speed dominate:** Luna, with verification when correctness matters.
- **Methodical operational documentation:** Terra.
- **GPT-5.5:** benchmark behavior only while available.

This routing hypothesis is **not adopted** until owner ratings and repeated real-work validation are completed.
