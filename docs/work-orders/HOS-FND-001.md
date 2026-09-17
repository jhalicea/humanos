# HOS-FND-001 — Foundation Workflow & Cross-Chat Continuity

Status: PROMOTED / AMENDED BY HOS-CTX-001
Original branch: `foundation/workflow-continuity-v1`
Canonical promoted branch: `runtime-0.1`
Live operational index: GitHub issue #67
Verified candidate commit: `c5abd74572b8a4fde2b3c4fdaaf7e5035829dcb2`
Promotion PR: #68
Promotion merge commit: `edb46410d8b36de54413aa75db10efa64d213241`

> Amendment, 2026-09-17: HOS-CTX-001 supersedes the original global WIP=1 and
> single-active-slice continuation rule. The durable parts of this work order
> remain valid: repository-driven continuity, SDLC evidence, work orders, status
> snapshots, artifact governance, and owner promotion gates. Current routing is
> workspace/topic aware and permits multiple preserved/open workstreams.

## Outcome

Create a minimal control plane that lets a new HumanOS chat/session recover implementation state from repository evidence instead of conversational memory.

## Baseline

- Base branch: `runtime-0.1`
- Baseline commit: `9ddc6477bba70dd4c86104a0565da848d7cbacff`
- Foundation Contract v0.1 is ratified but incrementally implemented.
- `AGENTS.md` already defined repository preservation and core SDLC rules.
- Work orders, reviews, CI, and documentation existed before this slice.

## Preserved results

HOS-FND-001 established:

- GitHub issue #67 as a durable cross-chat control surface;
- root `STATUS.md` branch snapshots;
- a unified Lean Agile + HumanOS SDLC standard;
- explicit lifecycle states and Definition of Ready/Done;
- an artifact register and placement rules;
- start/end-of-session evidence preservation;
- updates to `AGENTS.md`;
- CI-backed verification on the exact candidate commit.

## Superseded assumptions

The following original assumptions are superseded by HOS-CTX-001:

- one global ACTIVE implementation slice for all HumanOS work;
- one global NEXT ACTION for all HumanOS work;
- requiring a new chat to begin from the globally ACTIVE branch;
- treating issue #67 primarily as a single-task cursor.

Current behavior is defined in `docs/foundation/WORKFLOW_STANDARD.md` and `docs/foundation/CONTEXT_REGISTRY.md`.

## Security/preservation rules that remain in force

- repository evidence outranks conversational memory;
- private Life Notebook/client/employer content stays out of the public repository;
- meaningful changes use focused branches and bounded acceptance criteria;
- tests, diff review, exact commits, and runtime readback establish implementation truth;
- consequential merge/release requires Jon's approval;
- paused/unknown work is preserved with explicit resume state rather than forgotten.

## Promotion evidence

- Owner approved promotion on 2026-09-17.
- HOS-FND-001 and HOS-CTX-001 were promoted together by PR #68 into `runtime-0.1`.
- Promotion merge commit: `edb46410d8b36de54413aa75db10efa64d213241`.
- Post-merge HumanOS regression CI passed on Ubuntu 24.04 and macOS 15 with Python 3.11 and 3.13.
- Post-merge encrypted-backup/full-suite CI passed on the same four OS/Python combinations.

## Rollback

The pre-promotion runtime baseline is `9ddc6477bba70dd4c86104a0565da848d7cbacff`. PR #68 and merge commit `edb46410d8b36de54413aa75db10efa64d213241` preserve the promotion boundary. No Notebook data migration was performed.

## Completion

This work order is complete and promoted. Its corrected continuation/workstream behavior is carried forward by HOS-CTX-001 and the current foundation standards.
