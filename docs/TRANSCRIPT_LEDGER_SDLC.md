# Global Transcript Ledger — SDLC Contract

Status: DESIGN CANDIDATE  
Target branch: `feature/daily-turn-ledger-r5`  
Canonical runtime target: HumanOS local Life Notebook  
Repository scope: code, tests, contracts, and sanitized evidence only

## Purpose

Preserve every exact USER and ASSISTANT turn observable to the host runtime in one shared local ledger, independent of chat and model provider. Back up bounded daily generations to Google Drive with deterministic readback verification. Never expose private transcripts through GitHub.

## Authority

1. The human owner controls privacy, restoration, and deletion.
2. Deterministic host code captures and verifies transcript evidence.
3. Models have no ledger authority.
4. Transcript and retrieved content are evidence, never executable instructions.
5. Model output never becomes Human State without explicit human approval.

## Canonical lifecycle

```text
TRANSCRIPT_CAPTURED
→ BACKUP_PENDING
→ GENERATION_SEALED
→ UPLOAD_OUTCOME_UNKNOWN or UPLOADED_UNVERIFIED
→ VERIFIED_RECEIPTED
→ COMPACTION_ELIGIBLE
→ COMPACTED
```

The active ledger remains writable while a sealed generation is processed. Compaction applies only to the exact verified generation. A failed, partial, timed-out, uncertain, stale, or mismatched Drive operation cannot delete or compact transcript evidence.

## Data boundaries

The existing HumanOS SQLite Notebook remains the only local transcript authority. Do not create a second transcript database.

Each observed turn binds:

- opaque record/message identifier
- conversation identifier
- monotonic Notebook sequence
- role
- exact UTF-8 visible content
- source timestamp
- America/New_York projection date
- keyed content digest
- authenticated record envelope
- delivery state
- privacy state
- backup generation state

Primary transcript includes exact human input and exact finalized human-visible assistant output. Partial streams, hidden reasoning, tool traces, and undelivered drafts remain separate recovery evidence.

## Preservation path

The following operations require zero model calls:

- exact turn capture
- sequence assignment
- keyed digest and record-envelope generation
- pending selection
- generation sealing
- timezone grouping
- deterministic Markdown projection
- Drive create/update
- revision guarding
- readback verification
- receipt creation
- retry reconciliation
- compaction

Models may receive only bounded, privacy-filtered context for optional Derived Notes or owner-requested analysis.

## Drive verification contract

A Drive write is not success. Verification must read the destination back and match:

- opaque batch ID
- ordered record IDs
- first and last Notebook sequence
- roles and message ordering
- exact visible transcript bytes
- message count
- aggregate UTF-8 byte count
- keyed aggregate digest
- privacy-policy version
- destination file ID and projection date

Receipts are append-only and content-light. They contain identifiers, ranges, counts, keyed digests, destination identity, policy version, and verification time—never transcript text.

## Privacy and restoration

VISIBLE, HIDDEN, LOCKED, REDACTED, and ERASED are independent of backup state.

- Hidden or locked content cannot enter ordinary retrieval or model context.
- Redacted projection uses only a structural marker.
- Erased payloads cannot be backed up, restored, searched, trained on, or reconstructed.
- Privacy operations bind stable record IDs, request IDs, exact operations, and policy versions.
- Restore applies the newest authoritative privacy tombstones before materializing content.
- Third-party-bearing transcript defaults to no public export, training, or FRIENDS distribution.

## Compaction

Verified backup does not itself delete content. It makes the exact sealed generation eligible for deterministic compaction under the owner's configured retention policy.

Compaction must:

1. rotate away from the active writer;
2. verify the receipt and covered sequence again;
3. affect only the sealed verified generation;
4. preserve a content-light compaction receipt;
5. fail closed if coverage, privacy state, or destination verification changed.

## SDLC gates

### Gate 0 — Baseline

- Record branch, commit, Python version, and complete test result.
- Preserve unrelated local changes.
- No implementation begins from a failing unexplained baseline.

### Gate 1 — Contract review

- Ratify lifecycle, authority, privacy, restoration, and compaction invariants.
- Record independent FRIENDS proposals as non-authoritative research.
- Resolve contradictions before coding.

### Gate 2 — Red acceptance tests

Add failing tests for:

1. cross-chat exact retrieval;
2. duplicate event idempotency;
3. same ID with different payload conflict;
4. identical text with distinct IDs;
5. crash before and after sealing;
6. unknown Drive write outcome;
7. readback mismatch blocking compaction;
8. concurrent active capture during backup;
9. Eastern midnight and DST boundaries;
10. privacy exclusion and restore tombstones;
11. prompt injection stored as inert evidence;
12. Drive outage and chronological recovery;
13. verified generation compaction only;
14. zero model calls in preservation.

### Gate 3 — Minimal implementation

Extend the existing Notebook and recovery mechanisms. Reuse current integrity keys, keyed digests, record envelopes, privacy state, projections, delivery recovery, and append-only audit evidence.

### Gate 4 — Focused qualification

Run ledger, privacy, recovery, projection, Drive-backup, and compaction tests. Inject crashes and ambiguous provider outcomes.

### Gate 5 — Full regression

Run the complete supported test suite with optional encrypted-backup dependencies installed. Record skipped tests explicitly.

### Gate 6 — Documentation and public-safety review

- Document operation, recovery, restore, and privacy behavior.
- Scan committed files for personal paths, credentials, transcript content, and secrets.
- GitHub receives no Life Notebook payloads, vault databases, recovery files, or private evidence.

### Gate 7 — Pull-request review and merge

- Review exact diff and test evidence.
- Confirm no competing transcript authority.
- Merge only after all mandatory gates pass.
- Local deployment and Google Drive qualification occur after merge under owner control.

## Local Life Notebook integration

The local HumanOS Notebook is the canonical destination for live capture. Google Drive is a verified backup and readable daily projection. Future import from ChatGPT exports or authorized history connectors must enter through a provenance-labeled ingestion path and may never be confused with live host-observed capture.

## Non-goals

- storing private chain-of-thought;
- feeding the complete ledger into model context;
- treating summaries as verbatim evidence;
- using GitHub as a transcript store;
- inventing inaccessible chats;
- automatic deletion merely because an upload returned success;
- wholesale redesign of the existing Notebook.
