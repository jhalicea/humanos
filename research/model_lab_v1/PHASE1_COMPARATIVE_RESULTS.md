# HumanOS Model Lab v1 — Phase 1 Comparative Results

**Status:** PHASE 1 OBJECTIVE COMPLETE / OWNER PREFERENCE RECORDED / EFFICIENCY INCOMPLETE

This document is post-hoc analysis. It does not modify the pre-registered hypotheses in `MODEL_ROUTING_HYPOTHESES.md`.

## Method

Objective scores come from the frozen three-task Quick Screen. Jon-fit is scored holistically across each model's three raw responses using the frozen six-dimension rubric in `SCORECARD.md`.

The `natural working feel` dimension began as an assistant estimate. Jon has now supplied qualitative owner feedback. Because he expressed task-dependent preferences rather than exact 0–5 ratings, the numerical Jon-fit table remains provisional; the owner feedback below takes precedence over any simplistic global ranking.

Efficiency is not ranked yet because wall-clock and visible plan-usage data were not captured consistently across the cohort.

## Objective result

| Model | Task 1 | Task 2 | Task 3 | Objective total | Objective average /60 |
|---|---:|---:|---:|---:|---:|
| GPT-6 Astra | 60 | 60 | 60 | 180/180 | 60.00 |
| GPT-5.6 Luna | 60 | 59 | 60 | 179/180 | 59.67 |
| GPT-5.6 Sol | 60 | 60 | 55 | 175/180 | 58.33 |
| GPT-5.6 Terra | 60 | 59 | 55 | 174/180 | 58.00 |
| GPT-5.5 | 60 | 59 | 55 | 174/180 | 58.00 |

## Provisional Jon-fit scoring

Dimensions are 0–5 each: understands intent quickly; concise but not shallow; decisive and useful; challenges assumptions appropriately; low bureaucracy / low overengineering; natural working feel.

| Model | Intent | Concise | Decisive | Challenges assumptions | Low bureaucracy | Natural feel* | Jon-fit /30 |
|---|---:|---:|---:|---:|---:|---:|---:|
| GPT-5.5 | 5 | 5 | 5 | 5 | 5 | 5 | **30** |
| GPT-6 Astra | 5 | 4 | 5 | 5 | 5 | 4 | **28** |
| GPT-5.6 Sol | 5 | 5 | 5 | 5 | 4 | 4 | **28** |
| GPT-5.6 Luna | 5 | 5 | 5 | 4 | 4 | 4 | **27** |
| GPT-5.6 Terra | 5 | 5 | 5 | 4 | 5 | 3 | **27** |

\* provisional numerical estimate; owner qualitative feedback below supersedes a forced one-dimensional ranking.

## Owner feedback — 2026-09-15

Jon reported that he had not previously paid close attention to model differences and only noticed them after deliberately comparing how they reason and converse.

His preference is **task-dependent rather than a single ranking**:

- For **thinking through problems**, he especially likes **GPT-5.5, GPT-6 Astra, and GPT-5.6 Sol**.
- He likes **GPT-5.6 Luna** because it is fast, inexpensive in relative plan usage, and still produces very good work.
- **GPT-5.6 Terra** is currently his least-preferred conversational fit; he experiences it as comparatively dry and less aligned with the way he likes to think and converse.

Interpretation: Jon appears to value different model personalities for different cognitive modes. He does not want one universal favorite. The routing policy should preserve those modes instead of collapsing them into a single leaderboard.

This owner feedback strengthens H6 (no global winner) and H7 (working fit matters independently of benchmark correctness). It also clarifies H4: the perceived difference in GPT-5.5 is not merely capability; conversational framing and problem exploration materially affect preference.

## Evidence by model

### GPT-5.5 — strongest collaborative framing signal

Observed pattern: frames the real problem quickly, uses natural-language boundaries, and often names the anti-pattern before prescribing the build. In Task 2 it reframed the language debate around the trusted surface and warned against Rust being added decoratively. In Task 3 it immediately narrowed scope with the equivalent of: not a full email client, not an inbox-managing agent, one narrow intake capability. Jon specifically identifies 5.5 as one of the models he likes when thinking through problems.

Weakness: polished framing can hide specification defects. Task 3's acceptance-test arithmetic was ambiguous. This is an important reason not to equate natural working feel with objective correctness.

Provisional role signal: **GENERAL ENGINEER / COLLABORATOR / THINKING PARTNER**.

### GPT-6 Astra — strongest disciplined senior-review behavior

Observed pattern: consistently narrows the problem, turns reliability claims into proof obligations, and distinguishes demonstrated evidence from proposed capability. In Task 2 it required independently reproduced high-severity failures and regression proof before migration. In Task 3 it explicitly separated a local webhook demonstration from evidence of live provider delivery and deferred n8n/agents until intake reliability existed. Jon also identifies Astra as a preferred model for thinking through problems.

Weakness: more formal and review-oriented than conversational; can feel heavier than necessary for ordinary work.

Provisional role signal: **ARCHITECT / REVIEWER / LONG-HORIZON SPECIALIST / THINKING PARTNER**.

### GPT-5.6 Sol — strongest authority-boundary reasoning

Observed pattern: good at identifying what a technology change cannot solve. In Task 2 it separated Rust's memory/concurrency safety from authorization, transaction correctness, and model authority. In Task 3 it preserved a single idempotent intake path and explicitly ended by distinguishing a proposed plan from evidence that the capability exists. Jon also identifies Sol as a preferred model for thinking through problems.

Weakness: sometimes expands scope more than necessary and, in Task 3, missed the acceptance-fixture ambiguity.

Provisional role signal: **ARCHITECT / REVIEWER / GENERAL ENGINEER / THINKING PARTNER**.

### GPT-5.6 Luna — much stronger engineer than the initial worker hypothesis predicted

Observed pattern: compact, implementation-forward, and technically credible. It tied together webhook, polling, auth, idempotency, retries, queue behavior, n8n, and bounded agent authority while still producing a coherent acceptance test. Task 2 was only one point behind the strongest architecture answers. Jon specifically values Luna for speed, economy, and consistently strong output.

Weakness: tends to satisfy the requested technology list aggressively instead of pruning scope. Its Task 3 plan risks doing too much in seven days.

Provisional role signal: **WORKER / GENERAL ENGINEER / FAST DEFAULT**.

### GPT-5.6 Terra — methodical balanced engineer, weaker conversational fit for Jon

Observed pattern: practical sequencing, observability, polling-first design, cursor safety, and evidence-aware live-vs-mock distinctions. It is less likely than Luna to rush into extra components and less formal than Astra.

Weakness: fewer distinctive high-level reframes, its Task 3 acceptance accounting was ambiguous, and Jon currently experiences its conversational style as comparatively dry and less aligned with how he likes to think.

Provisional role signal: **GENERAL ENGINEER / SECONDARY OPTION**.

## Combined known-quality view

To avoid pretending efficiency is known, combine only objective average (/60) and provisional Jon-fit (/30). This is a /90 known-quality subtotal, not a final score. Because Jon's owner feedback is task-dependent rather than numerical, this table should not be interpreted as his personal preference ranking.

| Model | Objective avg /60 | Provisional Jon-fit /30 | Known-quality subtotal /90 |
|---|---:|---:|---:|
| GPT-6 Astra | 60.00 | 28 | **88.00** |
| GPT-5.5 | 58.00 | 30 | **88.00** |
| GPT-5.6 Luna | 59.67 | 27 | **86.67** |
| GPT-5.6 Sol | 58.33 | 28 | **86.33** |
| GPT-5.6 Terra | 58.00 | 27 | **85.00** |

The tie between Astra and GPT-5.5 is informative rather than contradictory: Astra earned its position through objective rigor; GPT-5.5 earned it through unusually strong working-style fit. Jon's qualitative feedback further suggests that Sol belongs in the same preferred 'thinking partner' group despite its lower quick-screen subtotal.

## What Phase 1 changed

- H1 Luna: **partially contradicted.** Luna was not merely a cheap worker; it performed near the top on architecture and tied Astra on Task 3 objective quality.
- H2 Terra: **plausible technically, weaker on owner conversational fit.** Terra behaved like a balanced engineer, but Jon currently finds it dry and less preferred conversationally; Phase 1 also contains no reliable cost/usage comparison.
- H3 Sol: **partially supported.** Sol showed strong architecture and authority reasoning and is one of Jon's preferred models for thinking through problems, but it did not dominate the quick screen.
- H4 GPT-5.5: **supported.** Its response style is behaviorally distinct, especially in framing, scope language, conversational problem definition, and owner preference for problem-thinking.
- H5 Astra: **supported on rigor, not exclusivity.** Astra was the only model with a perfect objective 180/180 and is also one of Jon's preferred models for thinking through problems, but Luna was extremely close objectively.
- H6 No global winner: **strongly supported and owner-confirmed.** Jon explicitly likes different models in different ways.
- H7 Jon-fit independent of correctness: **strongly supported and owner-confirmed.** Terra's technically solid performance does not translate into preferred conversational fit, while 5.5/Sol/Astra are favored for problem-thinking.

## Current routing hypothesis after Phase 1

This is a post-hoc working hypothesis, not production routing:

- **Luna:** default high-volume worker, quick implementation, first-pass general engineer, and cost-sensitive work.
- **Terra:** secondary balanced engineer when its style is acceptable or when a neutral/methodical response is useful; not Jon's default conversational model.
- **Sol:** architecture, security, authority-boundary review, and interactive problem-thinking.
- **GPT-5.5:** collaborative planning, framing, teaching, exploratory reasoning, and work where natural interaction quality matters; preserve extra verification because polished prose can mask small specification errors.
- **Astra:** highest-risk review, proof obligations, difficult architecture, failure analysis, long-horizon tasks, and deep problem-thinking.

A better mental model is not 'best to worst' but:

`thinking mode -> 5.5 / Sol / Astra`

`fast execution mode -> Luna`

`neutral secondary engineering mode -> Terra`

## Next experiment

Phase 2 should stop asking all models the same easy tasks. Give each model role-matched work, then include one deliberate cross-over challenge to test the routing hypothesis. Capture wall-clock time and visible plan usage before/after every run so efficiency becomes measurable.
