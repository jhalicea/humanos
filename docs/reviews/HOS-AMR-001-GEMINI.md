# HOS-AMR-001-GEMINI

Status: EXTERNAL PROPOSAL — reviewed, not canonical policy.

## Metadata
- Provider: Google
- Model: gemini-2.5-pro
- Timestamp: 2026-09-11 05:44:30 EDT
- Review ID: HOS-AMR-001-GEMINI

## Executive finding
Gemini argues that the learning system should remain an evidence-gathering lifelong copilot rather than drift into a conventional LMS. It supports the encounter stages and K/P/D/C dimensions but recommends explicit uncertainty/recency, domain-specific weighting, bidirectional state, prior-knowledge fast-track, passive project evidence, and long-horizon skill decay.

## HumanOS triage

### ACCEPT AS V1 DATA-MODEL REQUIREMENTS
1. Preserve evidence time explicitly (`last_evidenced_at` semantics; current engine has `last_practiced`, which should be clarified rather than duplicated blindly).
2. Represent confidence/uncertainty separately from mastery. One successful observation must not silently mean high-confidence mastery.
3. Allow K/P/D/C weights to be skill-specific while retaining a documented default.
4. Stage transitions must be capable of moving both directions when evidence warrants it; stage is not an irreversible achievement badge.
5. Prior knowledge can challenge-out / fast-track through demonstrated evidence; no forced traversal through every encounter state.
6. Passive project activity may create candidate learning evidence, but extraction itself must not become authoritative grading.

### ACCEPT AS DESIGN PRINCIPLES, NOT IMMEDIATE ALGORITHMS
- Long-term forgetting/staleness matters.
- Cross-domain transfer is strong evidence when independently demonstrated.
- Skill graph needs eventual macro/micro aggregation.
- Goal changes should change what is prioritized, not rewrite historical evidence.
- Obsolete technologies need explicit status/context rather than silently remaining current.

### REJECT / QUALIFY
- Do **not** eliminate Course Completion %. HumanOS explicitly distinguishes Course Completion, Mastery, Career Readiness, and Skill Mastery. Completion is useful as a bounded curriculum/version metric; it must not masquerade as lifelong competence. Goal/initiative progress can be added separately rather than renaming a distinct metric.
- Do **not** implement an automatic cron-based downgrade/forgetting curve yet. We lack calibrated domain-specific decay evidence. Store recency/confidence now; implement decay later as a versioned, testable policy.
- Do **not** let passive parsing of GitHub, shell history, chats, or other projects silently grade the human. Such observations are candidate evidence subject to scope, provenance, privacy, and human correction.
- Cross-domain success should increase confidence only under an explicit evidence model; it should not literally “multiply” mastery without calibration.

## Code-level reconciliation
Current PR code already has timezone-aware evidence timestamps, append-only evidence IDs, and evidence-derived scoring. It currently has fixed global K/P/D/C weights and no confidence field. `last_practiced` exists but its semantics are narrower than `last_evidenced_at`. The current stage field is mutable but no deterministic evidence-to-stage transition policy exists yet.

## Proposed bounded Learning Academy slice
Implement on the dedicated Learning Academy branch, after the foundation branch is green:
- per-skill optional K/P/D/C weights with validated sum;
- confidence as a derived/explicitly labeled estimate based on evidence sufficiency, not model certainty;
- `last_evidenced_at` naming/semantics;
- challenge-out/prior-knowledge evidence path;
- tests proving a single success cannot imply high-confidence mastery;
- no decay algorithm yet.

## Course evidence
This review is relevant to `ai.evaluation`, `ai.systems`, and `ai.security`, but must not automatically promote Jon's mastery stage or scores.
