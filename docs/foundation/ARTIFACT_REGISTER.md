# HumanOS Artifact Register

Status: FOUNDATION CONTROL DOCUMENT
Purpose: identify durable HumanOS artifacts and prevent competing or orphaned workflows.

This register contains public/project metadata only. Life Notebook transcripts,
credentials, private paths, personal records, client/employer identities, proprietary
information, and sensitive local evidence do not belong here.

| Artifact | Location | Role / authority | Update trigger |
|---|---|---|---|
| HumanOS Constitution | `core/constitution.md` | Governing constitutional copy beneath owner authority and above subordinate decisions/standards | Constitutional change process only |
| Foundation ratification | `docs/FOUNDATION_RATIFICATION.md` | Ratified Foundation Contract v0.1 boundary | New ratification/amendment |
| Repository working agreement | `AGENTS.md` | Mandatory repository/SDLC/context-routing instructions | Workflow or safety rule change |
| Global routing/index | GitHub issue #67 | Mutable router/index for discovering workspace/workstream state and current session focus; pointer only | Registry/workstream focus materially changes |
| Public context registry | `config/context_registry.public.json` | Safe workspace/workstream metadata used for topic-aware development routing | Workstream created, renamed, related, status/resume point changes |
| Registry implementation | `context_registry.py` | Deterministic schema validation, routing, boundary checks, conflict checks | Context-registry behavior changes |
| Private context overlay | external/local path via `HUMANOS_CONTEXT_PRIVATE_REGISTRY` | Sensitive workspace identities/local roots/private-only streams; never committed | Private workspace metadata changes |
| Context registry design | `docs/foundation/CONTEXT_REGISTRY.md` | Architecture/security/operations contract for the development Context Layer kernel | Context design evolves |
| Branch status snapshot | `STATUS.md` | Commit-scoped state for the selected branch/session | Branch state/evidence/next-action change |
| Lean Agile + SDLC standard | `docs/foundation/WORKFLOW_STANDARD.md` | Unified topic-aware routing, WIP, SDLC, continuation, isolation standard | Approved workflow evolution |
| Artifact register | `docs/foundation/ARTIFACT_REGISTER.md` | Map of durable project artifacts and roles | Durable artifact category/path changes |
| Work orders | `docs/work-orders/HOS-*.md` | Acceptance contract for bounded slices | Scope/progress/verification changes |
| Reviews | `docs/reviews/*.md` and milestone review files | Security/architecture/diff/independent findings | Formal review performed/updated |
| Tests | `tests/` | Executable evidence under covered conditions | Behavior/acceptance criteria change |
| CI workflows | `.github/workflows/` | Automated commit-specific checks | CI policy/test matrix change |
| Architecture docs | `docs/architecture.md`, `docs/mirror-runtime.md`, related docs | Public architecture description; not implementation proof | Architecture description changes |
| Model governance | `docs/model-governance.md` | Model authority/proposal/evidence boundary | Model governance change |
| Security/privacy docs | `docs/security-and-privacy.md` | Public security/privacy boundary | Security/privacy design change |
| Testing/evidence docs | `docs/testing-and-evidence.md` | Evidence interpretation/testing guidance | Evidence policy change |
| Roadmap | `docs/roadmap.md` | Planned direction, not routing truth | Roadmap change |
| README/docs index | `README.md`, `docs/index.md` | Entry points/public status | User-facing docs change |
| Release/rollback evidence | tags, releases, commit history, work orders | Promotion and rollback truth | Merge/release/promotion |

## Promoted foundation/context baseline

`HOS-FND-001 — Foundation Workflow & Cross-Chat Continuity` and
`HOS-CTX-001 — Development Context Registry Kernel` are promoted into
`runtime-0.1` by PR #68 at merge commit
`edb46410d8b36de54413aa75db10efa64d213241`.

HOS-CTX-001 supersedes HOS-FND-001's original global WIP=1 assumption. HumanOS
may preserve multiple open workstreams; the current session selects one focused
execution slice and must reconcile component conflicts before concurrent edits.

Other HumanOS workstreams remain independently preserved in the context registry.
Their state is not changed merely because the foundation/context kernel is promoted.

## Placement rules

- Governance/foundation standards: `core/` or `docs/foundation/`.
- Public safe routing metadata: `config/context_registry.public.json`.
- Sensitive workspace mapping: private overlay outside Git only.
- Bounded implementation contracts: `docs/work-orders/`.
- Formal findings: `docs/reviews/`.
- Executable behavior checks: `tests/`.
- Research not adopted: research index/location with explicit proposal status.
- Global routing/index: issue #67; do not create another global status ledger.
- Branch/session state: root `STATUS.md` on that branch.

## Lifecycle

A durable artifact may be `DRAFT`, `CANDIDATE`, `RATIFIED/APPROVED`,
`IMPLEMENTED`, `VERIFIED`, `SUPERSEDED`, or `ARCHIVED` as appropriate.
Workstreams use the states defined in `WORKFLOW_STANDARD.md`.

Document status does not imply runtime implementation. Runtime claims require
executable/readback evidence. When superseded, preserve provenance and point to
the replacement rather than silently deleting history.
