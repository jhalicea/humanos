# HOS-LN-000 — Life Notebook LN-0 Consolidation

**Status:** V-03 PASS / PROMOTED
**Workspace:** `WS-HUMANOS`  
**Branch:** `life-notebook-ln0`  
**Baseline:** `runtime-0.1` @ `0cf78d9abe5dcfcc6114bb43167dcf7406478657`  
**Architecture contract:** `docs/life-notebook/LN0_CONSOLIDATED_ARCHITECTURE.md`  
**Baseline map:** `docs/life-notebook/LN0_BASELINE_MAPPING.md`  
**Verification plan:** `docs/life-notebook/LN0_VERIFICATION_PLAN.md`

## Outcome

Merge the existing HumanOS Life Notebook/runtime foundation with the new Life Notebook architecture so that LN-1 can be implemented without creating a competing runtime, rewriting working components unnecessarily, or reopening constitutional work.

## Why now

The current runtime already has real Life Notebook capture, recovery, context, capability, browser, and conversation-capture infrastructure. Recent architecture work added stronger requirements for intelligence sovereignty, the Canonical State / Knowledge Graph separation, source authority, provider isolation, encrypted durable storage, deletion fan-out, and enterprise-grade SDLC/agent roles.

These must be reconciled into one implementation path before schema/security work begins.

## Classification

`EXTEND` — this is not a new HumanOS system. It extends the existing `runtime-0.1` Life Notebook and Context work.

## Existing foundation found

Repository inspection on 2026-09-25 confirmed:

- default/canonical branch is `runtime-0.1`;
- current branch head at inspection: `0cf78d9abe5dcfcc6114bb43167dcf7406478657`;
- the repository is Python-first today;
- `notebook.py` already has a process writer lock, SQLite WAL, append-only transcript/events, recovery tables, HMAC-keyed content integrity, transaction helpers, and readback/integrity enforcement;
- `conversation_capture.py` already provides provider-neutral exact host-turn capture with keyed idempotency and checkpoint verification;
- `conversation_ledger.py` already provides append-only external-message import with source identity and conflict detection;
- `context_registry.py`, `context_runtime.py`, `context_graph.py`, and related work orders already form an active Context/Brain lineage;
- `AGENTS.md` and `docs/foundation/WORKFLOW_STANDARD.md` already define repository routing, focused workstreams, evidence-based promotion, independent review, rollback, and preservation rules;
- `README.md` explicitly distinguishes verified runtime behavior from planned work and documents current Life Notebook boundaries/limitations.

## Preserve

Do not replace these without a proven reason:

1. exact transcript fidelity;
2. read-back verification before checkpoint claims;
3. single-writer discipline;
4. idempotent/retry-safe capture;
5. truthful recovery/degraded states;
6. append-only evidence/correction history;
7. local-first authority;
8. model/provider abstraction;
9. Context Registry / Context Runtime lineage;
10. capability/authorization separation;
11. test/CI/rollback discipline;
12. existing runtime evidence and frozen history.

## New architecture to integrate

The LN-0 architecture adds/refines:

- three semantic planes: Notebook evidence, Canonical State, Knowledge Graph;
- authority order: Notebook > State > Graph;
- sole Ingestor kernel writer;
- sole State Applier State writer;
- least-privilege projection workers;
- source authority ceilings;
- four policy axes: epistemic, sensitivity, delegation, provider;
- models consume ContextPackets and do not browse the Brain;
- unique independently deletable payload objects;
- State watermark/poison-event semantics;
- mention-first reversible entity resolution;
- projection checkpoints/impact invalidation;
- deletion fan-out to all persistent derived bytes;
- encrypted storage/key-recovery direction;
- external-provider isolation as an enforceable boundary;
- mobile v1 as capture-only, not replicated Brain.

## Explicit non-goals

This slice does **not**:

- rewrite the Constitution or Foundation;
- ratify old Foundation candidates;
- rewrite HumanOS in Rust;
- start LN-1 schema implementation;
- build the Knowledge Graph;
- build embeddings;
- add cloud providers;
- solve distributed/multi-device Brain replication;
- create a second Notebook/runtime;
- migrate or delete existing Notebook evidence.

## Risks

1. redesigning around old candidate documents instead of current runtime reality;
2. accidental schema rewrite before migration/recovery design exists;
3. conflating Graph confidence with Canonical State authority;
4. giving local/external models direct Brain retrieval;
5. treating encryption/security recipes from model reviews as verified facts;
6. adding governance artifacts that duplicate existing workflow/status systems;
7. breaking current exact-capture/recovery behavior while trying to improve architecture.

## Acceptance criteria

HOS-LN-000 is complete when:

- [x] current repository/runtime foundation has been inspected read-only;
- [x] merge map (preserve/refine/defer) is documented;
- [x] consolidated LN-0 architecture contract exists on this branch;
- [x] exact current Notebook schema/capture/recovery behavior is mapped to proposed `NotebookEventV1` / `PayloadObjectV1` without assuming destructive migration;
- [x] Context Compiler/current Context Runtime integration point is mapped;
- [x] component capability matrix is translated into implementable writer/model/worker boundaries at architecture level;
- [x] encryption/key-recovery spike plan is written;
- [ ] SQLCipher/SQLite WAL behavior is verified from primary technical evidence and a reproducible spike;
- [x] deletion fan-out dependency contract is turned into test cases/spec packet;
- [x] source-authority/ingestion abuse cases are turned into test cases/spec packet;
- [ ] LN-1 work order is written with executable acceptance tests;
- [ ] independent architecture/security review finds no unresolved schema-blocking defect;
- [ ] one explicit owner decision promotes LN-0 from candidate to implementation-ready.

## Evidence plan

Use:

- current repository files and exact commit SHAs;
- automated tests and CI for existing behavior;
- isolated test vaults only;
- primary SQLite/SQLCipher/macOS documentation for implementation claims;
- targeted local spikes for crash, encryption, key recovery, and process/egress behavior;
- independent reviewer packets containing the same requirements/diff/evidence;
- no owner Notebook content in Git or hosted-model review packets.

## Rollback

This workstream currently changes documentation only. `runtime-0.1` remains untouched. Delete/revert the `life-notebook-ln0` branch to abandon the candidate without affecting runtime behavior or Notebook data.

## V-03 execution record — 2026-09-26

Attempts 1–4 are preserved as **FAILED / rejected evidence**. Independent
Review #2 rejected Attempt 2's caller-created trusted-principal boundary. Attempt
3's isolated fixture added authenticated-session resolution, resolved-source
idempotency, exact-byte canonical hashing, mutation verification, actual-path
SIGKILL recovery, and projection-failure isolation. Attempt 4 was rejected for
omitting persisted `ingested_at` from the commitment, lacking real concurrent
distinct-event ancestry coverage, and recording stale/contradictory counts.
The completed independent review of Attempt 5 returned **PASS WITH FINDINGS**,
with no blocking findings. The promotion decision is **YES**. V-03 status:
**PASS / PROMOTED**.

### V-03 review lineage

- Attempt 1 — FAIL — caller-controlled source label granted authority.
- Attempt 2 — FAIL — trusted principal remained caller-created; crash/integrity proof inadequate.
- Attempt 3 — FAIL — authentication remained forgeable; canonical commitment incomplete.
- Attempt 4 — FAIL — `ingested_at` uncommitted; distinct concurrent ancestry not tested; evidence inconsistent.
- Attempt 5 — PASS WITH FINDINGS / PROMOTED — no blocking findings; promotion decision YES.

Attempt 5 replaces only the isolated fixture and tests. It uses a HumanOS-owned
test authenticator with opaque signed tokens, resolved principal/policy, semantic
submission fingerprints, and one complete authoritative envelope. It does not
modify Runtime 0.1 production code or Notebook data. Focused execution:
`python3 -m unittest tests.test_ln0_v03_ingestor -v` — **8/8 passed**.
The fixture has no separately persisted payload store, so no separate-payload
orphan claim is made. The actual event transaction SIGKILL proof left no
committed event. The independent verdict is **PASS WITH FINDINGS** with no
blocking findings; the promotion decision is **YES**.

Required broader execution: `python3 -m unittest discover -s tests -v` — **592
tests run, 11 skipped, and 1 sandbox loopback PermissionError** in
`test_swarm.SwarmTests.test_live_loopback_and_attribution`. This is unrelated to
V-03 and prevents claiming a completely green repository suite. Record it as a
separate known environment/test issue for later investigation; do not alter
`test_swarm.py` as part of V-03. No Runtime 0.1 production source or owner
Notebook data was modified.

## Next action

Preserve the completed independent review and investigate the separate sandbox
loopback environment/test issue later. V-03 implementation and tests remain
unchanged by this promotion documentation update.

After V-03 review, execute the first remaining evidence-producing LN-0 packets:

1. **V-01 Current-Schema Migration Fixture** — prove an exact, idempotent mapping from representative Runtime 0.1 evidence into the proposed kernel/payload model without touching owner data.
2. **V-02 Encrypted SQLite / SQLCipher Spike** — verify exact encryption/WAL/crash/backup/key-recovery behavior on the target stack from primary technical sources plus isolated execution.

Their results decide the LN-1 migration/storage ADR and unlock the LN-1 work order.
