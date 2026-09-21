The real decision is not “sync vs async vs batch.” It is:

**What event can HumanOS truthfully claim it has captured, and what durable local acknowledgment must occur before that claim is made?**

I recommend a hybrid with a crucial distinction:

**Synchronously append each completed visible turn to a local SQLite capture ledger; asynchronously project that ledger into the human-readable Life Notebook.**

The ledger is not a disposable queue. It is the canonical evidence that capture occurred. The notebook is a rebuildable, query-friendly projection.

Why this is the right boundary:

- The synchronous path stays tiny: validate an envelope, assign an event ID, commit locally, acknowledge.
- Provider APIs, browser connectors, classification, formatting, linking, and notebook projection stay outside that path.
- A broken connector may stop new observation, but it cannot corrupt or erase already committed continuity.
- Batching becomes an optimization for projection—not a gamble with uncaptured history.
- One SQLite database, one worker, and an explicit state machine are understandable by one owner. Kafka, distributed queues, or elaborate event infrastructure would be architecture for architecture’s sake.

The minimum event should preserve raw visible content plus provenance: provider, conversation identity, turn role, provider timestamp when available, local observation time, capture method, stable or derived external ID, content hash, and capture version. Projection status should be explicit: `CAPTURED`, `PROJECTED`, or `FAILED_RETRYABLE`. “Saved to notebook” must mean projected and verified—not merely observed or queued.

### Assumptions worth challenging

**“Visible” means capturable.** It does not always. Browser DOMs can virtualize older turns, streaming responses may be incomplete, and providers expose different identifiers. HumanOS must distinguish:

- observed complete turn;
- observed partial/streaming turn;
- suspected gap;
- connector unavailable.

**“Losing history is unacceptable” means zero loss is technically guaranteed.** That promise is only possible after HumanOS receives the event. If it passively watches another provider interface, there is an unavoidable observation boundary. The honest guarantee is: *once locally acknowledged, the turn survives provider and projector failure*. Gaps before observation must be detected and surfaced, not silently denied.

**The formatted notebook must be immediately current.** Probably not. What must be immediate is durable capture. A projection lag of seconds is acceptable if status is visible and recovery deterministic.

**Every token delta must be journaled.** Usually unnecessary. Capture the finalized visible turn, with optional periodic snapshots only for long streams where losing an in-progress response matters.

### What I would do for the next 30 days

**Days 1–7: define and prove the capture contract.** Specify the event envelope, acknowledgment point, conversation identity rules, deduplication key, partial-turn behavior, and truthful statuses. Build failure tests conceptually before implementation: crash before commit, crash after commit, duplicate delivery, projector failure, provider disappearance, and missing-turn detection.

**Days 8–14: implement one local vertical slice.** Use SQLite WAL and a short transaction per finalized turn. Add an idempotent projector that reads unprojected events and materializes them into a test notebook. No provider-specific formatting in the ledger.

**Days 15–21: test two unlike sources.** Choose one browser-mediated provider and one local/model-API source. This exposes the real portability problems: identities, completion detection, edits/regenerations, and unavailable metadata.

**Days 22–30: run a reliability qualification.** Simulate crashes, locked databases, duplicate observations, connector outages, and projector restarts. Measure capture commit latency, projection lag, duplicates, detected gaps, and recovery success.

At day 30, expand only if the system demonstrates: no loss after acknowledgment, deterministic replay, idempotent projection, visible failures, and negligible turn latency. The governing idea is simple: **capture locally first; derive everything else later.**