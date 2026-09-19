# HOS-EXEC-INTEGRITY-001 — Execution / Input Integrity

Status: PROMOTED / CANONICAL MERGE VERIFIED  
Branch: `fix/exec-integrity-paste-framing-v1`  
Baseline: `2d4b383c6723177a3d1ad6ef3774d79dc8e6b7cd` (`runtime-0.1`)

## Objective

Prevent a large multiline terminal paste from being fragmented into multiple HumanOS turns when later TTY chunks are not immediately buffered. Fragmentation can create unintended transactions and visually interleave runtime/context notices with the remaining pasted text.

## Evidence

The observed session began with 22 unfinished execution transactions and showed runtime metadata such as `Context route:` appearing inside the visual body of a long pasted message. Current `read_human_input` waited briefly for the first extra line but used a zero-time poll after every subsequent line, so a delayed TTY refill could terminate capture prematurely.

## Approved scope

1. Preserve normal one-line input behavior.
2. Preserve explicit `:paste` / `/send` framing.
3. Once automatic multiline paste is detected, wait through a bounded idle window for later TTY refills.
4. Add a deterministic regression reproducing a delayed second refill.
5. Rely on existing transaction/recovery regressions for duplicate transaction prevention, resumable model outage, preserved tool results, unfinished-turn coexistence, and delivery idempotency.
6. Do not delete, close, or mutate the already-existing unfinished transactions.
7. Do not expand into Work Order automation, FRIEND routing, model routing, or BodyFixOS.

## Acceptance criteria

- A simulated delayed terminal refill remains one exact HumanOS message.
- Blank lines and leading whitespace remain unchanged.
- Explicit paste mode remains unchanged.
- Existing transaction/resume/replay tests remain green.
- No destructive recovery or migration occurs.

## Rollback

Revert promotion commit `eca9652cef75962b98cc60e314f952f8e56bcd1b` if rollback is required. No Notebook data migration is part of this slice.

## Verification and promotion evidence

- Candidate head: `0a3f01fa1fe60a4d3c8a63979d918e18517b4a2f`
- Regression run `35409587970`: SUCCESS across Ubuntu 24.04/macOS 15 × Python 3.11/3.13; representative job ran 472 tests with 8 skipped and no failures.
- Encrypted-backup/full-suite run `35409587986`: SUCCESS across Ubuntu 24.04/macOS 15 × Python 3.11/3.13.
- Owner approved promotion on 2026-09-18.
- Promotion PR: #86.
- Canonical merge commit: `eca9652cef75962b98cc60e314f952f8e56bcd1b`.
- `runtime-0.1` was verified identical to the merge commit immediately after promotion.
- No Notebook migration, transaction deletion, task close, release, or tag was performed.

## Next candidate

Execution Work Order schema + FRIEND packet schema + stale-baseline check.
