# HumanOS Capture Fabric Bakeoff

Status: **experimental feature branch; do not merge without live end-to-end evidence and owner approval.**

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
private local remote-event mirror
       |
       v
durable local CaptureSpool
       |
       v
verified Life Notebook SQLite  <-- canonical owner-controlled record
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

A repeated `idempotency_key` with identical content is a safe retry. A repeated key with different content fails closed. Human edits and assistant regenerations are represented as new immutable variants rather than overwriting prior evidence.

## Route 1 — provider-native signed event/webhook

**Target:** best possible route when a provider exposes a real signed committed-message event stream.

HumanOS has a provider-neutral `ProviderWebhookIngress` contract. It refuses a request unless a real provider-specific signature verifier succeeds. HumanOS does **not** claim that ChatGPT or another provider currently exposes the required normal-chat webhook merely because the adapter exists.

Promotion evidence:

- official provider event source exists;
- signature verification is implemented from the provider specification;
- human and assistant committed-message events are emitted without model/tool discretion;
- retries are documented and idempotent;
- native mobile conversations are covered;
- a live event survives provider retry and HumanOS restart.

## Route 2 — HumanOS Capture MCP gateway

**Target:** preferred owner-controlled route when Route 1 is unavailable.

The application layer exposes exactly one conversational-writer capability:

`humanos_append_capture_event(event)`

It does not expose arbitrary SQL, deletion, transcript search, Life Notebook reading, filesystem access, or administrative database capabilities. Local HumanOS synchronization uses separate read credentials.

A runnable MCP Python SDK v2 wrapper is present in `capture_mcp_server.py`. Its database credential is expected to be the dedicated append-only writer role. The MCP transport wrapper can change without changing the HumanOS event contract.

Current state: application layer and runnable server code are implemented. A live remote MCP deployment and ChatGPT connection are still required before this route is called operational.

## Route 3 — direct PostgreSQL connector

**Target:** fastest practical prototype and independent comparison baseline.

The same schema can run on compatible PostgreSQL providers without changing the event model.

A real private Neon/PostgreSQL bakeoff relay is now provisioned. It contains the append-only event table plus two SECURITY DEFINER functions:

- `humanos_append_capture_event(jsonb)`
- `humanos_capture_after(bigint, integer)`

The final runtime authority is represented by separate NOLOGIN capability templates: `humanos_capture_writer_limited` can execute only the append function and has no table read/update/delete or cursor-read authority; `humanos_capture_reader_limited` can execute only the cursor-read function and cannot append or read the table directly. CI verifies these boundaries. Provider-created administrative roles must not be reused as production runtime identities merely because they can be narrowed with ordinary grants; deployment must use purpose-built least-privilege identities.

Live synthetic evidence already obtained:

- exact Unicode/leading-trailing whitespace/multiline text was remotely committed;
- the relay returned `REMOTE_CAPTURED` and a durable sequence;
- an identical retry returned the same sequence and event identity rather than inserting a duplicate;
- remote cursor readback returned the exact text unchanged;
- PostgreSQL CI independently verifies append-only UPDATE/DELETE denial, conflict rejection, idempotency, exact text, cursor behavior, and writer/reader privilege separation.

This proves the database/event layer independently of MCP deployment. It is not automatically the preferred final interface because a generic database connector can be broader than the single-purpose HumanOS MCP. The final design keeps the least-privilege function boundary even if the infrastructure later moves to another PostgreSQL provider or a private server.

## Route 4 — local browser/native bridge

**Target:** independent desktop fallback and reconciliation sensor.

The existing HumanOS browser capture path can observe the rendered desktop conversation and durably land events locally even when the cloud relay is unavailable. It acknowledges only after durable local storage and tolerates the Life Notebook writer lock.

It does not solve native iPhone capture by itself, and provider DOM changes require maintenance. It should remain a fallback/reconciliation lane rather than the sole capture mechanism.

## Route 5 — Google Drive archive / distilled transcript export

**Target:** backup, portability, human-readable archive, and disaster recovery — not live transaction capture.

Existing transcript batching remains useful for:

- periodic distilled transcript files;
- encrypted vault backups;
- owner-readable exports;
- provider-independent disaster recovery.

Drive should not make normal conversation capture wait on network file writes and should not decide whether a turn is canonical.

## Remote-to-local synchronization

`capture_remote_sync.py` adds a staged synchronization path rather than writing a cloud event directly into the Life Notebook:

1. read events after the highest locally mirrored remote sequence;
2. require contiguous remote sequence ordering;
3. validate every Capture Event v1 object;
4. atomically write the remote page into a private local SQLite mirror using WAL + `synchronous=FULL`;
5. read the committed rows back and run SQLite integrity verification;
6. convert mirrored events into the existing durable local `CaptureSpool`;
7. opportunistically ingest the spool into the Life Notebook;
8. if the Notebook writer is busy, leave the already-durable local event pending and retry later.

Assistant regenerations are materialized as new local variant turns with the original human prompt repeated as branch context. Human edits are preserved as new human half-turns. Prior transcript evidence is never rewritten.

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
| Privacy | Amount of raw transcript plaintext exposed outside the owner-controlled device |

## Selection policy

HumanOS can use more than one route. The likely final shape is defense in depth:

- primary remote capture route: Route 1 if a trustworthy provider-native committed-message event exists, otherwise Route 2;
- durable remote mailbox: least-privilege PostgreSQL;
- independent comparison/debug path: Route 3;
- desktop reconciliation/fallback: Route 4;
- archive/disaster recovery: Route 5.

A route is not called "working" until a real or explicitly synthetic acceptance event has been written, read back, matched exactly, retried without duplication, and — for production promotion — imported into the local Life Notebook.

## Privacy gate before real conversations

The bakeoff relay currently uses **synthetic plaintext test events only**. Real private conversations should not be routed into the remote relay until the production privacy mode is chosen and tested.

The preferred direction is application-level envelope encryption: remote PostgreSQL stores ciphertext plus only the minimum routing/idempotency information needed for synchronization; owner-controlled HumanOS keeps decryption authority. TLS and database role restrictions remain required, but they are not substitutes for minimizing remote plaintext exposure.

## Current implementation evidence

Implemented on `feature/capture-fabric-bakeoff`:

- `capture_fabric.py` — immutable event contract, receipts, reference relay, webhook ingress contract, test verifier;
- `capture_mcp_gateway.py` — one-tool least-privilege MCP application surface;
- `capture_mcp_server.py` — runnable MCP Python SDK v2 wrapper;
- `capture_postgres.py` — function-only PostgreSQL writer/reader adapter;
- `capture_remote_sync.py` — remote mirror -> durable local spool -> Life Notebook synchronization;
- `sql/capture_fabric_postgres.sql` — append-only PostgreSQL relay and RPC functions;
- `sql/capture_fabric_roles.sql` — least-privilege writer/reader capability templates;
- `tests/test_capture_fabric.py` — exactness, idempotency, conflict, immutability, cursor, webhook, MCP authority tests;
- `tests/test_capture_remote_sync.py` — remote mirroring, exact Notebook import, variant turns, gap failure, busy-writer recovery;
- `tests/capture_fabric_postgres.sql` — live PostgreSQL behavior checks;
- `tests/capture_fabric_roles.sql` — privilege-boundary checks;
- `.github/workflows/capture-fabric-postgres.yml` — PostgreSQL CI verification;
- `.github/workflows/capture-mcp-tests.yml` — current MCP dependency/import authority-surface check.

Still requiring live external evidence:

- a provider-native signed conversation event source for Route 1;
- a deployed MCP transport connected to ChatGPT for Route 2;
- one remote synthetic human+assistant pair pulled through the real reader path and imported into Jon's local Life Notebook;
- live desktop acceptance on Jon's Mac for Route 4;
- final encrypted remote-payload design and final Drive archive policy.

## Promotion gate

Do not merge this branch based only on unit tests. Promotion requires at least:

- full HumanOS regression suite on macOS and Linux;
- PostgreSQL append-only integration test;
- current MCP SDK import/tool-surface test;
- live MCP deployment with a function-only writer credential;
- one synthetic remote human+assistant turn imported exactly once into a local Life Notebook and verified after restart;
- duplicate retry and conflicting retry tests across the remote boundary;
- a documented privacy decision for remote transcript payloads;
- owner approval.
