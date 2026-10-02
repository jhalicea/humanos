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
- append-only `HOS-MEM-*` semantic events with idempotency and source provenance;
- chained event integrity using the Notebook content-integrity function;
- rebuildable current state with `ACTIVE` / `CONFLICTED` semantics;
- explicit correction through a new event with `supersedes` lineage;
- bounded current memory + provenance supplied to later Mirror turns;
- persistence across Notebook close/reopen;
- fail-soft semantic extraction: memory failure cannot erase or block a completed chat;
- content-light memory-processing receipts in task state.

The current semantic taxonomy is intentionally small: preference memory only. This is a
working vertical slice proving the conversation -> semantic ledger -> derived state ->
restart -> context/provenance -> supersession loop before broader memory types are added.

## Acceptance scenario

The automated acceptance test proves:

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

A separate test forces semantic extraction to raise an exception after the conversation
has completed and verifies that the exact human and assistant transcript remains intact
and the task remains complete.

## Verification evidence

At commit `846338877a99e3aa0e014ef76888f089df3042f9`:

- all 7 HOS-LN-002 memory tests passed;
- macOS/Python 3.13 regression execution ran **613 tests** and returned **OK** with 8
  optional-dependency skips;
- encrypted-backup/full-suite CI passed on Ubuntu/macOS × Python 3.11/3.13.

Privacy refinement commit `059e02c4edd82506afee3d599e441a5a94e13440`
changed the durable task memory-processing receipt to status/IDs only. Work-order and
status preservation/provenance corrections followed, so fresh CI on the final branch
head is required before any promotion claim.

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
        \                              /
         \                            /
          ------ hardened runtime ----
```

Usability is no longer blocked on completing every future hardening gate first.

## Explicit non-claims

- HOS-LN-002 is not yet promoted to `runtime-0.1`.
- No owner production Notebook data was committed or migrated.
- Full semantic coverage for decisions/tasks/open questions/entities is not implemented
  in this v1 slice.
- PRE-LN-1 cryptographic/storage/deletion requirements are not claimed complete.
- Passing the bounded acceptance test does not itself qualify the future LN-1 kernel.

## Promotion gates

- [ ] final-head regression CI passes Ubuntu/macOS × Python 3.11/3.13;
- [ ] final-head encrypted-backup/full-suite CI passes the same matrix;
- [ ] final diff review finds no transcript-authority, provenance, privacy, or fail-soft blocker;
- [ ] owner explicitly approves promotion.

## Next authorized action

Finish final-head CI and bounded review. If clean, present the exact candidate evidence
to the owner for promotion approval. Do not merge this branch merely because earlier
intermediate commits were green.
