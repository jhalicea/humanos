# HumanOS Status Snapshot

Status: ACTIVE DEVELOPMENT SLICE
Date: 2026-09-17
Global routing/index control plane: GitHub issue #67
Current branch: `foundation/context-workstream-registry-v1`

This file is the commit-scoped status snapshot for this branch. HumanOS may have
multiple open workstreams; this file describes only the current branch/session.

## Selected workstream

- Work order: `HOS-CTX-001 — Development Context Registry Kernel`
- Workspace: `WS-HUMANOS`
- Branch: `foundation/context-workstream-registry-v1`
- Baseline: `foundation/workflow-continuity-v1` at
  `c5abd74572b8a4fde2b3c4fdaaf7e5035829dcb2`
- Outcome: a small but strong precursor to the future Context Layer that can route
  development work by workspace/topic, discover related workstreams, preserve
  resume state, and fail closed across workspace boundaries.

## Corrected workflow truth

- HumanOS does **not** enforce one global ACTIVE task.
- Multiple workstreams may coexist across HumanOS, personal, business, employer,
  client, experiment, and research contexts.
- The current session selects one focused execution slice at a time.
- A request is routed by `workspace -> related workstream -> CONTINUE / EXTEND /
  CREATE_SEPARATE / AMBIGUOUS` before implementation.
- Ambiguous cross-workspace requests require confirmation.
- Workspace-private data is isolated by default.
- Component conflicts on the same repository are checked before concurrent edits.

## Registry surfaces

- Public safe registry: `config/context_registry.public.json`
- Registry implementation: `context_registry.py`
- Private overlay example: `examples/context-registry.private.example.json`
- Design/operations: `docs/foundation/CONTEXT_REGISTRY.md`
- Workflow standard: `docs/foundation/WORKFLOW_STANDARD.md`
- Global router/index: GitHub issue #67

The real private overlay is never stored in Git and is selected with
`HUMANOS_CONTEXT_PRIVATE_REGISTRY`.

## Known related work

The public registry includes safe metadata for currently discoverable HumanOS
workstreams such as foundation/workflow, model loader, model router, adaptive
learning/mastery, browser tooling, Notebook capture/recall, inbox automation,
multi-model swarm, backups, and file/context intelligence. Unknown branch status
is recorded as `UNKNOWN` instead of guessed.

## Continuation behavior

In a new chat/session, Jon can simply ask for the actual work. The operating
sequence is:

1. identify the workspace/context from the request or ask if ambiguous;
2. load the registry;
3. search related workstreams;
4. report whether this looks like CONTINUE, EXTEND, CREATE_SEPARATE, or AMBIGUOUS;
5. inspect the selected branch/work order/evidence;
6. continue only after that reconciliation.

No “continue HumanOS” phrase is required.

## Next action

Verify HOS-CTX-001 with registry-specific tests plus full HumanOS CI, inspect the
final diff for privacy/authority/workflow regressions, update issue #67 as a
global router/index, and leave promotion pending for Jon.

## Privacy boundary

This file and the public registry contain project metadata only. They must never
contain real confidential client/employer identities, credentials, private local
paths, Life Notebook transcripts, proprietary data, or personal secrets.
