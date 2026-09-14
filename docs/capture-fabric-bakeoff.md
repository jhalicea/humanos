# HumanOS Capture Fabric Bakeoff

Status: **experimental feature branch; do not merge without live evidence.**

HumanOS is testing five capture routes against one provider-neutral event contract. The goal is not to pick a vendor. The goal is to prove which transport most reliably preserves an exact conversation event and delivers it into the owner-controlled Life Notebook.

## Canonical architecture

```text
provider UI / API
       |
       v
capture route
       |
       v
HumanOS Capture Event v1
       |
       v
append-only remote relay (when used)
       |
       v
verified local import
       |
       v
Life Notebook SQLite  <-- canonical owner-controlled record
       |
       +--> distilled transcript/export
       +--> encrypted disaster-recovery backup
```

The remote relay is a mailbox, not the Life Notebook. Google Drive is an archive/backup destination, not the live transaction database.

## Shared event contract

Every route must produce the same immutable event fields:

- `version`
- `source`
- `conversation_id`
- `turn_id`
- `event_type`
- `role`
- `text`
- `idempotency_key`
- `variant_id`
- `source_created_at`

`text` is exact message content. It is never summarized or normalized by the capture layer.

A repeated `idempotency_key` with identical content is a safe retry. A repeated key with different content fails closed.

## Route 1 — provider-native signed event/webhook

**Target:** best possible route when a provider exposes a real signed conversation event stream.

HumanOS now has a provider-neutral `ProviderWebhookIngress` contract. It refuses a request unless a real provider-specific signature verifier succeeds. HumanOS does **not** claim that ChatGPT or another provider currently exposes the required normal-chat webhook merely because the adapter exists.

Promotion evidence:

- official provider event source exists;
- signature verification is implemented from the provider specification;
- human and assistant committed-message events are emitted without model/tool discretion;
- retries are documented and idempotent;
- native mobile conversations are covered;
- a live event survives provider retry and HumanOS restart.

## Route 2 — HumanOS Capture MCP gateway

**Target:** best owner-controlled route.

The application layer exposes exactly one conversational-writer capability:

`humanos_append_capture_event(event)`

It does not expose arbitrary SQL, deletion, transcript search, Life Notebook reading, filesystem access, or administrative database capabilities. Local HumanOS synchronization uses separate read credentials.

The MCP transport wrapper can change without changing the HumanOS event contract.

Promotion evidence:

- remote MCP server is deployed;
- ChatGPT can invoke the append tool from native mobile and desktop sessions;
- exact user and assistant content can be captured without a second model pass;
- tool invocation is reliable enough for the chosen capture guarantee;
- credentials are append-only / least-privilege;
- local HumanOS imports the event exactly once.

## Route 3 — direct PostgreSQL connector

**Target:** fastest practical prototype and comparison baseline.

The same schema runs on PostgreSQL. Supabase and Neon can both be tested without changing the event model.

The database exposes `humanos_append_capture_event(jsonb)` and `humanos_capture_after(bigint, integer)`. The underlying event table is append-only. Public access is revoked. A production writer credential should receive `EXECUTE` on the append function only.

This route is intentionally compared with Route 2. If a generic database connector cannot be constrained to a tiny permission surface, Route 2 wins even if Route 3 is simpler.

## Route 4 — local browser/native bridge

**Target:** independent desktop fallback and reconciliation sensor.

The existing HumanOS browser capture path remains valuable because it can observe the rendered desktop conversation and durably land events locally even when the cloud relay is unavailable. It does not solve native iPhone capture by itself.

The bakeoff should eventually map its events into the same Capture Event v1 contract rather than maintaining a permanent parallel identity model.

## Route 5 — Google Drive archive / distilled transcript export

**Target:** backup, portability, human-readable archive, and disaster recovery — not live transaction capture.

Existing transcript batching remains useful for:

- periodic distilled transcript files;
- encrypted vault backups;
- owner-readable exports;
- provider-independent disaster recovery.

Drive should not be the synchronization database unless all database/gateway routes fail the bakeoff.

## What we measure

Do not choose the winner by elegance alone. Every live route gets the same tests:

| Property | Required evidence |
| --- | --- |
| Exactness | Unicode, leading/trailing whitespace, multiline content round-trips exactly |
| Completeness | Human and assistant events both arrive |
| Idempotency | Retry produces one logical event |
| Conflict safety | Same key + changed text fails closed |
| Mobile | Works from native iPhone ChatGPT when claimed |
| Desktop | Works from normal desktop use when claimed |
| Model independence | Capture does not require a second LLM pass |
| Provider independence | HumanOS schema is not vendor-specific |
| Least privilege | Writer cannot read/delete/alter unrelated memory |
| Offline behavior | Failure queues or retries without losing canonical local evidence |
| Recovery | Restart/crash does not duplicate or silently drop an event |
| Latency | Time from committed message to durable receipt |
| Cost | Database/API/storage operations per 1,000 events |
| Operational burden | Secrets, daemons, OAuth, deployment and maintenance required |

## Selection policy

HumanOS can use more than one route. The likely final shape is defense in depth:

- primary remote capture route: Route 1 if a trustworthy provider-native event exists, otherwise Route 2;
- rapid prototype / independent comparison: Route 3;
- desktop reconciliation/fallback: Route 4;
- archive/disaster recovery: Route 5.

A route is not called "working" until a real conversation event has been written, read back, matched exactly, retried without duplication, and imported into the local Life Notebook.

## Current implementation evidence

Implemented on `feature/capture-fabric-bakeoff`:

- `capture_fabric.py` — immutable event contract, receipts, reference relay, webhook ingress contract, HMAC test verifier;
- `capture_mcp_gateway.py` — one-tool least-privilege MCP application surface;
- `sql/capture_fabric_postgres.sql` — append-only PostgreSQL relay and RPC functions;
- `tests/test_capture_fabric.py` — exactness, idempotency, conflict, immutability, cursor, webhook, MCP authority tests;
- `tests/capture_fabric_postgres.sql` — live PostgreSQL behavior checks;
- `.github/workflows/capture-fabric-postgres.yml` — PostgreSQL 16 CI verification.

Still requiring live external evidence:

- a provider-native signed conversation event source for Route 1;
- a deployed MCP transport for Route 2;
- connected Supabase and/or Neon project for Route 3;
- Capture Event v1 normalization for the inherited browser adapter in Route 4;
- final archive policy and privacy semantics for Route 5.
