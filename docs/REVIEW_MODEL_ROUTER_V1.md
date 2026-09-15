# HumanOS Model Router v1 — Focused Review Findings

Status: REVIEW IN PROGRESS / CORRECTIVE CHANGES IMPLEMENTED / LOCAL RE-VERIFICATION PENDING
Date: 2026-09-15
Branch: `feature/model-router-v1`
PR: #63

## Review basis

This review applies the HumanOS repository working agreement, Foundation commitments, `docs/security-and-privacy.md`, and `docs/testing-and-evidence.md` to the focused router implementation reconstructed from the locally verified Model Lab checkpoint.

The initial focused implementation passed the repository-wide GitHub Actions matrix. The review then identified durability and file-boundary gaps that passing tests had not covered. Corrective code and regression tests were added; those corrections must be treated as unverified locally until the owner reruns the prescribed suite and dry run on the final candidate commit.

## Findings and disposition

### MRV1-001 — BLOCKER -> CANDIDATE FIX IMPLEMENTED — routing-ledger file boundary

Finding: the original `RoutingEventLedger` accepted a path and used normal file opening without explicit no-follow protection.

Corrective implementation:
- ledger path, ledger directory, and lock path reject direct symlinks;
- ledger/lock opens use `O_NOFOLLOW` when available and verify regular-file type with `fstat`;
- reads also use the safe no-follow file descriptor path rather than `Path.read_bytes()`;
- regression tests cover symlink ledger file, symlink ledger directory, and symlink lock file.

Remaining gate: local owner verification on the final candidate commit plus final diff review.

### MRV1-002 — BLOCKER -> CANDIDATE FIX IMPLEMENTED — single-writer coordination

Finding: original append performed read -> verify -> derive sequence/hash -> append without a process lock.

Corrective implementation:
- POSIX `flock` protects the full read/verify/append critical section;
- lack of locking support fails closed rather than silently bypassing coordination;
- reads take a shared lock and appends take an exclusive lock;
- a multiprocess regression test launches concurrent writers and requires one valid sequential hash chain.

Remaining gate: local owner verification on the final candidate commit. Portability beyond the current POSIX local targets remains a documented limitation rather than a silent fallback.

### MRV1-003 — BLOCKER -> CANDIDATE FIX IMPLEMENTED — interrupted JSONL tail semantics

Finding: original `read_all()` could encounter a partial final write without a defined reconciliation boundary.

Corrective implementation:
- the router ledger reuses HumanOS `recovery_ledger.validate_recovery_appendable_bytes()` before parsing/appending;
- an unterminated physical record or malformed complete record fails closed;
- original bytes are left untouched;
- tests prove an unterminated tail and malformed complete record block later appends without mutation.

This intentionally chooses fail-closed reconciliation rather than silently repairing or deleting evidence.

Remaining gate: local owner verification on the final candidate commit.

### MRV1-004 — IMPORTANT -> CANDIDATE FIX IMPLEMENTED — retry/idempotency semantics

Finding: original append did not define duplicate `event_id` behavior.

Corrective implementation:
- an existing equivalent event ID is treated as idempotent success;
- `created_at` is excluded from logical retry comparison so a retry after an uncertain outcome does not duplicate solely because its wall-clock timestamp changed;
- the same event ID with materially different content fails closed with `RoutingLedgerConflict`;
- tests cover both cases.

Remaining gate: local owner verification and independent review of whether the logical-equivalence rule is sufficiently narrow.

### MRV1-005 — IMPORTANT -> CANDIDATE FIX IMPLEMENTED — routing telemetry Git boundary

Finding: `var/model-routing/` was not ignored by Git.

Corrective implementation:
- `.gitignore` now excludes `var/model-routing/`;
- routing telemetry remains owner-local runtime evidence rather than source-code or PR payload.

Remaining gate: verify the local dry run does not appear in `git status`.

### MRV1-006 — HOLD — free-text routing context remains outside this increment

Later Model Lab experiments added task descriptions/evidence/assumptions to routing events. Those changes remain deliberately excluded from this focused baseline because arbitrary task text may contain private content and because that later experiment had not been locally re-verified.

This remains a separate future SDLC increment requiring a data-minimization policy and its own acceptance criteria.

## Positive findings

- Implementation is isolated on `feature/model-router-v1`, based on `runtime-0.1`; Model Lab PR #62 has been restored to a research-only boundary.
- Router policy remains `v1-candidate`, learning-mode, recommendation-only, and unlocked.
- Model/provider dispatch is absent.
- Authority, automatic execution, and policy promotion are explicitly false.
- Experimental Astra-Light -> Terra-High provenance is not promoted into policy.
- The router ledger uses existing HumanOS audit hash primitives and now reuses the existing recovery append validator rather than defining weaker tail semantics.
- Tests use temporary ledgers rather than the active Life Notebook.
- Local routing telemetry is excluded from Git.

## Verification state

Historical source checkpoint `d932808409ddec353341bb769b5e45d21d7596d7`:
- owner-local targeted suite: 20/20 PASS;
- owner-local no-dispatch dry run: ledger recorded + verified, no dispatch, no authority.

Focused PR #63 before corrective review changes:
- GitHub Actions repository-wide matrix: PASS.

Current corrective candidate:
- macOS 15 / Python 3.11 GitHub Actions full suite observed: **418 tests, OK, 8 skipped**;
- routing safety/concurrency/retry regression tests observed passing in that full run;
- remaining GitHub Actions matrix jobs must complete successfully;
- owner-local full-suite and dry-run verification on the final candidate commit are still required.

## Current disposition

PR #63 remains **DRAFT**. The original blockers now have candidate fixes, but they are not considered closed for release until:

1. all current GitHub Actions jobs pass on the same immutable head;
2. the owner runs `python3 -m unittest discover -s tests -v` on that head;
3. the owner repeats the local no-dispatch dry run and confirms ledger verification plus a clean Git status for `var/model-routing/`;
4. the focused diff is reviewed again after all corrective commits;
5. independent review is performed against the same immutable commit;
6. findings are dispositioned and affected tests rerun;
7. the owner explicitly approves merge/release.
