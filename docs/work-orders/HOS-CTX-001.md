# HOS-CTX-001 — Development Context Registry Kernel

Status: ACTIVE / NOT PROMOTED
Branch: `foundation/context-workstream-registry-v1`
Workspace: `WS-HUMANOS`
Parent/related: extends `HOS-FND-001`

## Outcome

Build a small but strong operational precursor to the future HumanOS Context Layer so development requests can be routed by workspace and topic, related unfinished work can be discovered before creating duplicates, private work contexts remain isolated, and resume state is durable across chats.

## Baseline

- Parent candidate: `foundation/workflow-continuity-v1`
- Baseline commit: `c5abd74572b8a4fde2b3c4fdaaf7e5035829dcb2`
- HOS-FND-001 is verified/promotion-pending but contains one incorrect assumption: a global WIP limit of one ACTIVE HumanOS slice.
- HumanOS already has many feature/experiment branches that can legitimately coexist.

## Scope

Included:

- public workspace/workstream registry;
- private overlay mechanism outside Git;
- deterministic schema validation and topic-aware routing;
- CONTINUE / EXTEND / CREATE_SEPARATE / AMBIGUOUS classification;
- workspace confidentiality and fail-closed cross-workspace access check;
- typed workstream relationships;
- component conflict detection for concurrent repository work;
- initial safe registry of known HumanOS workstreams;
- topic-driven cross-chat procedure that requires no magic phrase;
- update foundation workflow/agent/status/index documentation.

Excluded:

- full Mirror/runtime integration;
- automatic GitHub API discovery inside HumanOS runtime;
- semantic embedding/vector routing;
- client/employer identities in the public repository;
- automatic cross-workspace data transfer;
- automatic merge/promotion;
- full future Context Layer identity/temporal/permission graph.

## Security invariants

1. Workspace is a security/ownership boundary.
2. Schema-v1 cross-workspace policy is `DENY`.
3. Cross-workspace access requires explicit owner authorization.
4. Private overlay cannot redefine public workspaces/workstreams.
5. Private metadata/private-only streams are excluded from public snapshots.
6. Ambiguous routing fails closed.
7. Unknown branch/workstream state is `UNKNOWN`, never guessed.
8. Existing related work is reported before new parallel work is created.
9. Public Git contains no real confidential client/employer names, local roots, credentials, Notebook transcripts, or proprietary data.

## Acceptance criteria

1. `context_registry.py` loads and strictly validates the public registry.
2. Public registry contains a safe HumanOS workspace and useful known workstreams.
3. Private overlay can add a client/employer workspace without leaking it through `public_snapshot()`.
4. Private overlay cannot redefine a public workspace/workstream.
5. Cross-workspace access fails without explicit authorization.
6. Routing a model-loader continuation selects HOS-MAL-001.
7. Routing an inbox improvement recognizes the existing inbox stream.
8. Explicit separate/new wording preserves the related candidate while returning CREATE_SEPARATE.
9. Equal workspace/workstream matches return AMBIGUOUS.
10. Unknown relation targets fail validation.
11. Overlapping concurrent component scopes are detectable.
12. Workflow/AGENTS docs no longer require one global ACTIVE HumanOS slice.
13. Full HumanOS regression CI remains green on the exact final commit.
14. Final diff contains no confidential/private workspace data.
15. Issue #67 is converted from a single-task cursor to a global routing/index surface.

## Test plan

- dedicated `tests/test_context_registry.py`;
- full `python3 -m unittest discover -s tests -v` through existing CI;
- inspect diff against `c5abd74572b8a4fde2b3c4fdaaf7e5035829dcb2`;
- inspect public registry for sensitive identifiers/paths;
- verify CLI validation/routing behavior from tests or runtime readback.

## Rollback

Before promotion, delete the branch or reset it to the baseline commit. The current HumanOS runtime is not wired to the registry, so rollback does not mutate Notebook data or production runtime state.

## Known gaps

- deterministic token routing is intentionally simpler than future semantic context;
- registry updates are manual in this slice;
- private overlay storage/encryption policy is not implemented here;
- component conflict detection is advisory and path-scope based;
- runtime capabilities do not yet enforce workspace labels end-to-end.

## Next action

Run dedicated tests and full CI on the implementation commit, review the exact diff and privacy boundaries, update issue #67 as a routing/index control plane, then leave promotion pending for Jon.
