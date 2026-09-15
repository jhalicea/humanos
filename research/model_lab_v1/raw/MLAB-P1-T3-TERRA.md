Build **HumanOS Email Inbox Intake v0** first: a narrow capability that imports email metadata into the existing Inbox concept, deduplicates it, records provenance, and retries safely. Start with polling; add webhooks only after polling is reliable.

Day 1 — Define the contract
Choose one source: Gmail API or a mocked mailbox if auth would delay you. Define one normalized record:

`source`, `external_id`, `received_at`, `from`, `subject`, `snippet`, `raw_ref`, `status`.

Write acceptance criteria before code: import new messages, never duplicate, preserve source identity, and expose failures.

Day 2 — Build the polling adapter
Implement `poll_email(source_cursor) -> messages`. Start with the last 24 hours or a fixed test fixture. Store the cursor only after a successful batch.

Day 3 — Add Inbox ingestion
Route normalized messages into HumanOS Inbox. Enforce idempotency with a unique `(source, external_id)` key. Keep raw content/reference separate from derived summaries.

Day 4 — Add observability
Log each run with: start/end, cursor before/after, fetched, created, duplicates, failed, retry count. Make a simple command or view that shows the latest run and its failures.

Day 5 — Add retries and a small queue
Put each message ingestion into a durable local queue/table. Retry transient failures with bounded exponential backoff; mark permanent failures clearly. Do not build distributed infrastructure—SQLite-backed jobs are enough.

Day 6 — Add authentication safely
Use OAuth/API credentials from environment or OS keychain, never source code or logs. Implement a deliberate “credential missing/expired” error path. If using Gmail, complete one real authorized read; otherwise keep the mock fixture and document the unverified live step.

Day 7 — Prove it end-to-end
Run a controlled batch of 20 fixture emails, including duplicates and two forced failures. Demonstrate successful recovery and a clean Inbox result.

Measurable acceptance test:

- 20 inputs: 16 unique valid, 2 duplicates, 2 transient failures.
- First run creates 16 Inbox items and records 2 retryable failures.
- After recovery, retries succeed without creating duplicates.
- A second identical run creates 0 items.
- Every Inbox item can be traced to its `source` and `external_id`.

Debugging exercise: deliberately make the ingestion step fail after writing the Inbox item but before acknowledging the queue job. Fix the resulting duplicate risk using the idempotency key and transaction boundaries.

Oral-interview question: “Why must the polling cursor advance only after the batch is safely persisted, and what failure occurs if it advances earlier?”

Do not learn yet: n8n, Make, webhook receivers, multi-agent orchestration, Kafka/RabbitMQ, or generic “AI agents.” They are useful later, but they will hide the core mechanics you need to understand: polling, auth, idempotency, queues, retries, and evidence. Once this works, recreate the same flow in n8n or Make, then replace polling with a webhook where the provider supports it.
