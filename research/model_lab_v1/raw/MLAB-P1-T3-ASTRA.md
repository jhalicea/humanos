# MLAB-P1-T3-ASTRA — Raw Response

## Build HumanOS Email Intake v0

**One capability:** selected emails appear in HumanOS Inbox exactly once, with sender, subject, received time, source ID, and a reference back to the email.

Start with polling. Use your existing language and storage. This follows the earlier proposed scope; repository implementation remains unverified.

## First seven days

**Day 1 — Make one email appear.**
Inspect the existing Inbox write/read path. Implement an importer for a saved email fixture using that path. Read the resulting item back through HumanOS. Documentation alone does not count.

**Day 2 — Make replay safe.**
Normalize email fields. Enforce uniqueness on `(provider, account, message_id)` in storage. Import the same fixture twice; confirm one Inbox item. Keep personal email in the personal workspace.

**Day 3 — Connect your actual mailbox.**
Implement read-only authentication and fetch ten selected messages. Store credentials outside source control and logs. For Gmail, use OAuth and `messages.list` followed by `messages.get`; Google documents that flow in its [API guide](https://developers.google.com/workspace/gmail/api/guides/list-messages). Start with one folder or label.

**Day 4 — Run unattended polling.**
Poll every five minutes. Persist progress only after successful intake, handle pagination, and replay an overlapping window safely. Restart the process and verify that it resumes without skipping messages.

**Day 5 — Survive failure.**
Add a small persistent jobs table with attempt count, next retry time, and last error. Retry temporary failures with bounded exponential backoff; expose exhausted jobs for manual replay.

**Debugging exercise:** terminate the worker after writing an Inbox item but before marking its job complete. Restart it. Explain and fix any duplicate or lost item.

**Day 6 — Learn the webhook boundary.**
Add a local authenticated `POST /webhooks/email` endpoint using the same intake path. Test valid, repeated, and unauthorized requests. A local test sender demonstrates webhook handling; it does **not** establish live provider delivery.

**Day 7 — Ship and demonstrate.**
Wire intake into HumanOS’s actual capability routing, permissions, and user-visible status. Show imported items, failures, and replay. Save test results and reproduction commands.

## Measurable acceptance test

From a clean test scope, process **20 distinct emails**, replay all 20, inject two temporary failures, and restart mid-job:

- Exactly **20 Inbox items**, each with correct source identity.
- Zero lost messages or duplicates.
- Temporary failures recover within the configured retry budget.
- A permanent failure remains visible and replayable.
- Five real selected emails arrive through unattended polling within six minutes.

## Oral-interview question

“Why can a crash cause the same email to be delivered twice, and how does your implementation prevent two Inbox items?”

## Do not learn yet

Defer **n8n, Make, external queue infrastructure, autonomous agents, auto-replies, and AI classification**. After intake passes, use n8n to orchestrate this working capability. Add model-generated triage suggestions only after delivery is reliable.
