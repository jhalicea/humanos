# HumanOS Artifact Register

Status: FOUNDATION CONTROL DOCUMENT
Purpose: identify durable HumanOS artifacts and prevent competing or orphaned documentation workflows.

This register contains public/project metadata only. Life Notebook transcripts, credentials, private paths, personal records, client information, and sensitive local evidence do not belong here.

| Artifact | Location | Role / authority | Update trigger |
|---|---|---|---|
| HumanOS Constitution | `core/constitution.md` | Governing constitutional copy beneath owner authority and above subordinate canonical decisions/standards | Constitutional change process only |
| Foundation ratification | `docs/FOUNDATION_RATIFICATION.md` | Records ratified Foundation Contract v0.1 and implementation boundary; subordinate to the Constitution | New ratification/amendment |
| Repository working agreement | `AGENTS.md` | Mandatory repository/SDLC instructions for agents and contributors | Workflow or safety rule change |
| Live Control Room | GitHub issue #67 | Mutable live cross-chat operational cursor: active slice, branch, state, next action, paused/deferred work; pointer only, not historical proof | Start/end of meaningful HumanOS work or priority change |
| Branch status snapshot | `STATUS.md` | Commit-scoped state snapshot and fallback continuation cursor | Active branch/state/evidence/next-action change |
| Lean Agile + SDLC standard | `docs/foundation/WORKFLOW_STANDARD.md` | Unified flow/WIP/state/SDLC/continuation standard | Approved workflow evolution |
| Artifact register | `docs/foundation/ARTIFACT_REGISTER.md` | Map of durable project artifacts and their roles | Durable artifact category/path added or retired |
| Work orders | `docs/work-orders/HOS-*.md` | Acceptance contract for a bounded slice | Slice definition/progress/gaps/verification changes |
| Reviews | `docs/reviews/*.md` and milestone review files | Security, architecture, diff, or independent findings and dispositions | Formal review performed/updated |
| Tests | `tests/` | Executable evidence for behavior under covered conditions | Behavior or acceptance criteria change |
| CI workflows | `.github/workflows/` | Automated repository checks; evidence is commit-specific | CI policy/test matrix change |
| Architecture docs | `docs/architecture.md`, `docs/mirror-runtime.md`, related docs | Public architecture description; not proof of implementation | Architecture description changes |
| Model governance | `docs/model-governance.md` | Model authority/proposal/evidence boundary | Model governance change |
| Security/privacy docs | `docs/security-and-privacy.md` | Public security/privacy boundary | Security/privacy design change |
| Testing/evidence docs | `docs/testing-and-evidence.md` | Evidence interpretation and testing guidance | Evidence policy change |
| Roadmap | `docs/roadmap.md` | Planned direction; not current operational cursor | Roadmap change |
| README/docs index | `README.md`, `docs/index.md` | Entry points and verified public status | User-facing documentation change |
| Release/rollback evidence | tags, release notes, commit history, relevant work orders | Promotion and rollback truth | Merge/release/promotion |

## Current bounded work

### ACTIVE

- `HOS-FND-001 — Foundation Workflow & Cross-Chat Continuity`
- Branch: `foundation/workflow-continuity-v1`
- Live cursor: issue #67

### PAUSED / PRESERVED

- `HOS-MAL-001 — Verified Sharded Model Artifact Loader`
- Branch: `experiment/webllm-inspired-model-loader`
- Preserved reviewed commit: `018c9c57e40e91395defe6222f38bd2b99c83905`
- Its work order/review artifacts remain on that branch until separately promoted.

## Placement rules

- Governance/foundation standards: `core/` or `docs/foundation/` depending on authority.
- Bounded implementation contracts: `docs/work-orders/`.
- Formal findings: `docs/reviews/`.
- Executable behavior checks: `tests/`.
- Research that is not an adopted decision: research index/location with explicit proposal status.
- Current operational state: issue #67 plus branch `STATUS.md`; do not create a second status ledger.

## Lifecycle

A durable artifact is `DRAFT`, `CANDIDATE`, `RATIFIED/APPROVED`, `IMPLEMENTED`, `VERIFIED`, `SUPERSEDED`, or `ARCHIVED` as appropriate. Document status does not imply runtime implementation. Runtime claims require executable/readback evidence.

When an artifact is superseded, preserve provenance and point to the replacement rather than silently deleting history.
