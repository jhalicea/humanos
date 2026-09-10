# HumanOS Record Envelope Integrity v1

Status: implementation candidate for issue #30.

## Verified repository facts

- The authoritative Life Notebook is SQLite in WAL mode with `synchronous=FULL`.
- `transcript.seq` is `INTEGER PRIMARY KEY AUTOINCREMENT`.
- Transcript rows are append-only after insert via `transcript_no_update` / `transcript_no_delete` triggers.
- New visible content uses vault-scoped HMAC-SHA256 over the exact stored UTF-8 text.
- The integrity key is stable vault identity; protected vaults fail closed if it is missing or replaced.
- Current key policy is `stable-v1-no-auto-rotation`.
- Portable backups preserve the integrity key and verify the restored Notebook.
- SQLite is authoritative; `recovery.jsonl` is independent fallback evidence.

## MVP decisions

1. Add nullable `record_integrity` and `record_integrity_version` columns. Do not backfill history.
2. Existing rows with both fields NULL remain legacy content-verifiable rows, never represented as envelope-protected history.
3. New rows receive envelope integrity at insert time. Never weaken append-only triggers to update the row afterward.
4. Do not bind `seq` in v1: SQLite assigns it during insert, while HumanOS deliberately forbids post-insert transcript updates. Ordering remains protected by SQLite constraints and transcript semantics; a later envelope version may revisit sequence anchoring.
5. Bind `tx`, `ordinal`, `role`, `content_digest`, and `created`, plus explicit record/envelope version domain separation.
6. Do not duplicate raw `text` in the envelope input. `content_digest` already authenticates exact stored UTF-8 text and is verified before the envelope.
7. Do not introduce a second `vault_id` identity primitive in v1. The stable bound integrity key already supplies vault-scoped verification and portable backup semantics.
8. Do not add key-rotation metadata in v1; the current lifecycle is explicitly stable/no-auto-rotation.
9. Reuse the repository's deterministic canonical JSON for the small typed envelope plus an explicit domain label. Avoid a new TLV/HKDF subsystem until cross-language requirements justify it.
10. MAC-without-version, version-without-MAC, unknown versions, and envelope mismatches fail closed.

## Verification order

1. SQLite integrity check.
2. Audit-chain verification.
3. Content digest against exact transcript text.
4. Record envelope proof for versioned rows.
5. Projection readback.

## Threats addressed

- role tampering
- ordinal tampering
- transaction reassignment
- timestamp tampering
- content-digest substitution
- metadata/content splicing
- partial-envelope downgrade

## Not solved here

- wholesale rollback to an older but internally valid vault snapshot
- availability attacks such as deleting the database
- compromised integrity key
- malicious code that intentionally disables verification

Those require separate controls and must not be conflated with record-envelope integrity.

## Separate follow-up

Harden parsing of `recovery.jsonl`: preserve malformed tail bytes as forensic evidence, never silently skip a malformed middle record, and keep recovery idempotent.
