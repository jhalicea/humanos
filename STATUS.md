# HumanOS Status Snapshot

Status: **HOS-LN-002 IMPLEMENTED CANDIDATE / FINAL-HEAD CI REQUIRED / NOT PROMOTED**  
Date: 2026-10-01  
Workspace: `WS-HUMANOS`  
Project: Life Notebook  
Workstream: `HOS-LN-002 — Usable Life Notebook Memory Vertical Slice`  
Branch: `feature/life-notebook-usable-memory-v1`  
Baseline / merge base: `runtime-0.1` @ `3f2f25ea09941c8727daac1826e37badf0730d72`  
Work order: `docs/work-orders/HOS-LN-002.md`

## Current outcome

A bounded usable-memory vertical slice is implemented on this feature branch using the
existing HumanOS Notebook rather than a competing memory store.

The slice now provides:

- exact human/assistant transcript evidence preserved by the existing Notebook runtime;
- deterministic preference extraction after transcript completion;
- append-only `HOS-MEM-*` semantic events with content-free idempotency identity and exact source provenance;
- keyed chained event integrity;
- rebuildable current state with `ACTIVE` / `CONFLICTED` semantics;
- explicit correction through a new event with `supersedes` lineage;
- replay detection before current-state resolution;
- persistence across Notebook close/reopen;
- bounded current memory + provenance supplied to later Mirror turns;
- content-light `MEMORY_CONTEXT_BOUND` event-ID snapshots written before first model execution;
- exact bound-memory reconstruction on interrupted-task resume, preventing later state from silently changing an in-flight task;
- fail-soft semantic extraction: memory failure cannot erase or block a completed chat;
- content-light memory-processing receipts in task state.

The current semantic taxonomy is intentionally small: preference memory only. This is a
working vertical slice proving the conversation -> semantic ledger -> derived state ->
restart -> context/provenance -> supersession loop before broader memory types are added.

## Acceptance scenario

The automated acceptance tests cover both ordinary restart and interrupted execution:

```text
I prefer concise morning summaries.
        ↓
exact transcript persisted
        ↓
preference event + provenance
        ↓
current state = concise
        ↓
Notebook close/reopen
        ↓
How do I like my morning summaries?
        ↓
concise (from persisted derived state)
        ↓
provenance points to original page / tx / transcript seq
        ↓
Actually, make them detailed.
        ↓
new event supersedes old event
        ↓
old history retained; current state = detailed
```

The crash/resume test additionally begins a task while memory is `concise`, persists a
content-light binding before model execution, forces a model outage, changes current
memory to `detailed`, and then resumes the interrupted task. The resumed task must still
receive the originally bound `concise` snapshot, and only one binding event may exist.

A separate failure test forces semantic extraction to raise after a completed
conversation and verifies that the exact human/assistant transcript remains intact and
the task remains complete.

## Verification evidence

An earlier intermediate candidate at commit
`846338877a99e3aa0e014ef76888f089df3042f9` passed its seven then-existing memory tests,
ran **613 regression tests** successfully on macOS/Python 3.13 with 8 optional-dependency
skips, and passed the encrypted-backup/full-suite matrix on Ubuntu/macOS × Python
3.11/3.13.

That evidence is historical only. Privacy, idempotency, and crash-safe context-binding
refinements were added afterward. The current suite contains eight HOS-LN-002 acceptance
areas, and fresh CI on the final branch head is mandatory before promotion.

## Provenance correction

The actual branch merge base is
`3f2f25ea09941c8727daac1826e37badf0730d72`. An earlier draft status listed the first
parent of that merge instead; the documentation was corrected before final qualification.

## Relationship to PRE-LN-1

HOS-LN-002 does not cancel or overwrite PRE-LN-1. The separate schema/integrity,
SQLCipher/key-custody, migration/cutover, deletion, and production-qualification work
remains necessary for the hardened Life Notebook target.

The project direction is now explicitly two-track:

```text
USABLE LIFE NOTEBOOK                HARDENING
working transcript                  schema/integrity
semantic ledger                     SQLCipher / key custody
current state                       deletion fan-out
restart + recall                    migration/cutover
provenance                          production qualification
supersession
crash-safe context binding
        \                              /
         \                            /
          ------ hardened runtime ----
```

Usability is no longer blocked on completing every future hardening gate first.

## Explicit non-claims

- HOS-LN-002 is not yet promoted to `runtime-0.1`.
- No owner production Notebook data was committed or migrated.
- Full semantic coverage for decisions/tasks/open questions/entities is not implemented in this v1 slice.
- PRE-LN-1 cryptographic/storage/deletion requirements are not claimed complete.
- Passing the bounded acceptance tests does not itself qualify the future LN-1 kernel.

## Promotion gates

- [ ] final-head regression CI passes Ubuntu/macOS × Python 3.11/3.13;
- [ ] final-head encrypted-backup/full-suite CI passes the same matrix;
- [ ] final diff review finds no transcript-authority, provenance, privacy, crash/resume, or fail-soft blocker;
- [ ] no PRE-LN-1 workstream is overwritten or falsely marked complete;
- [ ] owner explicitly approves promotion.

## Next authorized action

Finish final-head CI and bounded review. If clean, present the exact candidate evidence
to the owner for promotion approval. Do not merge this branch merely because earlier
intermediate commits were green.
