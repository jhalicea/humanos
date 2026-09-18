# HOS-CTX-005 — Temporal Context + Relevance Resolution

Status: PROMOTED / POST-PROMOTION VERIFIED  
Branch: `feature/context-temporal-relevance-v1`  
Workspace: `WS-HUMANOS`  
Parent: extends promoted `HOS-CTX-004`  
Baseline: `runtime-0.1` at `5223fc2ff157672658736d27ee0c4d400dff8ba9`

## Relationship classification

**EXTEND as a new bounded Context Engine workstream.**

CTX-004 made verified historical Notebook work recoverable across conversations. CTX-005 adds deterministic temporal relevance over that same evidence. It does not create a second memory system.

## Outcome

Resolve bounded chronology expressions against verified Notebook timestamps before human disambiguation.

Initial supported scopes:
- yesterday;
- today / earlier today;
- last week (previous Monday-to-Monday UTC window);
- most recent / latest verified historical workstream.

## Security and authority invariants

- Notebook verification and CTX-004 eligibility remain the trust boundary.
- Temporal resolution only filters already-verified historical records.
- No raw transaction identifiers enter model context or primary human UX.
- No embeddings, LLM date inference, entity graph, branch switching, tool permission, merge, or replay authority.
- Ambiguity after temporal filtering still fails closed.
- Exact human input remains unchanged.
- Temporal semantics are explicit and deterministic; current v1 uses UTC because Notebook timestamps are canonical UTC evidence.

## Acceptance criteria

1. `yesterday` resolves only the previous UTC calendar date.
2. `today` / `earlier today` resolves only current UTC calendar date.
3. `last week` resolves the previous Monday-to-Monday UTC window.
4. `most recent` / `latest` selects the first eligible record from verified Notebook history ordering.
5. No temporal phrase preserves CTX-004 candidate behavior.
6. Existing CTX-001..004 tests remain green.
7. Full regression and encrypted-backup matrices pass before promotion.

## Deliberate boundaries

Natural-language ranges such as `three days ago`, user-local timezone/calendar semantics, ordering relations such as `before the model loader`, event/entity graph reasoning, semantic retrieval, and broad relevance scoring remain future bounded increments.

## Promotion gate

No automatic merge/release. Promotion requires Jon's explicit approval after verification.

## Verification evidence

Verified candidate implementation commit: `f750e96fb808a496a957492da8388c29e60b0ee2`.

- Regression run `35296691364`: SUCCESS — Ubuntu 24.04 and macOS 15 × Python 3.11/3.13.
- Encrypted-backup/full-suite run `35296691290`: SUCCESS — same four-job matrix.
- Pre-verification comparison: 4 commits ahead of `runtime-0.1`, 0 behind; changes limited to Context runtime, dedicated temporal tests, registry metadata, and this work order.

Promotion remains owner-gated.

## Promotion evidence

Owner-authorized PR #72 merged into `runtime-0.1` at `1fb56505a17ff503c14cf31783991efdf31e950b`.

- Post-promotion regression `35297790406`: SUCCESS.
- Post-promotion encrypted-backup/full-suite `35297790327`: SUCCESS.
- Post-promotion Pages `35297789718`: SUCCESS.

HOS-CTX-005 is canonical. No release/tag was created.
