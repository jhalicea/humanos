# HOS-CTX-009 — Entity & Relationship Context Graph Foundation

Status: REVIEW  
Branch: `feature/context-entity-relationship-graph-v1`  
Workspace: `WS-HUMANOS`  
Parent: extends promoted `HOS-CTX-008`  
Baseline: `runtime-0.1` at `76da5347c62be237a371dd6ede8948100ca1091a`

## Relationship classification

**EXTEND as a new bounded Context Engine workstream.**

CTX-001 through CTX-008 established workspace routing, session/historical continuation,
temporal relevance, local-time interpretation, and temporal hardening. CTX-009 adds
the first structured entity/relationship substrate in the same Context Engine lineage.

## Outcome

Create a deterministic local graph primitive that can represent typed entities and
directional relationships without turning model inference into authority.

The graph stores:

- workspace-scoped stable entity IDs;
- typed entity classes;
- typed directional relationships;
- explicit provenance for entity and relationship assertions;
- workspace and confidentiality ownership;
- deterministic SQLite persistence at a caller-selected local path;
- an explicit schema-version marker and append-only graph/provenance rows in schema v1.

## Authority and evidence model

Life Notebook remains chronological evidence and provenance authority. The graph is
derived structured interpretation. A graph row never overrides Notebook evidence,
repository evidence, permissions, or owner authority.

Schema v1 accepts only explicit provenance kinds:

- `OWNER_ASSERTION`
- `NOTEBOOK_EVIDENCE`
- `REPOSITORY_EVIDENCE`
- `REGISTRY_EVIDENCE`
- `TOOL_EVIDENCE`

`MODEL_OUTPUT` is deliberately not an accepted canonical provenance kind. Models may
later propose graph assertions, but another trusted process/owner action must validate
and source them before insertion.

## Security / isolation boundary

- Entity IDs are derived from workspace + type + stable key, preventing implicit
  cross-workspace identity collapse.
- Reads require the expected workspace.
- Cross-workspace relationships fail closed.
- Relationships across different confidentiality classes fail closed in schema v1.
- Provenance references are bounded content-light identifiers, not transcript payloads.
- No graph data is committed to Git; only the implementation and tests are public.
- No IP/geolocation inference, embeddings, semantic matching, hidden memory, or model
  auto-write path is introduced.
- No branch/tool/merge/release authority is added.

## Data-handling boundary

The schema primitive is not itself cryptographic evidence and is not yet wired to a
protected HumanOS vault location. CTX-009 therefore does not authorize storing real
personal, client, employer, credential, or other sensitive graph content in a live
runtime. Before Mirror or agents consume sensitive graph state, a later bounded slice
must define protected storage placement, integrity/rebuild semantics, backup/export,
privacy deletion behavior, and the provenance re-verification policy.

A compromised or manually edited graph database must never outrank the Life Notebook,
repository evidence, permissions, or owner-confirmed state.

## Scope

Implementation:

- `context_graph.py`
- `tests/test_context_graph.py`
- `docs/work-orders/HOS-CTX-009.md`
- `config/context_registry.public.json`

## Explicit exclusions

This slice does **not**:

- integrate the graph into Mirror/model context;
- auto-import Life Notebook content;
- auto-seed the graph from the Context Registry;
- perform entity resolution or alias merging;
- use embeddings/vector search;
- infer relationships from model prose;
- implement cross-workspace authorization bridges;
- compose model context packages;
- replace the Life Notebook or Context Registry.

Those belong to later bounded Context Engine slices.

## Acceptance

1. Entity IDs are deterministic and workspace-scoped.
2. Entities are typed, persistent, idempotent, and can accumulate trusted provenance.
3. Relationships are typed, directional, persistent, idempotent, and provenance-bearing.
4. `MODEL_OUTPUT` provenance is rejected.
5. Wrong-workspace reads and cross-workspace relationships fail closed.
6. Mixed-confidentiality relationships fail closed in schema v1.
7. Reopening the local SQLite graph preserves verified rows.
8. Existing HumanOS tests remain compatible.
9. Full regression and encrypted-backup matrices pass.
10. Promotion remains owner-gated.

## Rollback

Before promotion, rollback is branch deletion or switching back to `runtime-0.1`.
No canonical Notebook evidence, user data, or existing runtime database is modified
by this isolated graph substrate.
