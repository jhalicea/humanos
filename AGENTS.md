# HumanOS repository working agreement

Owner instruction recorded 2026-09-07: follow the SDLC and always use the owner's
repository. The owner plans to give the code to Claude and Gemini for later review.

## Repository and preservation

- Develop the existing HumanOS runtime in https://github.com/jhalicea/humanos.
  Use branches/worktrees of this repository; do not create a competing runtime or
  repository. The installed checkout is <HUMANOS_ROOT>.
- This is the code repository, not the canonical personal record store. Preserve
  HumanOS ownership, Mirror's interface role, and the Life Notebook boundaries.
- Inspect git status, existing implementation, tests, and applicable governing
  records before changing behavior. Preserve uncommitted work and rollback points.
- Keep Notebook transcripts/databases, workspace contents, backups, credentials,
  and private test evidence out of Git, including history and PR attachments.

## Continuity and work-in-progress control

HumanOS has one live cross-chat operational cursor: GitHub issue #67,
`HumanOS Control Room — Current State & Continuation`.

Before meaningful HumanOS implementation or foundation work:

1. Read/reconcile issue #67 when GitHub is available.
2. Read the ACTIVE branch's root `STATUS.md`.
3. Read `docs/foundation/WORKFLOW_STANDARD.md`.
4. Read the ACTIVE work order in `docs/work-orders/`.
5. Inspect the referenced baseline/commit/tests before changing anything.

If issue #67 and `STATUS.md` disagree, stop implementation and reconcile the
conflict from Git/repository evidence. If issue #67 is unavailable, `STATUS.md`
and the active work order are the fallback; do not infer newer state from memory.

Use a strict WIP limit of one ACTIVE implementation slice and one explicit NEXT
ACTION. Other work must be classified as BACKLOG, READY, BLOCKED, PAUSED,
REVIEW, VERIFIED, PROMOTION_PENDING, PROMOTED, or DEFERRED. Starting unrelated
implementation requires the owner to change priority and preserve the prior
slice's resume point.

At the end of meaningful work, preserve exact evidence and update the work order,
branch `STATUS.md` when state changed, and issue #67. Historical evidence belongs
in commits/work orders/reviews; do not turn the Control Room into a transcript.

## SDLC for changes

Follow `docs/foundation/WORKFLOW_STANDARD.md`. The required lifecycle is:
DEFINE -> BASELINE -> DIVIDE -> PLAN -> IMPLEMENT -> TEST -> COMPARE -> VERIFY ->
PROMOTE -> PRESERVE.

1. State the concrete problem, bounded scope, and observable acceptance criteria.
2. Work on a focused branch. Extend existing components and preserve data formats
   unless a justified migration includes recovery and rollback.
3. Run relevant automated tests and real local checks for affected interactions.
   Use isolated test vaults. Never operate tests on the owner's active Notebook.
4. Review the diff for regressions, authority/scope changes, transcript fidelity,
   idempotency, recovery, and accidental private data before committing/pushing.
5. Push the branch and open a pull request with purpose, exact tested commit,
   commands/results, known limitations, and rollback instructions. Report local
   versus remote state truthfully; commits are not automatically uploads.
6. Resolve review findings, rerun affected checks, and record remaining defects.
   Merge/release within the owner's authorization. Preserve an identifiable
   previous release and verify installed behavior after a release.
7. Preserve the tested commit, evidence, state, resume point, and exactly one NEXT
   ACTION in the HumanOS continuity/control surfaces.

Use `python3 -m unittest discover -s tests -v` for the existing automated suite.
Live Ollama checks are separate from tests using simulated model responses.
CI, branch protection, and automatic deployment are not established by this file.

## Independent review

Give reviewers the same immutable commit, requirements, diff, reproduction steps,
and test evidence. Ask for findings tied to files/lines and observable failures.
Track findings and dispositions in the repository. Model agreement is not a test
result; reproduce claims before accepting or dismissing them. Models work
independently before comparison when independence is part of the review design.
The owner will arrange planned hosted-model reviews; do not transmit code or
personal records to those services based only on a statement of future intent,
and never send credentials, secrets, private Notebook paths, or unnecessary
personal information.
