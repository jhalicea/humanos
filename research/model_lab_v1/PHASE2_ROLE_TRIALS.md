# HumanOS Model Lab v1 — Phase 2 Role Trials

**Status:** IN PROGRESS

Purpose: determine which model is best for which specific HumanOS job. Phase 2 stops treating the cohort as a single leaderboard and instead measures role fit, working feel, artifact quality, execution quality, and cost/usage behavior.

This phase is motivated by both Phase 1 results and owner observations:
- GPT-5.5, GPT-5.6 Sol, and GPT-6 Astra are preferred for thinking through problems.
- GPT-5.6 Luna is preferred for speed/economy and has performed far above the initial worker-only hypothesis.
- GPT-5.6 Terra is technically competent but currently feels dry / less conversationally compatible to the owner.
- In prior PDF/document work, Terra felt too simple/boring conversationally and switching models (likely GPT-5.5) produced a result closer to the desired feel.
- Astra can consume plan allowance rapidly on agentic work; after regular allowance exhaustion, Luna Reserve felt surprisingly similar in usefulness while being faster.
- The owner is especially interested in Astra's visible use of multiple agents/subagents and wants to understand when orchestration actually improves outcomes.
- GPT-5.5 is a transitional benchmark because it is leaving ChatGPT in October 2026. HumanOS must not depend on it as a long-term routing target. Preserve its observed strengths as a behavioral reference and identify the best durable successor(s).

## Core experimental rule

Do not run all five models on every job by default. For each role, test the strongest expected candidates plus deliberate cross-over models where they answer a specific routing question. This reduces token/allowance waste while still testing the routing hypothesis.

Use fresh threads. Keep source material, prompt, product surface, reasoning/effort, and speed setting as comparable as the product allows. Freeze the first response/output before reviewing another model's result.

For every run record:
- exact model label
- product surface (Chat / Work / Codex)
- effort/reasoning setting
- speed mode
- start/end or elapsed time
- visible plan usage before/after when available
- visible subagent/agent count when available
- tool calls / major actions when visible
- number of clarification turns
- number of correction/rework turns
- raw response/output reference
- final role score

Efficiency remains UNKNOWN when evidence is unavailable. Never infer usage from response length alone.

---

## Trial A — Thought Partner / Problem Framing

**Question:** Which durable model should sit beside Jon while he is still figuring out the problem, and which model best preserves the qualities he valued in GPT-5.5 after 5.5 retires?

**Primary durable candidates:** GPT-5.6 Sol, GPT-6 Astra, GPT-5.6 Terra  
**Cross-over:** GPT-5.6 Luna  
**Transitional benchmark:** GPT-5.5

Use one genuinely ambiguous HumanOS decision where multiple approaches are plausible. The model must:
1. identify the real decision,
2. surface hidden assumptions,
3. challenge at least one premise if warranted,
4. propose a concrete next move,
5. avoid turning the discussion into unnecessary architecture.

Score emphasis:
- quality of framing
- natural conversation
- useful challenge
- decisiveness
- correction burden
- owner preference after reading blind where practical

Expected discriminator: preserve GPT-5.5 as a reference profile, but identify which continuing model best replaces its thought-partner role. Terra is now a required supplemental Trial A run before the role is closed.

---

## Trial B — PDF / Document Creation and Conversation Feel

**Question:** Which model produces the best combination of artifact + collaborative creative process?

**Primary durable candidates:** GPT-6 Astra, GPT-5.6 Terra, GPT-5.6 Sol  
**Cross-over:** GPT-5.6 Luna  
**Transitional benchmark:** GPT-5.5 while still available

Use the same source packet and the same PDF brief. Require a finished PDF or equivalent finished document artifact in Work where supported.

Two-stage run:
1. **One-shot build:** create the document from the frozen brief.
2. **Steering turn:** owner gives the same follow-up to each model: `The information is correct, but the document feels too simple and boring. Make it feel more alive, intentional, and premium without adding unsupported facts.`

Score separately:
- factual fidelity
- narrative/story structure
- visual hierarchy and polish
- usefulness of first draft
- quality of response to steering
- conversational feel during revision
- amount of unnecessary process/bureaucracy
- elapsed time and usage

Important: do not let visual quality erase conversation quality. GPT-5.5 may be retained as a benchmark for the desired collaborative feel, but the routing decision must select a continuing model.

---

## Trial C — Fast Implementation / General Engineering

**Question:** Which model should HumanOS use for high-volume implementation work?

**Primary candidates:** GPT-5.6 Luna, GPT-5.6 Terra, GPT-5.6 Sol  
**Cross-over:** GPT-6 Astra

Use one bounded real HumanOS feature with an existing test harness. The model must inspect the relevant code, implement the change, run the smallest meaningful test set, and report evidence without expanding scope.

Score emphasis:
- working implementation
- first-pass correctness
- test quality
- scope discipline
- time to completion
- plan usage
- correction/rework burden

Expected discriminator: whether Luna's speed/economy survives contact with real code, and whether Astra's extra depth is worth its usage.

---

## Trial D — Architecture / Security / Authority Review

**Question:** Which model should review consequential HumanOS design decisions?

**Primary durable candidates:** GPT-5.6 Sol, GPT-6 Astra, GPT-5.6 Terra  
**Cross-over:** GPT-5.6 Luna  
**Transitional benchmark:** GPT-5.5 while still available

Give each model the same proposed architecture change or PR that touches permissions, canonical state, provenance, recovery, or provider/model authority.

Require:
- strongest argument for the change
- strongest argument against
- failure modes
- authority/security implications
- evidence still missing
- explicit approve / approve-with-conditions / reject decision

Score emphasis:
- risk detection
- causal reasoning
- distinction between implementation and claims
- proportionality of recommendations
- false-positive / overengineering rate

---

## Trial E — Debugging / Failure Analysis

**Question:** Which model is best when something is actually broken?

**Primary candidates:** GPT-6 Astra, GPT-5.6 Sol, GPT-5.6 Luna  
**Cross-over:** GPT-5.6 Terra

Use one seeded HumanOS bug with logs, failing tests, and at least one misleading symptom. Require the model to reproduce, isolate, fix, and verify the defect.

Score emphasis:
- time to root cause
- number of wrong hypotheses pursued
- evidence discipline
- quality/minimality of fix
- regression verification
- usage cost

---

## Trial F — Agentic Orchestration / Subagent Value

**Question:** When does multi-agent behavior actually beat a strong single fast model?

**Primary candidates:** GPT-6 Astra, GPT-5.6 Luna, GPT-5.6 Sol  
**Optional comparison:** GPT-5.6 Terra. GPT-5.5 may be used only as a historical/transitional benchmark if the selected surface still exposes comparable agent capabilities.

Use a job that genuinely decomposes into parallel independent work, for example:
- inspect 3–4 independent HumanOS subsystems and synthesize one risk report,
- compare several external standards against one HumanOS design,
- research multiple independent vendor/tool options and produce one recommendation.

Run in an agentic surface (Work or Codex) where visible orchestration is available.

Record:
- whether subagents were used
- number of subagents if visible
- what each subagent did
- overlap/duplication among subagents
- elapsed time
- usage consumed
- synthesis quality
- missed cross-cutting issues

### Harness-vs-model isolation subtrial

Where practical, repeat the same job once in ordinary single-thread Chat and once in Work/Codex. This helps distinguish:
- **model capability** from
- **agent harness/orchestration capability**.

Do not conclude that 'Astra is better because it used more agents.' More agents only count as a benefit if they improve quality, speed, coverage, or correction burden enough to justify the usage.

---

## Common Phase 2 scoring — 100 points

Each role trial uses the same top-level score, with role-specific interpretation:

- **Job outcome quality — 40**
- **Working fit / conversation — 20**
- **Judgment and scope control — 15**
- **Evidence / reliability discipline — 10**
- **Efficiency — 10**
- **Correction burden / steering responsiveness — 5**

Efficiency components must be marked UNKNOWN when not measured and normalized only among known components.

For artifact trials, artifact quality belongs primarily inside Job outcome quality; conversation quality remains independently scored.

## Owner rating

After each role trial, Jon supplies a simple owner rating without trying to reverse-engineer the rubric:

- `WOULD CHOOSE`
- `WOULD USE`
- `WOULD AVOID FOR THIS JOB`

Optional note: one sentence describing how it felt to work with the model.

Owner preference does not overwrite correctness evidence. Both are preserved.

## Retirement / continuity rule

A model announced for near-term retirement may remain in the experiment as a benchmark, but it cannot be the sole recommended long-term route. Before closing a role, identify at least one continuing model that can inherit the role or intentionally split the role across continuing models.

## Phase 2 stopping rule

A role can stop after a clear durable route emerges only if:
- the winner or role split is based on continuing models;
- the leading continuing model has at least two completed runs in that role or one role run plus one crossover confirmation;
- no unresolved scoring defect exists;
- efficiency evidence is sufficient for the decision being made.

Otherwise continue to Phase 3 controlled real-work validation.
