# HumanOS Model Routing Policy v1 — Candidate

**Status:** SPECIFIED / MANUAL-ACTIVE FOR MODEL LAB / NOT IMPLEMENTED IN HUMANOS RUNTIME

**Evidence basis:** Phase 1, Phase 2 Trial A, Phase 2 Trial B, owner ratings, and usage-calibration observations through 2026-09-15.

## Purpose

Remove routine model-selection burden from the owner. Mirror should decide the default route from the shape and risk of the work, explain the route only when useful, and escalate only when evidence justifies it.

This policy chooses computational capability. It does **not** grant authority, change permissions, or bypass HumanOS governance.

## Owner-level rule

> **Default to Sol. Move down to Luna or Terra when the work is well bounded. Move up to Astra when failure, breadth, or unresolved uncertainty matters more than usage. GPT-5.5 is a temporary behavioral benchmark, never a production dependency.**

This is intentionally simpler than a global leaderboard.

## Stable role map

### GPT-5.6 Sol — Lead / default thought partner
Use Sol by default when the owner is thinking, deciding, designing, reviewing, writing an important artifact, or when the task does not clearly qualify for a cheaper route.

Best-current evidence:
- strong owner fit;
- strongest Trial B first draft;
- tied strongest known final Trial B quality;
- strong truth-boundary / provenance / authority framing in Trial A;
- preferred by owner over Astra for ordinary high-quality work.

### GPT-5.6 Luna — Fast worker
Use Luna when the plan is already clear and the remaining work is bounded, reversible, high-volume, repetitive, extraction-heavy, transformation-heavy, or straightforward implementation.

Do not ask Luna to silently resolve a material architecture, permission, provenance, or security ambiguity. Escalate instead.

### GPT-5.6 Terra — Methodical systems engineer
Use Terra for ordinary engineering and operational work where explicit state, reconciliation, maintainability, idempotency, careful sequencing, or procedural documentation are central.

Terra is a preferred experimental route when the owner wants a grounded, steady engineering pass rather than fast execution or broad ideation. Its role remains subject to more Phase 2 engineering validation.

### GPT-6 Astra — Senior engineer / escalation
Use Astra when the task is high consequence, cross-system, long-horizon, strongly agentic, failure-analysis heavy, or when an independent senior review is worth more than conserving allowance.

Astra is **not** the default merely because it is the highest capability tier. The owner currently prefers Sol for many important tasks and wants Astra used as a senior engineer / escalation layer.

### GPT-5.5 — Transitional collaboration benchmark
Never route production HumanOS work to GPT-5.5 as a required dependency. Preserve what the owner likes about it as a behavior profile to reproduce with continuing models:
- natural reframing;
- enough explanation to feel substantive;
- low bureaucracy;
- useful challenge;
- willingness to identify the real decision before formalizing the solution.

## The four-route shortcut

Mirror classifies every substantial task into one primary route:

| Route | Human meaning | Primary model |
|---|---|---|
| **BUILD** | The job is clear; execute it | Luna |
| **ENGINEER** | Make the system orderly, maintainable, and operational | Terra |
| **DECIDE** | Think, design, review, synthesize, or produce important work | Sol |
| **ESCALATE** | Senior review, broad failure analysis, cross-system risk, long horizon | Astra |

When uncertain between routes, choose **Sol**, not Astra.

## Risk lanes

### GREEN
Characteristics: bounded, reversible, low consequence, clear acceptance test.

Default: Luna.  
Alternative: Terra when state/reconciliation/maintainability dominates.

No second model is required unless the output will trigger an external or irreversible action.

### AMBER
Characteristics: moderate ambiguity or consequence; touches real HumanOS behavior, integration, canonical data, or a user-facing artifact that matters.

Default pattern: **Sol plans or reviews; Luna/Terra executes.**

Examples:
- Sol -> Luna for bounded implementation after design is settled.
- Sol -> Terra for integration/state/reconciliation work.
- Sol alone for architecture, important writing, or decision support when delegation would add ceremony.

### RED
Characteristics: security/privacy/authority boundaries; irreversible external action; canonical-state migration; multi-system failure; major architecture; consequential ambiguity; conflicting strong analyses.

Default pattern: **Sol lead + Astra senior review.**

If the task itself is primarily broad failure analysis or genuinely parallel investigation, Astra may lead, with Sol converting the result into the final bounded decision/work contract.

Luna may execute only explicitly bounded subjobs after the risk/authority questions are resolved.

## Routing algorithm

Mirror should silently answer these questions in order:

1. **Is the task already well defined?**
   - Yes -> candidate Luna/Terra.
   - No -> candidate Sol/Astra.
2. **Is the main difficulty operational state/maintainability rather than ambiguity?**
   - Yes -> Terra.
3. **Does a wrong answer materially affect security, privacy, permissions, canonical state, money, external actions, or irreversible work?**
   - Yes -> at least Sol; Astra review if impact is high.
4. **Does the job span multiple systems, require independent parallel investigation, or have expensive-to-miss failure modes?**
   - Yes -> Astra escalation.
5. **Otherwise:** Sol if judgment is still needed; Luna if only execution remains.

## Planner -> Worker -> Reviewer workflow

For substantial HumanOS work, use the smallest chain that adds value:

**ROUTE -> PLAN -> EXECUTE -> VERIFY -> RECORD**

- **ROUTE:** Mirror classifies task, route, risk lane, and whether review is required.
- **PLAN:** Sol normally resolves ambiguity and creates a bounded work contract. Terra may plan operational work. Astra plans only when breadth/high consequence justifies it.
- **EXECUTE:** Luna performs explicit bounded jobs; Terra performs methodical engineering jobs.
- **VERIFY:** Sol verifies consequential worker output. Astra performs senior review only on RED/high-breadth work or unresolved conflict.
- **RECORD:** Life Notebook / Model Lab records route, models, roles, result, correction burden, evidence, and available usage telemetry.

Do not force all five steps when a single-model route is sufficient.

## Default workflows by work type

| Work type | Default workflow |
|---|---|
| Quick extraction / formatting / routine edit | Luna |
| Bounded implementation with tests | Luna -> Sol review if consequential |
| Ordinary stateful engineering / integration | Terra -> Sol review when architecture-sensitive |
| Architecture / security / provenance / authority | Sol |
| High-risk architecture or cross-system review | Sol -> Astra |
| Debugging, ordinary | Sol or Terra pending Trial E; use Luna for bounded fix after root cause is known |
| Debugging, broad/multi-system/high-impact | Astra -> Sol synthesis |
| Important executive/research document | Sol |
| Premium transformation / senior editorial challenge | Sol -> Astra only when the extra pass is worth it |
| Bulk research/extraction | Luna -> Sol synthesis |
| Deep parallel investigation | Astra -> Sol decision synthesis |
| Life Notebook capture architecture | Sol lead; Astra challenge only for RED failure/security review |
| Life Notebook implementation after contract is frozen | Luna or Terra -> Sol verify |

## Behavior overlays

Model selection and communication style are separate. HumanOS should eventually support behavior overlays so the owner does not need GPT-5.5 itself to preserve a valued working feel.

### `COLLABORATIVE_REFRAMER`
Apply mainly to Sol, optionally Astra/Terra:
- identify the real decision first;
- explain enough to expose reasoning structure without padding;
- challenge weak assumptions;
- avoid unnecessary architecture;
- recommend a concrete next move;
- use plain language before specialist vocabulary.

### `LEAN_EXECUTOR`
Apply mainly to Luna:
- no brainstorming unless blocked;
- execute the contract;
- report evidence;
- escalate rather than invent new scope.

### `METHODICAL_ENGINEER`
Apply mainly to Terra:
- make states, transitions, invariants, retries, idempotency, and reconciliation explicit;
- prefer maintainability over cleverness.

### `SENIOR_CHALLENGER`
Apply mainly to Astra:
- search for expensive-to-miss failure modes;
- challenge the leading plan;
- inspect cross-system effects;
- distinguish evidence from inference;
- stop when additional depth is no longer changing the decision.

## Escalation triggers

A cheaper model must escalate rather than improvise when any of these becomes true:
- acceptance tests conflict with the plan;
- new authority or permission is required;
- canonical state or provenance semantics are unclear;
- the task changes from implementation into design selection;
- repeated failure occurs after a bounded correction attempt;
- evidence is materially contradictory;
- the cost of a missed failure becomes high.

Escalation path is normally:

`Luna -> Sol -> Astra`

Terra normally escalates to Sol, then Astra if needed.

De-escalate back to Luna/Terra as soon as uncertainty is resolved.

## Owner override

Owner preference is valid input. The owner may say `use Sol`, `use Terra`, `use Luna`, or `get Astra to review this` and HumanOS should honor the override unless a governance/safety boundary prevents the requested action.

The system should record `route_source: owner_override` rather than pretending the automated router selected it.

## Model-retirement rule

A retiring model may remain in evaluation as a benchmark but may not be the sole route in a durable workflow. Any useful behavior must be translated into role definitions, prompts/overlays, tests, and acceptance criteria that can survive provider/model changes.

## Routing event record

Every substantial routed job should eventually emit a small record:

```yaml
routing_event:
  task_id: <id>
  task_class: BUILD|ENGINEER|DECIDE|ESCALATE
  risk_lane: GREEN|AMBER|RED
  primary_model: <model>
  worker_model: <model|null>
  reviewer_model: <model|null>
  behavior_overlay: <name|null>
  route_source: automatic|owner_override|experiment
  reason_codes: []
  started_at: <timestamp>
  result_status: <status>
  corrections: <count>
  evidence_refs: []
  usage_observations: []
```

## Manual operating rule for ChatGPT now

Until HumanOS runtime routing exists, Mirror/ChatGPT should apply this policy manually when working on HumanOS tasks:

- do not ask the owner to pick a model for routine work;
- identify the recommended route internally;
- mention the route only when switching/escalation would materially improve the work or cost;
- if the current selected model is adequate, continue without ceremony;
- if a different model is materially preferable and the assistant cannot switch models itself, say exactly which model to use and why in one sentence;
- preserve the route and result in Model Lab / Life Notebook when the logging path is available.

## Current default

**Sol is the HumanOS default lead model.**

Luna is the default worker.  
Terra is the default methodical systems-engineering option.  
Astra is the default senior escalation/reviewer.  
GPT-5.5 is a temporary behavior benchmark only.

## Status boundary

This document makes the routing policy **SPECIFIED** and manually usable in Model Lab. It does **not** make automatic runtime routing implemented, tested, verified, or deployed.

Next implementation target: convert the machine-readable policy into a local deterministic router that emits a routing event and recommendation before model execution, then validate it against recorded Model Lab cases before granting it any automatic execution authority.
