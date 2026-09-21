# Recovery Ledger Continuation v1

Status: implementation candidate for issue #48.

## Problem

PR #46 correctly seals `runtime/recovery.jsonl` when its final physical record is unterminated. HumanOS must not append a delimiter to that record or concatenate a new record onto it. The owner still needs an explicit way to resume fallback logging without rewriting the sealed evidence.

## Design

Continuation is an explicit owner CLI action, never an automatic startup repair.

1. Open and verify the Notebook normally. SQLite remains authoritative.
2. Require the current `recovery.jsonl` to be sealed only by a final unterminated record. Middle corruption is not continuable.
3. Read the sealed ledger as exact bytes and derive a deterministic continuation ID from its full forensic SHA-256.
4. Persist an owner-only archive containing the exact predecessor bytes and an HMAC-authenticated continuation manifest under the existing vault integrity key. The SHA-256 field is labeled forensic checksum; the HMAC is the authenticated linkage proof.
5. Only after the archive is durable, atomically replace the active path with a new LF-terminated `LEDGER_CONTINUATION` header record containing the authenticated link to the predecessor archive.
6. Fsync files and containing directories. If the process stops after the archive is durable but before the active replacement, rerunning the explicit action reuses the deterministic archive and completes the transition. If it stops after replacement but before SQLite audit logging, rerunning validates the header/archive and records the missing audit event.
7. The old bytes are never truncated, normalized, or repaired. They move into the explicit archive lineage as exact bytes.
8. Normal `_append_recovery_record()` continues using `runtime/recovery.jsonl` after the transition with no hidden routing or pointer state.

## Invariants

- No automatic continuation.
- No continuation across malformed middle evidence.
- No source-byte rewrite before a durable exact archive exists.
- New active ledger starts with one complete physical LF record.
- Link authenticity comes from a domain-separated HMAC under the vault integrity key, not from raw SHA-256.
- Repeating the same continuation is idempotent.
- Any mismatched/tampered existing archive or continuation header fails closed.
- SQLite audit event is additive and idempotent; it does not make the recovery ledger authoritative.

## Acceptance tests

- terminated clean ledger refuses continuation;
- valid unterminated final object continues explicitly;
- malformed/truncated final tail continues after exact quarantine/archive preservation;
- archived predecessor bytes exactly equal the former active ledger bytes;
- new active ledger is valid LF-terminated JSONL with an authenticated continuation header;
- repeat invocation returns the same continuation and does not create a second archive/event;
- malformed middle record refuses continuation;
- tampered archive/header fails closed;
- simulated interruption after durable archive can be resumed;
- normal recovery writer can append after successful continuation.

## Scope boundary

Portable backup v1 currently does not include `recovery-archive/`. Ordinary Notebook open now verifies a recognized continuation header against its authenticated archive, so portable backup v1 explicitly refuses to create an incomplete bundle from a continued ledger until issue #52 adds archive-aware portability. Break-Glass #33 and anti-rollback/high-water-mark work remain separate.
