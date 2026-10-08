# HumanOS repository working agreement

Owner instruction recorded 2026-09-07: follow the Software Development Life Cycle (SDLC) and always use the owner's repository. The owner plans to give the code to Claude and Gemini for later review.

## Repository and preservation

- Develop the existing HumanOS runtime in https://github.com/jhalicea/humanos.
  Use branches/worktrees of this repository; do not create a competing runtime or
  repository. The installed checkout is <HUMANOS_ROOT>.
- This is the code repository, not the canonical personal record store. Preserve
  HumanOS ownership, Mirror's interface role, and the Life Notebook boundaries.
- Inspect git status, existing implementation, tests, and applicable governing
  records before changing behavior. Preserve uncommitted work and rollback points.
- Keep Notebook transcripts/databases, workspace contents, backups, credentials,
  and private test evidence out of Git, including history and Pull Request (PR)
  attachments.

## Architecture and product boundaries

Before architecture, repository-layout, data-boundary, security-boundary, or
cross-product changes, read:

- `docs/architecture/HUMANOS_ARCHITECTURE_BASELINE_PLAN.md`
- `docs/architecture/LOCAL_DEVELOPMENT_WORKSPACE_POLICY.md`
- `docs/architecture.md`
- `docs/foundation/WORKFLOW_STANDARD.md`

HumanOS and BodyFixOS are separate software products. BodyFixOS must not become a
HumanOS package, subdirectory, shared database namespace, private-state subtree, or
direct internal import. A future relationship is allowed only through an explicit,
versioned external connector / Application Programming Interface (API) contract
with independently approved permissions and data scope.

Do not describe a rule as enforced merely because a document states it. Distinguish
DOCUMENTED, IMPLEMENTATION-CONFIRMED, TESTED, ENFORCED, INFERRED, UNKNOWN,
CONTRADICTED, and OBSOLETE evidence states where the distinction matters.

HumanOS uses GREEN / AMBER / RED for its authority/delegation axis. Do not reuse
those colors for architecture reversibility. Architecture uses Reversibility Class
R1 (two-way door), R2 (coordinated/recoverable), and R3 (one-way or
expensive-to-reverse). R3 changes never become independently Artificial
Intelligence (AI)-executable; explicit human ratification is required.

Delegated architecture/governance work must include a Judgment Disclosure that
separates mechanical changes from judgments, alternatives, assumptions,
reversibility, evidence state, and owner-ratification requirements.

## Development headquarters and AI-assisted team (candidate rules)

HOS-ARCH-001 proposes `~/Developer` as the single **developer navigation root** with
`10_Repos` for canonical repositories, `20_Worktrees` for assigned Git worktrees,
`30_Labs` for experiments, `40_Artifacts` for bounded reports, `50_Imports`
for intake, and `90_Archive` for retained old material. Check the actual
owner-machine path and current Git identity before assuming this target layout is
already installed; the local `00_Map.md` is **unverified**. Use the public-safe
`docs/architecture/DEVELOPER_ROOT_MAP_TEMPLATE.md` only as a template.

This one human + AI-assisted engineering model defines *functions before agents*:
owner/product/architecture approval, scoped research, implementation, tests,
security review, and release verification. One model may fill multiple functions
when appropriate, but must not self-grant capability, self-ratify governance,
or claim an independent reviewer or live AI staff exists without evidence.

Before an expensive model/tool/artifact operation, route and budget the work:
reuse local/deterministic operations for simple verification, choose the least
expensive capable model **only when model selection is actually exposed**, and
escalate complexity or resource use when evidence, failed attempts, or the
owner's explicit choice justifies it. Do not spawn speculative workers or
request needless parallel model consensus. Keep granted data, tool scope, costs,
risk lane, reversibility and next action clear in the selected work order.

The inventory script is *not* an authority to clean the Mac. Its default scan
must stay within `~/Developer` and its private reports in scoped
`40_Artifacts`. Never move or prune worktrees, delete historical folders,
alter runtime databases, or assume disaster recovery is qualified without
explicit human approval plus real owner-host/restore evidence. Private
Notebook, secrets, and application-managed model/VM assets remain outside
the public source repository.

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
5. Push the branch and open a Pull Request (PR) with purpose, exact tested commit,
   commands/results, known limitations, and rollback instructions. Report local
   versus remote state truthfully; commits are not automatically uploads.
6. Resolve review findings, rerun affected checks, and record remaining defects.
   Merge/release within the owner's authorization. Preserve an identifiable
   previous release and verify installed behavior after a release.
7. Preserve tested commit, evidence, selected workspace/workstream, resume point,
   and one next action for that workstream.

Use `python3 -m unittest discover -s tests -v` for the existing automated suite.
Live Ollama checks are separate from tests using simulated model responses.
Continuous Integration (CI), branch protection, and automatic deployment are not
established by this file.

## Teaching terminology

When HumanOS or the Academy explains technical material, expand an acronym or
abbreviation on its first meaningful use, for example `MVC (Model-View-Controller)`
or `CI (Continuous Integration)`. Do not use opaque status shorthand such as
`CI GREEN`; write `Continuous Integration checks passed` or, after expansion,
`CI checks passed`. The detailed rule lives in
`docs/academy/HUMANOS_TEACHING_PROTOCOL.md`.

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
