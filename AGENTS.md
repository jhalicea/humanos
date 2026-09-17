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

## Context-aware continuity and workstream routing

HumanOS does not assume one global ACTIVE task. Multiple workstreams may coexist.
Before meaningful HumanOS implementation, research, or foundation work:

1. Read/reconcile GitHub issue #67 when GitHub is available. It is the global
   routing/index control plane, not a historical source of proof.
2. Load `config/context_registry.public.json` and any explicitly configured private
   overlay through `context_registry.py`.
3. Resolve the request to a workspace/security context first.
4. Search related workstreams in that workspace and classify the request as
   `CONTINUE`, `EXTEND`, `CREATE_SEPARATE`, or `AMBIGUOUS`.
5. Tell Jon what existing work was found and why before implementation.
6. Read the selected workstream branch `STATUS.md`/work order/evidence as applicable.
7. Inspect the referenced baseline, commit, diff, and tests before changing anything.

Do not require a magic phrase such as “continue HumanOS.” Routing is topic-driven.

If the workspace is ambiguous, especially between personal, employer, client, or
other private contexts, stop and ask for confirmation. Never silently borrow
workspace-private data from another workspace. General techniques may be reusable;
workspace-specific source code, documents, prompts, credentials, private paths,
business data, Notebook content, and proprietary artifacts are isolated by default.

The public registry contains safe aliases and non-sensitive HumanOS metadata.
Sensitive client/employer identities and local roots belong in a private overlay
outside Git. A private overlay may add metadata/workspaces/workstreams, but may not
redefine a public workspace or weaken the schema-v1 cross-workspace DENY policy.

## Work-in-progress and conflict control

HumanOS may have many OPEN/PAUSED/READY/UNKNOWN workstreams. The execution rule is:

- one focused implementation slice per selected workstream/session;
- one explicit next action for that selected slice;
- before editing, check for overlapping components in other concurrent workstreams
  on the same repository;
- overlapping `ACTIVE`, `REVIEW`, or `PROMOTION_PENDING` work requires reconciliation
  before modifying the same components;
- unfinished unrelated work does not block Jon from intentionally selecting another
  workstream.

Work states are defined in `docs/foundation/WORKFLOW_STANDARD.md`.

At the end of meaningful work, preserve exact evidence and update the selected work
order, branch `STATUS.md` when state changed, the registry when routing metadata or
resume state changed, and issue #67 when the global index/session focus changed.
Historical evidence belongs in commits/work orders/reviews; do not turn issue #67
into a transcript.

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
   idempotency, recovery, cross-workspace leakage, and accidental private data.
5. Push the branch and open a pull request with purpose, exact tested commit,
   commands/results, known limitations, and rollback instructions. Report local
   versus remote state truthfully; commits are not automatically uploads.
6. Resolve review findings, rerun affected checks, and record remaining defects.
   Merge/release within the owner's authorization. Preserve an identifiable
   previous release and verify installed behavior after a release.
7. Preserve tested commit, evidence, selected workspace/workstream, resume point,
   and one next action for that workstream.

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
and never send credentials, secrets, private Notebook paths, client/employer data,
or unnecessary personal information.
