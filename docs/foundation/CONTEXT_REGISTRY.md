# HumanOS Development Context Registry

Status: CONTEXT LAYER PRECURSOR / FOUNDATION CANDIDATE
Work order: `HOS-CTX-001`
Implementation: `context_registry.py`
Public data: `config/context_registry.public.json`

## Purpose

This is the smallest operational precursor to the future HumanOS Context Layer. It exists now so HumanOS development can safely answer:

- Which workspace/owner context does this request belong to?
- What related project/workstream already exists?
- Should we CONTINUE, EXTEND, CREATE_SEPARATE, or ask because it is AMBIGUOUS?
- Which branch/work order/resume point should be inspected?
- Is private data allowed to cross into another workspace?
- Would the proposed edit overlap another concurrent workstream?

It is stronger than a flat branch list, but it is not yet the full HumanOS Context Layer.

## Hierarchy

`OWNER -> WORKSPACE -> PROJECT -> WORKSTREAM -> WORK ORDER -> BRANCH -> SLICE -> EVIDENCE`

A workspace is both an organizational boundary and a security boundary.

Supported workspace types in schema v1:

- `HUMANOS_INTERNAL`
- `PERSONAL`
- `BUSINESS`
- `EMPLOYER`
- `CLIENT`
- `EXPERIMENT`
- `RESEARCH`

## Public/private split

The public registry contains safe aliases and non-sensitive project metadata only. Real confidential client/employer identities, private local filesystem roots, and private-only workstreams belong in an external overlay selected with:

`HUMANOS_CONTEXT_PRIVATE_REGISTRY=/path/outside/repo/private.json`

The private overlay may add private-only workspaces/workstreams and attach `display_name`, `local_roots`, and private notes. It may not redefine a public workspace/workstream or weaken the schema-v1 cross-workspace policy.

`ContextRegistry.public_snapshot()` emits public-registry entries only and excludes private-overlay metadata and private-only workspaces/workstreams.

## Isolation model

Every workspace has a confidentiality class and `cross_workspace_policy: DENY`.

Same-workspace access is allowed by this registry layer. Cross-workspace access raises `ContextBoundaryError` unless explicit owner authorization is supplied.

General public techniques can be reused across workspaces. Workspace-specific content cannot be reused implicitly.

## Workstream records

Each workstream records stable ID, workspace ID, title/project, repository and branch, work-order path when present, state, confidentiality, routing topics, component scope, typed relations, last verified commit when known, exact resume point, and one next action.

Unknown historical branch state is explicitly `UNKNOWN`; existence of a branch is not evidence that it is active, finished, safe, or merged.

## Relationships

Schema v1 supports `CONTINUES`, `EXTENDS`, `DEPENDS_ON`, `RELATED_TO`, `SUPERSEDES`, `EXPERIMENT_FOR`, `BLOCKED_BY`, and `INTEGRATES_WITH`.

Relation targets must exist and self-relations are rejected.

## Routing

`route_request()` uses deterministic token matching, not opaque semantic inference. Routing occurs in two stages: resolve a workspace, then score related workstreams inside that workspace.

The result is `CONTINUE`, `EXTEND`, `CREATE_SEPARATE`, or `AMBIGUOUS`.

A routing result is a development recommendation, not authority to edit or merge. The assistant should report the discovered relationship and inspect repository evidence before implementation. Equal workspace/workstream matches fail closed to `AMBIGUOUS`.

## Conflict detection

`find_component_conflicts()` compares proposed component scopes against other workstreams in the same repository that are `ACTIVE`, `REVIEW`, or `PROMOTION_PENDING`. Equal or nested paths are treated as overlapping. This is deliberately conservative and does not replace Git conflict detection.

## Command-line use

Validate:

```bash
python3 context_registry.py validate
```

Route a request:

```bash
python3 context_registry.py route "continue the sharded model loader manifest work"
```

Constrain to a known workspace:

```bash
python3 context_registry.py route "improve the email classifier" --workspace WS-HUMANOS
```

Use a private overlay:

```bash
HUMANOS_CONTEXT_PRIVATE_REGISTRY=/secure/path/context.private.json \
  python3 context_registry.py route "continue the client email classifier"
```

The CLI prints IDs/aliases and routing evidence; it does not print private display names or local roots.

## Security properties in this slice

- strict schema/unknown-field rejection;
- stable ID validation;
- typed workspace/workstream states;
- typed relation validation and unknown-target rejection;
- public/private overlay separation;
- private overlay cannot redefine public entries;
- schema-v1 cross-workspace policy cannot be weakened from `DENY`;
- explicit authorization required for cross-workspace access;
- private metadata excluded from public snapshot;
- ambiguous routing fails closed;
- concurrent component overlap can be detected before edits.

## Known gaps

This is not yet a full semantic Context Layer, Mirror-integrated context loader, complete information-flow monitor, automatic GitHub discovery service, signed registry, graph database, automatic conflict lock, temporal context engine, or identity/role credential system.

Those capabilities should be added incrementally when the development kernel proves the need.

## Future Context Layer direction

The schema is designed to grow toward richer context:

`identity + workspace + relationships + permissions + temporal context + retrieval + provenance`

The development registry should remain one data source inside that larger layer, not become the entire Context Layer.
