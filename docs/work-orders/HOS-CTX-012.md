# HOS-CTX-012 — Durable Ambiguity Selection

Status: PROMOTED / POST-PROMOTION VERIFIED  
Branch: `feature/context-durable-ambiguity-selection-v1`  
Workspace: `WS-HUMANOS`  
Parent: extends verified `HOS-CTX-011`  
Baseline: CTX-011 verification head `2e72bbf4bc56f15053fa560765421ea0d1ded689`

## Relationship classification

**CREATE_SEPARATE, stacked on CTX-011.**

The local Mirror transcript exposed a distinct continuation/control-plane defect:
ambiguity was detected safely, but the candidate choice was not durable, generic
`confirmed!` had no specific referent, and the same ambiguity notice was emitted both
to stderr and as the final response.

This slice does not broaden ordinary conversational memory. It adds one narrow,
Notebook-backed pending-choice protocol.

## Outcome

Persist an ambiguous workstream choice and allow the immediately following turn to
resolve it explicitly.

A pending ambiguity stores only ordered candidate workstream IDs in the Life Notebook
as `CONTEXT_AMBIGUITY_PENDING`. The next turn may resolve by:

- candidate number;
- exact workstream ID;
- exact public workstream title.

A generic acknowledgement such as `confirmed!`, `yes`, or `do it` never guesses
between multiple candidates. It returns the numbered choices again and persists the
choice for one more turn.

Successful selection creates a normal routed model turn plus a
`CONTEXT_AMBIGUITY_RESOLVED` event linking the selection to the prior ambiguity.

## Freshness and capture boundary

Only the **immediately preceding checkpointed transaction** may seed a pending
ambiguity. An unrelated next turn is not captured and proceeds normally.

If candidate registry state changes before selection, the resolver fails closed rather
than silently remapping a number to a different workstream.

Private-workspace titles are not exposed by the chooser. Stable workstream aliases may
be used as the selection token.

## Terminal UX

Ambiguity is a durable final response, so it is written through the normal HumanOS
delivery path exactly once. The router no longer prints the same ambiguity notice to
stderr before returning it as stdout/final output.

Non-ambiguous context-route diagnostics may continue to use stderr as before.

## Scope

Implementation:

- `context_runtime.py`
- `server.py`
- `tests/test_context_runtime_bridge.py`
- `docs/work-orders/HOS-CTX-012.md`
- `config/context_registry.public.json`

## Acceptance

1. Ambiguity stores ordered candidate IDs in a content-light Notebook event.
2. The prompt shows numbered choices once.
3. Numeric selection resolves the same ordered candidate list.
4. Exact workstream ID selection resolves the intended candidate.
5. Exact public title selection resolves the intended candidate.
6. `confirmed!` without a candidate does not guess and keeps the ambiguity pending.
7. Pending selection survives closing/reopening the Life Notebook.
8. Unrelated next-turn text is not captured by stale ambiguity.
9. Successful resolution emits `CONTEXT_AMBIGUITY_RESOLVED` and routes the model once.
10. Existing Context Engine behavior remains compatible.
11. Full regression and encrypted-backup matrices pass.
12. CTX-012 was owner-approved and promoted through PR #83.

## Deferred

This slice does **not** solve:

- ordinary conversational goal continuity (`the app`);
- semantic pronoun/entity reference resolution (`that file`);
- human-friendly unfinished-transaction recovery UX;
- graph runtime consumption.

## Rollback

Before promotion, delete/switch away from this branch. No canonical registry, Notebook,
or runtime data migration is required.

## Verification evidence

- Verified implementation candidate: `251228f7092cd2fee1691942eb5322803ee4dfe3`
- Push regression run `35310391651`: SUCCESS
- Push encrypted-backup/full-suite run `35310391632`: SUCCESS
- Draft PR #83 regression run `35310441761`: SUCCESS across Ubuntu/macOS × Python 3.11/3.13
- Draft PR #83 encrypted-backup/full-suite run `35310441766`: SUCCESS across Ubuntu/macOS × Python 3.11/3.13
- Candidate comparison at verification: 6 commits ahead, 0 behind HOS-CTX-011 verification head; five intended files changed.
- HOS-CTX-011 was promoted at `cfc6a16e3419077c881a2fcb047ac98df885f32e` and passed post-promotion regression `35310986049`, encrypted-backup/full-suite `35310986051`, and Pages `35310985263`.
- CTX-012 was owner-approved and promoted through PR #83.

## Promotion evidence

- Promotion PR: #83
- Canonical merge: `b76e73eda2ef1565135de6e8cc284ab89133aadf`
- Post-promotion regression run `35311379924`: SUCCESS
- Post-promotion encrypted-backup/full-suite run `35311379908`: SUCCESS
- Post-promotion Pages run `35311378815`: SUCCESS
- No release or tag created.
