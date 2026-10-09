# HumanOS Lean Agile + SDLC Workflow Standard v1.2

Status: FOUNDATION STANDARD CANDIDATE
Scope: repository work, foundation documents, runtime changes, experiments, reviews, and promotions.

## Purpose

HumanOS uses one coherent workflow, but many workstreams may coexist. Lean Agile
controls flow and work-in-progress inside the selected workstream; the HumanOS SDLC
controls evidence, safety, verification, and promotion.

The workflow is optimized for small reversible slices, human authority, topic-aware
continuity, workspace isolation, provider neutrality, and reproducible evidence.

## Context hierarchy

Development work is routed through:

`OWNER -> WORKSPACE -> PROJECT -> WORKSTREAM -> WORK ORDER -> BRANCH -> SLICE -> EVIDENCE`

The workspace is a security and ownership boundary. Workspaces support HumanOS
internal work, personal work, businesses, employers, clients, experiments, and
research. The development registry is a precursor to the future HumanOS Context Layer.

## Canonical control surfaces

1. **Global router/index:** GitHub issue #67. It points to registry/workstreams and
   current session focus; it is mutable and is not historical proof.
2. **Public workspace/workstream registry:** `config/context_registry.public.json`.
3. **Private overlay:** external/local file selected by
   `HUMANOS_CONTEXT_PRIVATE_REGISTRY`; never committed.
4. **Commit-scoped branch snapshot:** root `STATUS.md` on the selected branch.
5. **Acceptance contract:** applicable file in `docs/work-orders/`.
6. **Evidence:** tests, CI, commits, diffs, runtime readback, and review artifacts.
7. **Artifact map:** `docs/foundation/ARTIFACT_REGISTER.md`.
8. **Historical/personal record:** Life Notebook, outside the public code repository.

Chat memory, model summaries, and informal todo lists do not establish implementation truth.


## GitHub synchronization and publication gate

- `https://github.com/jhalicea/humanos` is the shared public **code/documentation**
  remote; local Git in that same repository and its worktrees is the valid isolated
  execution workspace. A local commit is not a remote push, PR, merge, or release.
- For a bounded, reviewable, public-safe change: commit on a focused branch, check
  the entire proposed commit range and history for sensitive material, push the
  exact candidate, verify the remote head SHA, and open a draft PR with evidence
  and limits. Keep unrelated dirty/untracked data untouched; record what is still
  local/unpushed. A PR and passing CI do not authorize merge or deployment.
- Because the remote is public, **never push** Notebook transcripts, personal
  records, client/employer data, credentials, private paths, backups, embeddings,
  private prompts, or raw operational logs, including in commits, history, tests,
  issues, or PR attachments. If classification is uncertain, stop publication,
  keep the artifact local/protected, and obtain an explicit owner destination and
  disclosure decision. A private GitHub repository is not by itself consent to
  upload private HumanOS records.
- Reuse existing registered status, work order, registry, and issue #67; do not
  create a parallel sync log or project tracker.


## Topic-aware routing before implementation

For every meaningful request:

1. **Resolve workspace first.** Use explicit context when supplied. If personal,
   employer, client, or other private contexts are ambiguous, ask before proceeding.
2. **Discover related work.** Search the registry plus relevant branches/work orders,
   issues, docs, and evidence inside that workspace.
3. **Classify the request:**
   - `CONTINUE` — resume a strong match to unfinished/resumable work.
   - `EXTEND` — related work exists but the request adds a distinct capability.
   - `CREATE_SEPARATE` — a new bounded stream is appropriate; preserve links to
     related work instead of duplicating it.
   - `AMBIGUOUS` — more than one workspace/workstream is plausible; confirmation
     is required before implementation.
4. **Report what was found** and why before changing files.
5. **Inspect the selected stream** and only then enter the SDLC.

No magic continuation phrase is required.

## Workspace isolation

Schema v1 is fail-closed:

- public/private workspaces have explicit confidentiality classes;
- cross-workspace policy is `DENY`;
- workspace-specific code, documents, prompts, business data, credentials, paths,
  Notebook content, and proprietary artifacts never cross boundaries implicitly;
- general techniques and public knowledge may be reused without carrying private
  workspace content;
- explicit owner authorization is required for any cross-workspace transfer;
- private overlay metadata may add local/private context but may not redefine a
  public workspace or weaken the DENY policy;
- public snapshots must not serialize private-overlay identities or local roots.

## Lean Agile flow and WIP

HumanOS uses a Kanban-style state model:

- `BACKLOG` — captured but not selected.
- `READY` — bounded, acceptance criteria defined, dependencies known.
- `ACTIVE` — currently being implemented in its own workstream.
- `BLOCKED` — cannot progress until a named condition is resolved.
- `PAUSED` — intentionally preserved with a resume point.
- `REVIEW` — implementation complete enough for formal review.
- `VERIFIED` — acceptance criteria and required evidence passed.
- `PROMOTION_PENDING` — verified and awaiting Jon's promotion decision.
- `PROMOTED` — approved merge/release and readback complete.
- `DEFERRED` — intentionally postponed.
- `UNKNOWN` — branch/workstream exists but status is not yet established by evidence.
- `ARCHIVED` / `SUPERSEDED` — retained for provenance, not active mutation.

There is **no global WIP=1 rule**. Multiple workstreams can remain open or active
across separate areas. The operational limit is one focused implementation slice
per selected workstream/session.

Before concurrent edits in the same repository, compare declared component scopes.
Overlapping components in another `ACTIVE`, `REVIEW`, or `PROMOTION_PENDING`
workstream must be reconciled before editing.

## Definition of Ready

A slice may enter implementation only when its work order or equivalent contract states:

- workspace and workstream identity;
- desired outcome;
- bounded scope and explicit exclusions;
- risks and authority boundary;
- baseline branch/commit;
- observable acceptance criteria;
- affected files/components when known;
- test/evidence plan;
- rollback path;
- one next action for that slice.

## Unified SDLC

Each selected implementation slice follows:

1. **DEFINE** — outcome, scope, exclusions, risks, acceptance tests, done criteria.
2. **BASELINE** — inspect repository truth, registry, tests, branch, commit, governance.
3. **DIVIDE** — split token-heavy/review work into bounded independent packets.
4. **PLAN** — choose the smallest reversible change and identify approval gates.
5. **IMPLEMENT** — change only the selected slice on its focused branch.
6. **TEST** — normal behavior plus relevant failure, recovery, security, isolation,
   duplication, restart, and regression cases.
7. **COMPARE** — compare independent reviewers/models and the real diff; consensus is
   not proof.
8. **VERIFY** — read back files, exact commit, tests/CI, and runtime behavior.
9. **PROMOTE** — Jon approves consequential merge/release; preserve rollback.
10. **PRESERVE** — update work order, status, registry resume point, reviews/evidence,
    global index when needed, and one next action for the selected stream.

A model saying “done” never skips verification or promotion gates.


## Drift recognition and controlled pause

Check alignment at session resumption, before significant or external actions,
and at checkpoints: (1) current owner goal and accepted scope; (2) selected
workspace/workstream, canonical repository/base/head and actual local-vs-remote
state; (3) data privacy and authority grants; (4) cost/time/tool budget; and
(5) claimed results versus exact evidence and completion criteria.

- **Correct small reversible drift in scope** using existing rules and evidence;
  do not turn minor wording or formatting differences into new workstreams.
- **STOP -> CHECKPOINT -> REPLAN_REQUIRED** for material divergence: wrong or
  ambiguous workspace, unexpected branch/base, overlapping active edits,
  sensitive/public push risk, stale or missing evidence for a consequential claim,
  changed permissions, unapproved side effects, or exceeded resource budget.
  Preserve verified state, name the mismatch and smallest safe option, and
  request owner direction only where the existing authority cannot resolve it.
- Never silently expand the task, invent successful verification, bypass a
  privacy gate, escalate models/effort, or restart a costly investigation merely
  to keep moving. Resume only within an evidenced and authorized scope.
- Standardize recurring failures by extending an **existing** HumanOS control
  document through a bounded reviewed change. Do not proliferate constitutions,
  routers, registries, or approval ceremonies. Written guidance is not an
  automatic runtime enforcement mechanism.


## Cross-chat continuation protocol

At the start of a new HumanOS-related chat/session:

1. infer/request the relevant workspace from the user's actual topic;
2. load the public registry and authorized private overlay;
3. search related workstreams;
4. classify CONTINUE / EXTEND / CREATE_SEPARATE / AMBIGUOUS;
5. report the discovered relationship;
6. read the selected branch snapshot/work order/evidence;
7. continue from the preserved resume point.

If registry metadata and branch evidence disagree, branch/commit/test evidence wins;
update the registry after reconciliation.

At the end of meaningful work:

- preserve exact tested commit/evidence;
- update the selected work order and `STATUS.md` if state changed;
- update registry status/resume point/next action if appropriate;
- update issue #67 only when the global index or session focus materially changes;
- do not append transcripts or private content to control surfaces.

## Work-order rule

Every consequential implementation/research slice uses a stable ID. Work orders
must distinguish proposal from implementation, local evidence from external claims,
current scope from deferred ideas, and approved actions from pending approvals.

## Artifact rule

Every durable artifact belongs to a registered category: governance, context/registry,
architecture, work order, implementation, test/evidence, review, release/rollback,
research, or routing/index metadata. Do not create parallel status ledgers.

## Multi-model workflow

For meaningful HumanOS work, independent models may be used for bounded coding,
architecture, challenge, security, or review packets. Requirements:

- same necessary context and acceptance criteria;
- do not expose one model's answer before another commits its independent output;
- preserve raw outputs only when formal evidence requires them;
- record provider/model/version, timestamp, task, role, latency, and usage/cost when exposed;
- outputs remain proposals until repository evidence verifies them;
- never send hosted models credentials, secrets, private Notebook paths, client/employer
  data, or unnecessary personal information.

## Evidence and promotion gates

`VERIFIED` requires the evidence named by the work order. Typical evidence includes
relevant tests, full regression CI when shared behavior can be affected, exact-commit
diff/security review, runtime readback for runtime claims, and recorded limitations.

A green CI run proves only what that CI tests.

Consequential merge, release, destructive changes, security/privacy-boundary changes,
financial/legal/public actions, and external actions require Jon's approval.

## No-loose-workflow rule

The following are not independent sources of truth:

- chat todo lists;
- model memory;
- temporary scratchpads;
- duplicated backlog documents;
- undocumented branches;
- unreferenced review files;
- private notes copied into the public repository.

Capture durable work once in the registry/work order/index with explicit state and
relationships. Existing similar work must be discovered before creating a new stream.

## Completion rule

A slice is done only when acceptance criteria are satisfied, evidence is preserved,
rollback is known, registry/status are reconciled, and the selected workstream has
an explicit next action or terminal state. `PROMOTED` additionally requires owner
approval and post-promotion verification where applicable.
