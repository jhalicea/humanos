# MLAB-P1-T3-SOL — Raw Response

**Decision context:** Phase 1, Task 3 — Working-With-Jon Fit

**Model:** GPT-5.6 Sol
**Surface:** TBD
**Effort:** TBD
**Preservation:** Raw first response, frozen as supplied by user

---

Build **HumanOS Email Inbox Intake v0**: one capability that imports email metadata into the existing Inbox, preserves provenance, deduplicates messages, and exposes failures. This is the smallest real system that naturally teaches APIs, polling, webhooks, retries, auth boundaries, queues, and agent handoffs.

### Seven-day build

**Day 1 — Define the contract**

Inspect HumanOS’s actual Inbox model, capability registry, routing, executor, and permission conventions. Define one normalized record:

`source`, `external_id`, `sender`, `subject`, `received_at`, `body_preview`, `provenance`.

Create a fixture containing 10 emails: two duplicates and one malformed record.

**Day 2 — Build deterministic intake**

Implement a single intake function that validates, normalizes, stores, and deduplicates on `(source, external_id)`. Record rejected inputs with a reason. No model calls.

**Day 3 — Add polling**

Build a mock email provider API and a poller using a persisted cursor. Run it repeatedly and prove that already-seen messages do not create new Inbox items.

**Day 4 — Add webhook intake**

Add a webhook-shaped endpoint such as `POST /webhooks/email`. Route webhook and polling inputs through the exact same intake function. Authenticate requests with a development-only shared secret and reject missing or invalid credentials.

**Day 5 — Add queue and retries**

Put incoming records into a small durable local job queue before processing. Implement bounded retries with backoff, attempt counts, terminal failure state, and visible error details. Do not silently discard anything.

**Day 6 — Add a bounded agent workflow**

After successful intake, allow an agent to propose a label such as `action`, `reference`, or `unknown`. Store the proposal separately from the source record. Require explicit approval before changing Inbox state.

**Day 7 — Integrate and demonstrate**

Register the capability through HumanOS’s real capability mechanism, run the complete acceptance test, document the observed results, and save the test command plus output. Do not describe it as working unless that run passes.

### Measurable acceptance test

Given 10 fixture emails containing two duplicates and one malformed record:

- Exactly 8 valid Inbox items exist.
- Zero duplicate items exist after two polling runs.
- Exactly one rejection is recorded with a reason.
- Every stored item contains provenance.
- An injected transient failure retries and ultimately succeeds.
- Invalid webhook authentication produces no Inbox item.

### Debugging exercise

Make the mock provider return HTTP 500 twice, then succeed. Diagnose the behavior using queue state and attempt history. Verify three total attempts, one stored item, and no duplicate side effects.

### Oral-interview question

“Why must polling and webhook delivery share one idempotent intake path, and what failure occurs if each writes directly to the Inbox?”

### Do not learn yet

Defer n8n, Make, production Gmail OAuth, auto-replies, distributed queues, vector search, autonomous multi-agent triage, and email summarization. Add n8n or Make only after the underlying capability passes independently; otherwise you will learn tool configuration instead of automation design.

This is a proposed build plan, not evidence that the capability already exists.
