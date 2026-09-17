# HumanOS Lean Agile + SDLC Workflow Standard v1

Status: FOUNDATION STANDARD CANDIDATE
Scope: repository work, foundation documents, runtime changes, experiments, reviews, and promotions.

## Purpose

HumanOS uses one workflow, not separate Agile, SDLC, research, and handoff processes. Lean Agile controls flow and work-in-progress; the HumanOS SDLC controls evidence, safety, verification, and promotion.

The workflow is optimized for small reversible slices, human authority, cross-chat continuity, provider neutrality, and reproducible evidence.

## Canonical control surfaces

1. **Live operational cursor:** GitHub issue #67, `HumanOS Control Room — Current State & Continuation`.
2. **Commit-scoped snapshot:** root `STATUS.md` on the active branch.
3. **Acceptance contract:** one active file in `docs/work-orders/`.
4. **Evidence:** tests, CI, commits, diffs, runtime readback, and review artifacts.
5. **Artifact map:** `docs/foundation/ARTIFACT_REGISTER.md`.
6. **Historical/personal record:** Life Notebook, outside the public code repository.

No chat memory, model summary, or informal todo list outranks these surfaces for implementation state.

## Lean Agile flow

HumanOS uses a Kanban-style flow with a strict WIP limit of **one ACTIVE implementation slice**.

Allowed work states:

- `BACKLOG` — captured but not selected.
- `READY` — bounded, acceptance criteria defined, dependencies known.
- `ACTIVE` — the one slice currently being implemented.
- `BLOCKED` — cannot progress until a named condition is resolved.
- `PAUSED` — intentionally preserved while another slice is ACTIVE.
- `REVIEW` — implementation complete enough for diff/security/independent review.
- `VERIFIED` — acceptance criteria and required evidence passed.
- `PROMOTION_PENDING` — verified, awaiting Jon's approval for consequential merge/release.
- `PROMOTED` — approved change merged/released and read back.
- `DEFERRED` — intentionally postponed, not silently abandoned.

Only Jon can change priority when that would replace the ACTIVE slice or authorize consequential promotion.

## Definition of Ready

A slice may enter ACTIVE only when its work order states:

- desired outcome;
- bounded scope and explicit exclusions;
- risks and authority boundary;
- baseline branch/commit;
- observable acceptance criteria;
- affected files/components when known;
- test/evidence plan;
- rollback path;
- one next action.

If these are missing, the task is planning/research, not implementation.

## Unified SDLC

Every ACTIVE slice follows this sequence:

1. **DEFINE** — outcome, scope, exclusions, risks, acceptance tests, done criteria.
2. **BASELINE** — inspect repository truth, tests, branch, commit, and relevant governance.
3. **DIVIDE** — split token-heavy or review work into bounded independent packets when useful.
4. **PLAN** — choose the smallest reversible change and identify rollback/approval gates.
5. **IMPLEMENT** — change only the active slice on its focused branch.
6. **TEST** — cover normal behavior plus relevant failure, restart/recovery, duplication, security, and regression cases.
7. **COMPARE** — compare independent model/reviewer outputs and the real diff against acceptance criteria; consensus is not proof.
8. **VERIFY** — read back files, exact commit, tests/CI, and runtime behavior as applicable.
9. **PROMOTE** — Jon approves consequential merge/release; preserve rollback point.
10. **PRESERVE** — update status/control room, work order, review/evidence, artifact register, and exactly one next action.

A slice cannot skip directly from IMPLEMENT to PROMOTED because a model says it works.

## Cross-chat continuation protocol

At the start of any new HumanOS chat or session:

1. Read issue #67.
2. Read the ACTIVE branch's `STATUS.md`.
3. Read this workflow standard.
4. Read the ACTIVE work order.
5. Inspect referenced evidence before continuing.
6. State the current ACTIVE slice and NEXT ACTION internally; do not create a second active stream unless Jon changes priority.

If the live issue and branch snapshot disagree, stop implementation and reconcile the conflict using Git history and evidence.

At the end of every meaningful work session:

- update the work order with verified progress and remaining gaps;
- update `STATUS.md` if the branch state changed;
- replace the body of issue #67 with the current cursor;
- record the exact tested commit and evidence status;
- preserve paused/deferred items without turning them into active work;
- leave exactly one NEXT ACTION.

This makes continuation repository-driven rather than memory-driven.

## Work-order rule

Every implementation or consequential research slice uses a stable ID such as `HOS-FND-001` or `HOS-MAL-001`. The work order is the slice contract. It must distinguish:

- proposal vs implemented behavior;
- local evidence vs external claims;
- current scope vs deferred ideas;
- owner-approved actions vs pending approvals.

## Artifact rule

Every durable artifact belongs to one category in the artifact register: governance, architecture, work order, implementation, test/evidence, review, release/rollback, research, or operational cursor. New durable documents are registered instead of creating untracked parallel folders or informal ledgers.

## Multi-model workflow

For meaningful HumanOS work, independent models may be used for bounded coding, architecture, challenge, security, or review packets. Requirements:

- same necessary context and acceptance criteria;
- models do not see each other's answers before committing their own;
- raw outputs are preserved when they are part of formal evidence;
- provider/model/version, timestamp, task, role, latency, usage/cost when exposed, and estimates when unavailable are recorded where applicable;
- outputs remain PROPOSALS until repository evidence verifies them;
- never send hosted models credentials, secrets, private Notebook paths, or unnecessary personal information.

## Evidence and promotion gates

`VERIFIED` requires the evidence named by the work order. Typical evidence includes:

- relevant automated tests passing;
- full regression suite when the change can affect shared behavior;
- CI on the exact commit;
- diff/security review;
- runtime readback for runtime claims;
- known defects and limitations recorded.

A green CI run proves only what that CI actually tests.

Consequential merge, release, destructive changes, security-boundary changes, privacy changes, financial/legal/public actions, and external actions require Jon's approval.

## No-loose-workflow rule

The following are not independent sources of truth:

- chat todo lists;
- model memory;
- temporary scratchpads;
- duplicated backlog documents;
- undocumented branches;
- unreferenced review files;
- private notes copied into the public repository.

Capture a useful idea once in the Control Room/backlog or applicable work order, classify its state, and link any durable artifact in the register.

## Completion rule

A slice is done only when acceptance criteria are satisfied, evidence is preserved, the operational cursor is updated, rollback is known, and the next action is explicit. `PROMOTED` additionally requires owner approval and post-promotion verification where applicable.
