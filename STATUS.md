# HumanOS Status Snapshot

Status: HOS-LN-001 ACTIVE / PRE-LN-1 SCHEMA-INTEGRITY ADR REMEDIATED CANDIDATE / FINAL CI+REVIEW REQUIRED / LN-1 NOT STARTED
Date: 2026-09-30
Workspace: `WS-HUMANOS`
Project: Life Notebook
Workstream: `HOS-LN-001 — PRE-LN-1 Schema / Integrity ADR`
Branch: `life-notebook-ln1-schema-integrity`
Baseline: `life-notebook-ln0` at `85e0308e19a9c145fa44bd922c2010bd87675658`
Parent workstream: `HOS-LN-000` CLOSED / LN-0 IMPLEMENTATION-READY
Work order: `docs/work-orders/HOS-LN-001.md`
Primary ADR: `docs/life-notebook/ADR-LN-014_SCHEMA_INTEGRITY.md`

## Routing / continuation

The owner requested continuation from the current Life Notebook checkpoint. Repository
evidence showed HOS-LN-000 closed on 2026-09-28 with the next authorized action:
PRE-LN-1 architecture resolution beginning with the Schema / Integrity ADR.

This workstream remains bounded to that first PRE-LN-1 gate. No LN-1 implementation,
live writer change, owner Notebook migration, or PR merge is authorized.

## Current outcome

The latest remediated ADR candidate now defines:

- immutable `NotebookEventV1.event_hash` coverage and exclusions;
- HumanOS-normalized content-free immutable metadata rules;
- keyed/versioned structural event-chain integrity;
- `payload_commitment = null` for LN-1 V1;
- unique opaque `payload_object_id` as the immutable event-to-payload binding;
- one-to-one event↔payload linkage verified in both directions;
- exact payload-byte semantics with no hidden Unicode/serialization normalization;
- erasable keyed LIVE payload integrity binding exact bytes to exact `object_id` /
  `event_id`, immutable payload metadata, and exact `content_integrity_key_id`;
- fail-closed historical content-integrity key selection with no guessing/fallback;
- one authoritative event/payload/idempotency transaction boundary with explicit
  pre-commit and commit-before-ack crash semantics;
- authenticated effective-source idempotency with transient content fingerprinting
  only while LIVE;
- post-erasure retry behavior that cannot silently recreate content;
- event-chain validity after payload erasure without history rewrite;
- V-04 ErasureTag separation from original event integrity;
- restore quarantine plus event/payload/key-version/deletion-checkpoint reconciliation;
- migration rules preventing legacy plaintext-derived hashes or inadmissible
  descriptive metadata from becoming immutable LN-1 event history.

## Independent review record

### Pass 1

Three blockers were preserved on PR #117 before remediation:

1. LIVE payload integrity authenticated bytes but not event/object identity;
2. event/payload/idempotency atomic creation was not specified;
3. immutable metadata had no explicit content-free admissibility rule.

Remediation commit:
`4d082fcfe1b02bc38bc32a5e3e1700c0bad6b527`.

### Pass 2

Fresh review at `f08eb60681ee72b805aa6779ce47e756549e349d` found one additional
schema blocker: `content_integrity_key_id` was used to select the LIVE payload HMAC
key but was neither a required payload field nor MAC-authenticated. This would make
historical verification across key rotation ambiguous and leave the selector open to
substitution/downgrade ambiguity.

The finding was preserved on PR #117 before remediation.

Key-version remediation commit:
`e715af891d05cf092475d3b244ad087d429787c7`.

The ADR now requires the selector while LIVE, authenticates it inside the payload MAC
envelope, fails closed for unknown/unavailable/malformed selectors, forbids guessing or
fallback, removes the selector with erased payload-integrity state by default, and
requires tamper/unknown-key/historical-key-rotation implementation tests.

A final clean review of the exact remediated ADR commit is still required before owner
acceptance.

## CI evidence

Initial ADR head:
`87e04d27fbc40061cbdafc8481e6f4234e0161c6`.

At that head, the two general workflow families failed because current GitHub runners
did not have the SQLCipher CLI required by two already-existing LN-0 cross-V tests.
This was classified as verification-harness/environment evidence, not ADR rejection.

Harness-only repair commits:

- `d07a98f7510ab0e5a9b5b595dc9b5642d03a6067` — regression matrix;
- `a97aa8d37afe85485fdc772b6366bf3681a900dc` — encrypted-backup matrix.

Both workflow families completed SUCCESS at:

- `a97aa8d37afe85485fdc772b6366bf3681a900dc`;
- `f08eb60681ee72b805aa6779ce47e756549e349d`.

A final fresh CI result is required at the branch head containing the latest ADR,
work-order, and status remediation records.

## Preserved invariants

- HumanOS remains local-first authority.
- Ingestor remains sole kernel writer.
- Exact transcript fidelity and read-back-before-checkpoint remain required.
- Each event owns one independently deletable payload object.
- No normal plaintext-derived payload digest may survive `ERASE.COMPLETED` in governed
  persistent stores in scope.
- Immutable metadata may not be used as a content/PII smuggling channel.
- LIVE integrity key selection is explicit and authenticated; no silent fallback.
- Promoted V-03/V-04/V-05 evidence is unchanged.
- `runtime-0.1`, live capture, and owner Notebook data are unchanged.

## Explicit non-claims

This branch does not claim:

- LN-1 implementation has started;
- the production SQLCipher Python binding is selected;
- Keychain/KDF/wrapping/recovery/rotation/historical-key policy is solved;
- backup transport/custody is solved;
- migration/cutover is approved;
- production integration is qualified;
- ADR-LN-014 is accepted.

## Evidence state

Baseline branch head:
`85e0308e19a9c145fa44bd922c2010bd87675658`.

HOS-LN-001 work-order creation commit:
`899da1fbc0d124345fe9c0249bc3bc8cd9cbe2fe`.

ADR-LN-014 original candidate creation commit:
`af7837d6178f3ab66f0fb66f3cbe72c345260ac7`.

CI harness repair head with both workflow families passing:
`a97aa8d37afe85485fdc772b6366bf3681a900dc`.

First ADR review-remediation commit:
`4d082fcfe1b02bc38bc32a5e3e1700c0bad6b527`.

Second review key-version remediation ADR commit:
`e715af891d05cf092475d3b244ad087d429787c7`.

Updated work-order record after second review:
`5c96fdc296aa60138df4db8c61e69038665f3d07`.

No runtime implementation source was changed by HOS-LN-001.

## Remaining acceptance gates

- [ ] Fresh CI passes at the final candidate branch head.
- [ ] Fresh independent architecture/security review of ADR commit
      `e715af891d05cf092475d3b244ad087d429787c7`.
- [ ] Resolve any new reproducible schema blocker if found.
- [ ] Record the immutable reviewed commit/evidence.
- [ ] Jon explicitly accepts ADR-LN-014 for PRE-LN-1 use.

Only after this ADR is accepted may the program proceed to the separate SQLCipher
Runtime Binding + Key Custody ADR and controlled Migration / Cutover Plan. None of
those gates alone authorizes a LIVE Notebook writer; production integration
qualification remains required.

## Rollback

Revert HOS-LN-001/ADR/STATUS changes and the two CI-harness commits, or close/delete
the branch before promotion. `life-notebook-ln0`, `runtime-0.1`, promoted LN-0
evidence, and owner Notebook data remain untouched.

## Next action

Obtain fresh CI at the current final branch head, then perform a clean independent
review of ADR commit `e715af891d05cf092475d3b244ad087d429787c7` against frozen LN-0,
V-03/V-04 evidence, Runtime 0.1 integrity behavior, and HOS-LN-001 acceptance criteria.
If no blocker remains, preserve the review result and present the exact reviewed ADR
commit to the owner for explicit PRE-LN-1 acceptance.
