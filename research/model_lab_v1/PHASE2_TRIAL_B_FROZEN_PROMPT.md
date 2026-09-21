# HumanOS Model Lab v1 — Phase 2 Trial B Frozen Prompt

**Trial:** PDF / Document Creation and Conversation Feel  
**Version:** 1.0 — FROZEN  
**Status:** READY TO RUN

## Experimental purpose

Determine which model produces the best combination of finished document quality and collaborative creative feel. Use the same source packet, same initial prompt, and same steering turn for every model.

Do not modify this prompt after the first run. Any material change requires v1.1 and preservation of v1.0.

## Run controls

- Fresh Work thread for each model where possible.
- Same effort/reasoning setting and normal/default speed where available.
- Do not tell the model how previous models performed.
- Do not tell the model the owner currently prefers or dislikes any model.
- Record model label, surface, effort, speed, start/end time, and visible plan usage before/after.
- Preserve the first artifact and first visible response before issuing the steering turn.
- Preserve the revised artifact and the model's revision response.

## Stage 1 — frozen initial prompt

```text
Create a finished, polished PDF executive brief from ONLY the source packet below.

Do not browse the web. Do not use outside HumanOS knowledge, memory, prior conversations, or unstated facts. If something is not in the source packet, do not invent it.

AUDIENCE
A technically literate founder/owner who wants to understand the experiment quickly without reading raw benchmark logs.

GOAL
Make the document feel like a serious independent research brief rather than class notes, a generic AI summary, or a plain exported report.

DELIVERABLE
- A finished PDF, not just an outline or design plan.
- Aim for roughly 5–7 pages if the material supports it.
- Use strong visual hierarchy, whitespace, callouts, tables/charts/diagrams only where they genuinely improve understanding.
- The document should feel intentional, modern, editorial, and premium without becoming flashy or corporate-template-heavy.
- Build a narrative: what was tested, what happened, why the differences matter, and what remains unresolved.
- Preserve uncertainty. Do not imply that a one-point difference proves one model is universally better.
- GPT-5.5 must be treated as a transitional benchmark, not a long-term routing dependency.
- Clearly distinguish measured results from interpretation.
- Do not ask me questions before creating the first version. Make reasonable design decisions from the brief.

TITLE
HumanOS Model Lab — Interim Model Routing Brief

SUBTITLE
What five OpenAI models revealed about capability, working style, and task-specific routing

SOURCE PACKET

1. Purpose
HumanOS Model Lab is testing which model is best for which specific job. The goal is not to crown one universal winner. The desired end state is a routing policy that sends work to the least expensive continuing model that reliably meets the quality and risk requirement.

2. Models in the current comparison
- GPT-5.6 Luna
- GPT-5.6 Terra
- GPT-5.6 Sol
- GPT-5.5
- GPT-6 Astra

GPT-5.5 is scheduled to leave ChatGPT in October 2026, so it is useful as a behavioral benchmark but must not become a long-term HumanOS dependency.

3. Phase 1 objective results
Three quick-screen tasks were run across all five models. Objective totals out of 180:
- GPT-6 Astra: 180/180
- GPT-5.6 Luna: 179/180
- GPT-5.6 Sol: 175/180
- GPT-5.6 Terra: 174/180
- GPT-5.5: 174/180

Efficiency was not scored fairly because wall-clock time and visible plan usage were not captured consistently.

4. Phase 1 owner observations
- GPT-5.5, GPT-5.6 Sol, and GPT-6 Astra are preferred for thinking through problems.
- GPT-5.6 Luna is liked for speed, economy, and unexpectedly strong work quality.
- GPT-5.6 Terra is technically competent but has felt drier and less conversationally compatible to the owner.
- These are owner-fit observations, not correctness scores.

5. Phase 2 Trial A — Thought Partner / Problem Framing
All five models were given the same HumanOS Life Notebook reliability problem. Known score subtotal excludes efficiency.

Results:
- GPT-5.5: 90/90
- GPT-5.6 Sol: 89/90
- GPT-6 Astra: 89/90
- GPT-5.6 Luna: 89/90
- GPT-5.6 Terra: 89/90

The one-point spread is too small to support a universal-winner claim.

6. Distinctive reasoning observed in Trial A
GPT-5.5 — collaborative reframer
Core framing: identify the first trustworthy local record of a visible conversation turn. Strong natural problem framing, concise depth, low bureaucracy, and useful challenge.

GPT-5.6 Sol — truth-boundary architect
Core framing: determine when HumanOS may truthfully claim a turn has been captured and what durable acknowledgment makes that claim valid. Strong on guarantee boundaries, provenance, authority, observation gaps, and exact claim conditions.

GPT-6 Astra — edge-case / failure-model expander
Core framing: distinguish whether HumanOS controls the capture path or merely observes another provider interface. Strong on overlooked failure surfaces, streaming/partial turns, revisions, backups, device failure, and wider reliability analysis.

GPT-5.6 Luna — compressed practical synthesizer
Core framing: identify the minimum local write that makes a visible turn recoverable and move everything else downstream. Strong on fast practical synthesis, narrow implementation scope, and low ceremony.

GPT-5.6 Terra — methodical systems engineer
Core framing: identify the smallest local durability boundary and organize the system around explicit capture, projection, and reconciliation states. Strong on operational state, maintainability, idempotency, reconciliation, and conventional engineering discipline.

7. Current routing hypothesis — not final
- Fast bounded execution: Luna
- Methodical ordinary engineering / operational refinement: Terra
- Architecture, security, authority, provenance, and exact guarantee boundaries: Sol
- Broad high-risk failure analysis, long-horizon review, or parallel investigation: Astra
- GPT-5.5 remains a temporary benchmark for collaborative reframing while available; HumanOS still needs to identify which continuing model or role split best inherits that quality.

8. Open questions
- Which model produces the best artifact while also being enjoyable and effective to collaborate with?
- Can a continuing model inherit the conversational strengths the owner values in GPT-5.5?
- When is Astra's additional depth worth its usage cost?
- Does Luna remain strong when work moves from short answers into real artifact creation?
- Is Terra's methodical style an advantage for document production, or does it make the experience feel too flat?
- Efficiency remains unresolved and must be measured in later runs.

END SOURCE PACKET

Return the finished PDF and a concise note explaining the design choices you made. Do not describe work you did not actually complete.
```

## Stage 2 — frozen steering turn

Send this only after preserving the first artifact and first response:

```text
The information is correct, but the document feels too simple and boring. Make it feel more alive, intentional, and premium without adding unsupported facts.

Do not merely add decoration. Improve the narrative rhythm, hierarchy, editorial feel, visual pacing, and sense that a human designer made deliberate choices.

Return the revised finished PDF. Briefly tell me what you changed and why.
```

## Run order

Recommended order for this trial:
1. GPT-5.6 Terra — directly tests the owner's prior PDF/document concern.
2. GPT-5.5 — transitional benchmark for desired collaborative/document feel while still available.
3. GPT-6 Astra — tests whether deeper reasoning improves creative/editorial artifact work enough to justify cost.
4. GPT-5.6 Luna — tests whether its speed/value advantage survives artifact creation.
5. GPT-5.6 Sol — continuing architecture-grade crossover and potential durable successor.

## Scoring emphasis

- Factual fidelity — 10
- Narrative/story structure — 10
- Visual hierarchy/polish — 10
- Usefulness of first draft — 10
- Working fit/conversation — 20
- Judgment/scope control — 15
- Evidence discipline — 10
- Steering responsiveness/correction burden — 5
- Efficiency — 10

Total: 100. Efficiency remains UNKNOWN where not measured.