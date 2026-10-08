# MLAB-P1-T3-LUNA — Raw Response

Build one narrow capability: **Email → HumanOS Inbox intake**, with provenance, deduplication, retries, and a human approval boundary.

### 7-day plan

**Day 1 — Define the contract**

Specify one input event:

```
{
  "provider": "gmail",
  "message_id": "...",
  "received_at": "...",
  "sender": "...",
  "subject": "...",
  "body": "..."
}
```

Define the Inbox record, status states (`received`, `processed`, `failed`), and provenance fields. Use fixtures first; do not connect your real inbox yet.

**Day 2 — Build the webhook**

Add a HumanOS endpoint such as `POST /api/inbox/email`.

Implement:

- schema validation
- authentication using a shared secret
- idempotency keyed by `(provider, message_id)`
- durable storage
- safe response codes: `202` accepted, `409` duplicate, `400` invalid

Write tests for each case.

**Day 3 — Add a polling adapter**

Create a small adapter that reads fixture emails—or a local mock provider—and converts them to the webhook contract. Make the adapter restartable using a cursor or timestamp. Record raw input separately from normalized Inbox data.

**Day 4 — Add retries and failure visibility**

Introduce a queue or database-backed work table. Implement bounded retries with exponential backoff and a dead-letter state. Preserve the original error and attempt count. Test process interruption between receipt and processing.

**Day 5 — Connect n8n**

Use n8n only as orchestration:

`poll/mock email → HTTP Request → HumanOS webhook`

Configure timeout, response handling, and one retry. Do not put business rules or authority in n8n. Make is optional; reproduce the same request there only after the n8n path works.

**Day 6 — Add a bounded agent step**

Have an agent propose tags and a short summary from the stored email. It may write only a draft enrichment field. It may not send, delete, archive, forward, or alter the source message. Store model, prompt version, and input record ID.

**Day 7 — Operate and document**

Run the complete path repeatedly. Add a small status view or CLI showing received, processed, failed, retrying, and dead-letter items. Document the actual tested path, configuration, and known limits.

### Oral-interview question

Why must idempotency be enforced in HumanOS even if n8n or Make claims to retry safely?

### Debugging exercise

Force the worker to crash after queue insertion but before marking the email processed. Prove that restarting it produces exactly one Inbox record and does not lose the event.

### Acceptance test

Given 100 input events containing 10 duplicates and 5 transient processing failures, the system must produce exactly **90 Inbox records**, eventually process all eligible records, retry failures no more than three times, and preserve provenance for every record.

### Do not learn yet

Do not begin with multi-agent swarms, OAuth for multiple providers, vector databases, autonomous email actions, distributed Kafka-style queues, complex Make/n8n patterns, or generalized workflow platforms. First make this one path durable, observable, and truthful.
