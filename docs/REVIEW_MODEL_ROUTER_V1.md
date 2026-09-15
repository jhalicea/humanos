# HumanOS Model Router v1 — Focused Review Findings

Status: REVIEW IN PROGRESS / BLOCKERS IDENTIFIED
Date: 2026-09-15
Branch: `feature/model-router-v1`
PR: #63

## Review basis

This review applies the HumanOS repository working agreement, Foundation commitments, `docs/security-and-privacy.md`, and `docs/testing-and-evidence.md` to the focused router implementation reconstructed from the locally verified Model Lab checkpoint.

Remote CI on the focused PR has passed the repository-wide regression matrix, including macOS/Linux and Python 3.11/3.13. Passing tests do not by themselves close design or recovery findings.

## Findings

### MRV1-001 — BLOCKER — routing ledger path is not yet governed by HumanOS file-boundary controls

Current `RoutingEventLedger` accepts an arbitrary path and opens it using normal `Path.open("a")`. The current implementation does not explicitly reject a symlink ledger path or symlinked parent, and the CLI exposes `--ledger` directly.

This is inconsistent with HumanOS's existing security principle of rejecting traversal/symlinks in governed file operations. Before merge, the routing ledger must have an explicit local storage boundary and fail closed on unsafe path topology.

Acceptance for closure:
- define the allowed routing-ledger root;
- reject symlink ledger/parent paths;
- use no-follow semantics where the platform supports them;
- add tests proving unsafe paths are rejected before write.

### MRV1-002 — BLOCKER — no single-writer coordination around read/verify/append

Current append performs: read all -> verify chain -> derive sequence/hash -> append. Two processes can race between verification and write and can derive the same sequence/previous hash.

HumanOS documents single-writer coordination as a current durable-state control. The router ledger must either reuse an existing single-writer persistence primitive or add an explicit lock around the entire verification-and-append critical section.

Acceptance for closure:
- concurrent writers cannot create two records from the same previous hash;
- tests reproduce and prevent the race;
- lock failure is surfaced truthfully rather than silently bypassed.

### MRV1-003 — BLOCKER — interrupted final JSONL writes have no defined recovery/reconciliation behavior

`read_all()` decodes each line directly. A process or power loss after a partial append can leave an unterminated or malformed final record; the next read currently fails as a generic JSON error.

HumanOS already contains `recovery_ledger.py`, which parses physical LF-delimited records, fails closed on corrupt complete records, preserves suspect final tails, and provides `validate_recovery_appendable_bytes()` so an append refuses to proceed after an unterminated final record until reconciliation.

The router ledger should reuse this existing recovery behavior or a shared generalized primitive instead of inventing weaker JSONL semantics.

Acceptance for closure:
- partial/unterminated final writes are detected deterministically;
- the original bytes are not silently rewritten or discarded;
- a subsequent append is refused until reconciliation;
- tests cover malformed middle record and interrupted final record behavior.

### MRV1-004 — IMPORTANT — append retry/idempotency semantics are not explicit

The ledger uses `event_id` as `action_id`, but `append()` does not currently define what happens if the same event is retried after an uncertain outcome. A retry can create another ledger record rather than returning/rejecting based on the existing event identity.

Acceptance for closure:
- define whether duplicate identical `event_id` is idempotent success or explicit duplicate rejection;
- reject same ID with different body;
- add restart/retry tests.

### MRV1-005 — IMPORTANT — local routing telemetry directory is not ignored by Git

The default dry-run ledger is `var/model-routing/routing-events.jsonl`, while current `.gitignore` does not ignore that path. Routing evidence could therefore be accidentally staged into the repository.

Acceptance for closure:
- ignore the owner-local routing telemetry directory;
- document that runtime routing evidence is local state, not source code or PR evidence payload.

### MRV1-006 — HOLD — free-text routing context remains outside this implementation increment

Later Model Lab experiments added task descriptions/evidence/assumptions to routing events. Those changes were deliberately excluded from the focused baseline because they had not been locally re-verified and because arbitrary task text may contain private content.

This remains a separate future SDLC increment requiring a data-minimization policy before implementation.

## Positive findings

- Implementation does not modify existing runtime behavior files; it adds a narrow recommendation slice.
- The route remains `v1-candidate`, learning-mode, recommendation-only, and unlocked.
- Model/provider dispatch is absent.
- Authority, automatic execution, and policy promotion are explicitly false.
- Experimental Astra-Light -> Terra-High provenance is not promoted into policy.
- Tamper detection exists for complete, valid ledger records.
- Tests use temporary ledgers rather than the active Life Notebook.

## Current disposition

PR #63 must remain DRAFT. Do not merge or deploy until MRV1-001 through MRV1-003 are closed, MRV1-004/005 are resolved or explicitly dispositioned, the full suite is rerun on the corrected immutable commit, a local dry run is repeated, and independent review is completed.
