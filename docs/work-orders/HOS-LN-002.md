# HOS-LN-002 — Usable Life Notebook Memory Vertical Slice

Status: **PROMOTED TO `runtime-0.1` VIA PR #122 / OWNER-HOST PRODUCTION QUALIFICATION NOT ESTABLISHED**  
Project: Life Notebook  
Workspace: `WS-HUMANOS`  
Repository: `jhalicea/humanos`  
Branch: `feature/life-notebook-usable-memory-v1`  
Baseline / merge base: `runtime-0.1` @ `3f2f25ea09941c8727daac1826e37badf0730d72`  
Created: 2026-10-01

## Post-promotion evidence reconciliation (2026-10-10)

This section corrects the original **pre-promotion snapshot** using immutable GitHub evidence.
The detailed implementation and historical acceptance contract below are preserved;
their candidate-stage assertions and unchecked checkboxes are not the current branch status.

- **Promotion evidence:** [PR #122](https://github.com/jhalicea/humanos/pull/122) was merged into `runtime-0.1` on 2026-10-02 at commit `0fe4ea5751bb17be30656a5c95809b79d6718636`. Original feature-head commit: `c9413f50f181019257d7fd66941e596ebd8f8e10`.
- **Recorded canonical-commit CI:** [regression](https://github.com/jhalicea/humanos/actions/runs/36960921269) and [encrypted-backup/full-suite](https://github.com/jhalicea/humanos/actions/runs/36960921066) concluded **SUCCESS** for the merged commit. These are historical CI outcomes, not tests rerun by this reconciliation.
- **What was promoted:** deterministic **explicit-preference** semantic memory, provenance, correction/supersession, privacy-aware source suppression, rebuildable derived state, and bound context across restart.
- **What was *not* qualified:** real owner-vault migration, owner-host recovery/restore, universal external-conversation capture, broad semantic taxonomy/RAG, production SQLCipher/key custody, full deletion/remanence guarantees, or local-model retention/forgetting.
- **Separate lineage:** PRE-LN-1 / HOS-LN-001 remains independent; [draft PR #117](https://github.com/jhalicea/humanos/pull/117) is not promoted and does not become complete by HOS-LN-002's merge.
- **Governance evidence limit:** GitHub merge and green CI establish canonical incorporation and recorded tests; this note does not independently certify every historical owner-approval action or owner-device deployment.
- **Next bounded qualification:** synthetic owner-local Mirror conversation → restart → sourced preference readback/correction, followed by separately authorized restore/privacy qualification. Preserve the original vault; do not infer real-vault access permission from this note.

## Classification

`EXTEND`

This slice extends the existing exact transcript, conversation capture, Notebook recall,
checkpoint/recovery, and Context Runtime capabilities. It does not replace the PRE-LN-1
schema/integrity, SQLCipher/key-custody, migration/cutover, deletion, or production
qualification workstreams.

## Problem

HumanOS already persisted exact human/assistant turns and already supported bounded
Notebook recall with provenance, but ordinary Mirror conversation did not yet have a
small deterministic current-state memory loop equivalent to:

```text
conversation
  -> durable transcript evidence
  -> append-only semantic event
  -> rebuildable current state
  -> bounded context
  -> later recall with provenance
```

The project had accumulated extensive future-hardening work before proving this simple
user-visible loop end to end. HOS-LN-002 closes that bounded usability gap without
claiming the future hardened LN-1 kernel is complete.

## Implemented slice

### Canonical evidence remains the transcript

Existing `Notebook.start()` / `Notebook.append()` behavior remains authoritative. Human
input is persisted before model execution. Assistant output is persisted before the
transaction checkpoint. Semantic extraction occurs only after the completed transcript
exists.

### Append-only semantic memory events

`notebook_memory.py` adds a v1 semantic-memory projection with:

- stable `HOS-MEM-*` event identifiers;
- schema versioning;
- owner + subject + value;
- exact source transaction / transcript sequence / role provenance;
- content-free idempotency identity derived from source transaction + transcript row;
- replay detection before current-state resolution;
- previous-event and event hashes protected by the Notebook integrity key;
- no-update / no-delete database triggers for semantic events;
- `supersedes` lineage expressed by a new event rather than rewriting the old event.

The v1 semantic extractor is intentionally deterministic and bounded to explicit user
preferences. It requires no model authority.

### Derived current state

`memory_state` is a replaceable projection rebuilt from semantic events. It supports:

- `ACTIVE` for one surviving current event;
- `CONFLICTED` when multiple unsuperseded declarations for the same subject exist;
- deterministic rebuild from the append-only event history.

A plain contradictory declaration does not silently replace an earlier preference. An
explicit correction can supersede the active event.

### Crash-safe bounded Mirror context

A new Mirror turn computes a bounded semantic-memory selection and writes a
`MEMORY_CONTEXT_BOUND` audit event **before first model execution**. That event contains
only immutable `HOS-MEM-*` event IDs plus schema/status metadata; it does not duplicate
preference text.

The model context is reconstructed from those exact immutable event IDs. If the task is
interrupted and later resumed, HumanOS reuses the original binding rather than compiling
latest memory. Therefore a task that began with `concise` cannot silently resume with a
later `detailed` preference. Legacy unfinished tasks that predate this feature have no
binding and resume without retroactive semantic-memory injection.

If a persisted binding cannot be reconstructed from its source events, resume fails
closed rather than substituting current memory or an empty packet.

The model receives the reconstructed snapshot as host-derived data with provenance. It
is explicitly labeled as neither permission nor independent factual verification, and
conflicted records must not be resolved by guessing.

### Fail-soft extraction, content-light receipts

Semantic extraction runs after the exact conversation turn completes. An extractor
failure cannot erase or block that completed transcript.

Task state stores only processing status/IDs (`status`, `event_id`, `supersedes`,
`error_type`, `tx` when present). Preference content remains in the transcript and
semantic memory store rather than being copied into the processing receipt.

## Acceptance contract

The bounded acceptance scenario is:

1. Human: `I prefer concise morning summaries.`
2. Human/assistant transcript is durable.
3. A preference event is appended with source provenance.
4. Current state resolves `morning summaries -> concise`.
5. Close and reopen the Notebook/runtime.
6. Human: `How do I like my morning summaries?`
7. Mirror receives the persisted current state and can answer `concise`.
8. Provenance identifies the original Notebook page, transaction, and transcript row.
9. Human: `Actually, make them detailed.`
10. A new event supersedes the earlier event without rewriting it.
11. Current state becomes `detailed`.
12. Both historical events remain verifiable.

The crash/recovery extension additionally proves:

1. Current preference is `concise`.
2. A new task binds that semantic event before model execution.
3. The model fails and the task remains resumable.
4. Current preference later changes to `detailed`.
5. The interrupted task resumes with its original bound `concise` snapshot.
6. Exactly one content-light memory binding exists for the interrupted task.

## Tests

`tests/test_notebook_memory.py` now covers eight acceptance areas:

1. exact transcript provenance and idempotent retry;
2. restart persistence;
3. explicit supersession without history rewriting, including replay after state changed;
4. unresolved contradiction -> `CONFLICTED`;
5. destruction/rebuild of derived state from append-only events;
6. live Mirror acceptance flow across Notebook reopen;
7. interrupted-task recovery with the exact pre-failure memory binding;
8. semantic-extractor failure cannot erase or block the completed conversation.

The first complete CI execution at commit
`846338877a99e3aa0e014ef76888f089df3042f9` ran 613 regression tests on macOS/Python
3.13 and returned `OK` with 8 optional-dependency skips; all seven tests that existed at
that earlier commit passed. The encrypted-backup full-suite matrix also passed on
Ubuntu/macOS and Python 3.11/3.13 at that commit.

Subsequent privacy, idempotency, and crash-safe binding refinements invalidated
that earlier commit as final qualification evidence **at the time of the original candidate review**.
Later candidate-head and merged-commit CI are recorded in the post-promotion section above.

## Provenance correction

The branch merge base was independently re-read using GitHub compare and is
`3f2f25ea09941c8727daac1826e37badf0730d72`. An earlier draft listed its first parent
`eb5824ff533b2569fbe0a1d53617e7a3a6e06f7f`; that value was corrected before final
qualification.

## Explicit non-claims

HOS-LN-002 does **not** claim:

- the full Muse semantic taxonomy (decisions/tasks/open questions/entities) is implemented;
- PRE-LN-1 schema/integrity work is superseded;
- SQLCipher production binding or key custody is complete;
- physical deletion/remanence guarantees are complete;
- semantic-memory deletion fan-out is production-qualified;
- hosted-provider disclosure policy is changed;
- owner production Notebook data has been migrated;
- LN-1 is complete;
- this branch is production-ready merely because the bounded acceptance test passes.

## Historical pre-promotion gates (preserved snapshot)

The unchecked items below are original candidate-stage gates, **not a current claim that PR #122 remains unmerged**. GitHub promotion and CI evidence is recorded above; individual owner-host qualification remains separate.

At the time of the pre-promotion review:

- [ ] final branch head passes regression CI on Ubuntu/macOS × Python 3.11/3.13;
- [ ] final branch head passes encrypted-backup/full-suite CI on the same matrix;
- [ ] exact diff is reviewed for transcript authority, provenance, privacy, crash/resume consistency, and fail-soft behavior;
- [ ] no PRE-LN-1 workstream is overwritten or falsely marked complete;
- [ ] owner explicitly approves promotion.

## Rollback

Before the 2026-10-02 promotion, rollback would have been deletion/abandonment of the candidate branch alone. That historical option does not roll back incorporated canonical code.

After the 2026-10-02 promotion, revert the exact promotion commit through the normal owner-governed SDLC. The semantic-memory
projection is additive; canonical existing transcript evidence must not be deleted as a
rollback side effect.

## Next bounded extension after promotion

The bounded explicit-preference slice is incorporated into the canonical branch; broader semantic coverage remains separately gated. Only after additional bounded acceptance should it expand in small,
verified increments (for example decisions, tasks, open questions, contradictions, and
entities), reusing the same invariant:

**transcript evidence first -> append-only semantic history -> rebuildable state -> bounded context -> provenance.**
