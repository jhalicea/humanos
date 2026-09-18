# HOS-CTX-010 — Verified Registry → Context Graph Bridge

Status: REVIEW  
Branch: `feature/context-registry-graph-bridge-v1`  
Workspace: `WS-HUMANOS`  
Parent: extends promoted `HOS-CTX-009`  
Baseline: `runtime-0.1` at `0a2619ea637c8d836e98c5f12d2bfb98df53f741`

## Relationship classification

**EXTEND as a new bounded Context Engine workstream.**

CTX-009 established the local deterministic entity/relationship graph substrate. CTX-010
adds the first trusted projection bridge from an existing canonical HumanOS source:
the validated public Context Registry.

## Outcome

Project verified **public registry structure** into a caller-supplied local Context Graph
without model inference or private-overlay leakage.

Schema v1 projects:

- each public workspace as a `WORKSPACE` entity;
- each public workstream as a `WORKSTREAM` entity;
- each public workstream → workspace membership as a `BELONGS_TO` edge;
- registry relations already supported by the graph: `EXTENDS`, `RELATED_TO`,
  and `DEPENDS_ON`.

Every projected assertion carries `REGISTRY_EVIDENCE` provenance bound to a
SHA-256 digest of the exact public registry snapshot used for the projection.

## Stable identity rule

Registry IDs, not mutable display names/titles, are the graph stable keys and labels in
this slice. A future metadata/property layer may represent mutable titles, aliases,
status, and descriptions without mutating canonical identity rows.

## Public/private boundary

The bridge consumes only `public_workspace_ids` and `public_workstream_ids`.

- Private-overlay-only entities are never projected.
- A public relation targeting a non-public workstream is skipped and reported.
- Cross-workspace supported relations fail closed.
- Workspace/workstream confidentiality mismatch fails closed before graph mutation.
- Unsupported registry relation types are skipped and explicitly reported; they are
  never silently coerced into another graph relation.

## Authority boundary

The registry remains the source for these projected facts. The graph is a derived
structured view. Projection does not grant execution authority, does not modify the
registry, and does not make graph rows stronger than repository/Notebook/owner evidence.

No model output, embeddings, semantic entity merging, Notebook import, Mirror integration,
or private graph population is introduced.

## Crash/replay boundary

The bridge preflights security/boundary conditions before mutation. Graph inserts remain
append-only and idempotent. A process crash may leave a partial derived projection; rerun
is safe and completes the same deterministic assertions. No runtime consumer may treat
projection completeness as established merely because some graph rows exist; a later
runtime-integration slice must add an explicit completed-projection/readiness contract.

## Scope

Implementation:

- `context_graph_bridge.py`
- `tests/test_context_graph_bridge.py`
- `docs/work-orders/HOS-CTX-010.md`
- `config/context_registry.public.json`

## Acceptance

1. Public workspace/workstream entities project deterministically.
2. Workstream → workspace `BELONGS_TO` edges project deterministically.
3. Supported public registry relations project with the same direction/type.
4. Every projected entity/edge has `REGISTRY_EVIDENCE` bound to the public snapshot digest.
5. Re-running the same projection is idempotent.
6. Private-overlay-only entities are not projected.
7. Public relations to non-public targets are skipped and reported.
8. Unsupported relation types are skipped and reported rather than coerced.
9. Cross-workspace supported relations and confidentiality mismatches fail closed before mutation.
10. Existing HumanOS tests remain compatible.
11. Full regression and encrypted-backup matrices pass.
12. Promotion remains owner-gated.

## Explicit exclusions

This slice does **not**:

- seed project/person/goal entities;
- project mutable status/title/topic/component metadata;
- auto-run during Mirror startup;
- choose a live graph database path;
- authorize sensitive graph data;
- import Notebook evidence;
- resolve aliases or merge identities;
- produce model context packages.

## Rollback

Before promotion, switch back to `runtime-0.1` or delete this branch. CTX-010 does
not mutate canonical Notebook data or an existing production graph automatically.
