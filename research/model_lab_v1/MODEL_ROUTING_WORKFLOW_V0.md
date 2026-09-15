# HumanOS Model Routing Workflow v0

**Status:** SPECIFIED / NOT IMPLEMENTED IN RUNTIME

Purpose: define a simple, explainable rule for choosing GPT-5.6 Luna, Terra, Sol, GPT-6 Astra, and any temporary benchmark models by job type. This is a research routing specification only. It does not change production HumanOS behavior.

## Principle

Use the least expensive continuing model that reliably meets the quality/risk requirement. Escalate only when ambiguity, consequence, breadth, or unresolved failure justifies it.

A model scheduled for retirement may remain in Model Lab as a behavioral benchmark, but HumanOS must not create a long-term routing dependency on it.

## Human shortcut

If the owner says or means:

- **"I know what to do; build it."** -> Luna
- **"I need a steady engineer, not a brainstorm."** -> Terra
- **"Help me think through this architecture/security decision."** -> Sol
- **"Think with me; I am still figuring out the real problem."** -> route among Sol / Terra / Luna according to Phase 2 evidence; use Astra when the uncertainty is broad or consequential. GPT-5.5 is retained only as a temporary reference profile while available.
- **"This is high-risk, long-horizon, or needs independent parallel investigation."** -> Astra

Owner preference may override the default model when working feel matters, but the override is recorded separately from objective correctness.

## Deterministic routing questions

Score each task on four dimensions: LOW or HIGH.

1. **Ambiguity** — Is the real problem/solution unclear?
2. **Consequence** — Would a wrong answer materially affect security, privacy, canonical state, money, external actions, or irreversible work?
3. **Breadth** — Does the job naturally split into several independent investigations/workstreams?
4. **Execution volume** — Is the plan already clear and the remaining work mostly implementation, extraction, transformation, or repeated tool use?

### Routing table

| Pattern | Default route |
|---|---|
| Low ambiguity + low consequence + high execution volume | Luna |
| Medium ordinary engineering where a balanced style is useful | Terra |
| High ambiguity with architecture/security/authority implications | Sol |
| High ambiguity where conversational framing/problem definition matters | Phase 2 successor route among continuing models; GPT-5.5 is benchmark only |
| High consequence + high breadth, or difficult long-horizon agentic work | Astra |
| High execution volume after Sol/Astra/Terra has already resolved the plan | Luna worker |

## Planner -> Worker -> Reviewer workflow

For substantial HumanOS work:

1. **ROUTE** — Mirror classifies ambiguity, consequence, breadth, and execution volume.
2. **PLAN** — If uncertainty is material, select a continuing planner model (normally Sol, Terra, or Astra depending on task shape) to produce a bounded Work Contract. GPT-5.5 may be compared while available but is not a production dependency.
3. **WORK CONTRACT** — The planner outputs: goal, known facts, assumptions, scope, ordered jobs, acceptance tests, permissions, stop conditions, and unresolved questions.
4. **EXECUTE** — Luna performs well-defined implementation/research jobs whenever practical. Terra may be used for ordinary engineering if Luna is too broad/aggressive or the task benefits from a more methodical pass.
5. **VERIFY** — Sol reviews architecture/security/authority-sensitive work. Astra reviews only when the risk, breadth, or unresolved uncertainty justifies the additional usage.
6. **ESCALATE** — A worker must escalate rather than improvise when a job violates its Work Contract, encounters a material ambiguity, needs new authority, or repeatedly fails verification.
7. **RECORD** — Life Notebook / Model Lab records route, exact model, role, evidence, corrections, usage when available, and whether escalation changed the outcome.

## Work Contract schema

```yaml
goal: <specific outcome>
planner_model: <model>
worker_model: <model or none>
reviewer_model: <model or none>
known_facts: []
assumptions: []
scope:
  in: []
  out: []
jobs:
  - id: J1
    instruction: <bounded job>
acceptance_tests: []
permissions: []
stop_conditions: []
escalate_if: []
```

## Escalation rules

Escalate **Luna -> Sol** when:
- implementation exposes an architecture/security question;
- tests disagree with the plan;
- a permission/provenance/canonical-state boundary is unclear;
- the task requires choosing among materially different designs.

Escalate **Sol/Terra -> Astra** when:
- several independent workstreams must be investigated in parallel;
- the consequence of missing a cross-cutting issue is high;
- long-horizon coherence or multi-agent coordination is central to the job;
- two strong analyses remain in material conflict after evidence review.

De-escalate **Astra/Sol -> Luna** once uncertainty is resolved and the remaining jobs are explicit and testable.

## GPT-5.5 continuity treatment

GPT-5.5 is useful as a research reference because the owner strongly values its conversational reframing style. Because it is scheduled to leave ChatGPT in October 2026, the Model Lab should extract the properties that made it valuable rather than build workflows that require the model itself.

The replacement question is therefore not `Which model is identical to GPT-5.5?` but:

`Which continuing model, or combination of continuing models, reproduces the useful properties of GPT-5.5 for each job at acceptable cost?`

Those properties currently include:
- natural problem reframing;
- identifying the real decision before formalizing architecture;
- concise but substantive conversation;
- low bureaucracy;
- willingness to challenge the owner's premise without derailing the task.

Trial A now includes Terra as a required supplemental crossover specifically to help answer this succession question.

## Important distinction

Model selection is not authority. No model may expand its own permissions or silently change the route. Routing chooses computational capability; HumanOS governance still controls actions.

## Current evidence basis

Phase 1 suggests Luna is stronger at general engineering than originally expected; GPT-5.5 is a strong but temporary conversational/problem-framing benchmark; Sol is strong on authority and architecture boundaries; Astra is strongest on proof-oriented senior review; Terra is technically competent but currently less preferred by the owner conversationally. Phase 2 is now explicitly testing which continuing model(s) should inherit GPT-5.5's useful roles before retirement.
