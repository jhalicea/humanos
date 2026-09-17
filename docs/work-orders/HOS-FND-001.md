# HOS-FND-001 — Foundation Workflow & Cross-Chat Continuity

Status: ACTIVE
Branch: `foundation/workflow-continuity-v1`
Live operational cursor: GitHub issue #67
Owner instruction: organize HumanOS so Agile, SDLC, artifact tracking, and cross-chat continuation operate as one coherent workflow with no loose parallel processes.

## Outcome

Create a minimal control plane that lets a new HumanOS chat/session reliably recover the current implementation state from repository evidence instead of conversational memory, while enforcing one ACTIVE slice and one NEXT ACTION.

## Baseline

- Base branch: `runtime-0.1`
- Baseline commit: `9ddc6477bba70dd4c86104a0565da848d7cbacff`
- Foundation Contract v0.1 is ratified but incrementally implemented.
- `AGENTS.md` already defines repository preservation and core SDLC rules.
- Work orders, reviews, CI, and documentation exist, but no single live operational cursor/WIP state model previously tied them together.
- HOS-MAL-001 is preserved on `experiment/webllm-inspired-model-loader` at reviewed commit `018c9c57e40e91395defe6222f38bd2b99c83905` and is PAUSED while this slice is ACTIVE.

## Scope

Included:

- one live cross-chat Control Room issue;
- one commit-scoped root `STATUS.md` fallback/snapshot;
- one unified Lean Agile + HumanOS SDLC workflow standard;
- strict WIP limit of one ACTIVE implementation slice;
- explicit state vocabulary and Definition of Ready/Done;
- one artifact register and placement rules;
- start-of-session and end-of-session continuation procedure;
- update `AGENTS.md` so repository work follows the continuity/control-plane rules;
- documentation index links;
- preserve paused/deferred work with explicit resume points.

Excluded:

- modifying runtime behavior;
- changing the Life Notebook storage model;
- automatic ChatGPT memory synchronization;
- automatic GitHub issue updates by local HumanOS runtime;
- merging/promoting without Jon approval;
- resuming the model-loader implementation in this slice;
- creating a second backlog/project-management system.

## Lean Agile model

Use Kanban-style flow with `BACKLOG`, `READY`, `ACTIVE`, `BLOCKED`, `PAUSED`, `REVIEW`, `VERIFIED`, `PROMOTION_PENDING`, `PROMOTED`, and `DEFERRED` states. Exactly one implementation slice may be ACTIVE. Issue #67 holds the live cursor. Work orders hold slice contracts. Evidence lives in commits/tests/CI/reviews/runtime readback.

## Acceptance criteria

1. GitHub issue #67 exists and identifies one ACTIVE slice, one NEXT ACTION, paused/deferred work, branch, and evidence references.
2. Root `STATUS.md` documents the same active slice and continuation fallback without becoming a competing live ledger.
3. `docs/foundation/WORKFLOW_STANDARD.md` unifies Agile flow, WIP=1, SDLC, continuation, multi-model review, evidence, and promotion gates.
4. `docs/foundation/ARTIFACT_REGISTER.md` maps durable artifacts and forbids a second operational status ledger.
5. `AGENTS.md` requires HumanOS work to read/reconcile Control Room + STATUS + active work order before implementation and update continuity state after meaningful work.
6. `docs/index.md` links the new foundation workflow/control documents.
7. No runtime source code or Notebook data is changed by this slice.
8. Full regression CI remains green on the exact branch commit.
9. Diff review confirms no conflicting workflow authority, privacy regression, or second source of truth was introduced.
10. Control Room issue #67 is updated with the exact tested commit and the single next action after verification.

## Risks and controls

- **Drift between issue and STATUS:** issue is live cursor; STATUS is commit snapshot. Any conflict stops implementation until reconciled.
- **Issue unavailable offline:** STATUS + work order provide fallback; do not guess newer state.
- **Process overhead:** WIP=1 and one NEXT ACTION keep the control plane intentionally small.
- **Repository pollution:** project metadata only; private Life Notebook/personal evidence remains outside Git.
- **False continuity claim:** a new chat still has to read issue #67/repo evidence; this workflow does not claim invisible automatic memory transfer.

## Rollback

Before promotion, rollback is branch deletion. Issue #67 can be updated to point back to the previously active preserved slice. No production runtime data is modified.

## Verification plan

- inspect final diff against baseline;
- confirm files/links/state terminology are internally consistent;
- run `python3 -m unittest discover -s tests -v` through CI on the exact commit;
- confirm no runtime files changed;
- update issue #67 with exact commit and CI result.

## Next action

Complete the foundation files and `AGENTS.md`/docs-index integration, commit atomically, run CI, review the diff, then update issue #67. Do not merge until Jon approves promotion.
