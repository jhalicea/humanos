# MLAB-P1-T3-55 — Raw Response

Do this first: build **HumanOS Email Inbox Intake v0**.

Not a full email client. Not an agent that “manages your inbox.” One narrow capability: HumanOS can ingest email metadata from a test inbox/API, normalize it into the existing Inbox concept, deduplicate it, and mark each item with provenance.

**7-Day Build Plan**

**Day 1: Define the slice**
Pick one source: Gmail API, IMAP, or a mock email export. I’d start with **mock export first**, then Gmail later. Define the HumanOS Inbox item shape:

`source`, `external_id`, `from`, `subject`, `received_at`, `body_preview`, `labels`, `provenance`, `status`.

Do not classify, summarize, or auto-reply yet.

**Day 2: Build the importer**
Create a command like:

`humanos inbox import --source mock_email --file sample_emails.json`

It should validate input, reject malformed records, and write normalized Inbox items.

**Day 3: Add deduplication**
Use `source + external_id` as the stable identity. Re-running the same import must not create duplicates. Store enough provenance to prove where each Inbox item came from.

**Day 4: Add polling**
Add a basic polling runner:

`humanos inbox poll --source mock_email`

For now, polling can read from a folder or fixture file. The point is to learn polling state: last seen ID/time, repeat runs, no duplicate creation.

**Day 5: Add retry behavior**
Wrap import/poll steps with retry rules for transient failures. Record failed attempts visibly. Do not hide errors behind “agent reasoning.”

**Day 6: Add one webhook-shaped endpoint**
Create a local endpoint like:

`POST /webhooks/email`

It accepts the same normalized payload and routes through the same Inbox intake path. Now you can compare polling vs webhook without building two systems.

**Day 7: HumanOS capability**
Expose one real capability:

`inbox_intake`

It can answer or execute: “Import new inbox items from configured source.” It must go through the registry/routing/executor/permission pattern, not be a side script pretending to be integrated.

**Oral-Interview Question**

“Explain the difference between polling and webhooks using this Inbox system. Where is state stored, how are duplicates prevented, and what happens if HumanOS is offline?”

**Debugging Exercise**

Simulate three failures: duplicate email, malformed payload, and temporary source failure. Show that duplicates are ignored, bad records are rejected with evidence, and temporary failures retry without corrupting state.

**Acceptance Test**

Given 10 sample emails with 2 duplicates and 1 malformed record, after two imports HumanOS must contain exactly **8 valid Inbox items**, **0 duplicates**, **1 recorded rejection**, and each item must include source provenance.

**Do Not Learn Yet**

Do not learn n8n, Make, OAuth production flows, queues, distributed workers, multi-agent triage, email sending, auto-replies, vector search, or LLM classification yet. Those come after intake is boring, tested, and repeatable.
