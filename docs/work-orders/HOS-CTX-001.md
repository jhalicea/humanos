# HOS-CTX-001 — Development Context Registry Kernel

Status: VERIFIED IMPLEMENTATION / PROMOTION PENDING
Branch: `foundation/context-workstream-registry-v1`
Workspace: `WS-HUMANOS`
Parent/related: extends `HOS-FND-001`
Verified implementation commit: `b58a4f3c5e0c984dfd5d67b43e49407f7ad605b8`

## Outcome

Build a small but strong operational precursor to the future HumanOS Context Layer so development requests can be routed by workspace and topic, related unfinished work can be discovered before creating duplicates, private work contexts remain isolated, and resume state is durable across chats.

## Baseline

- Parent candidate: `foundation/workflow-continuity-v1`
- Baseline commit: `c5abd74572b8a4fde2b3c4fdaaf7e5035829dcb2`
- HOS-FND-001 is verified/promotion-pending but contained one incorrect assumption: a global WIP limit of one ACTIVE HumanOS slice.
- HumanOS already has many feature/experiment branches that can legitimately coexist.

## Scope delivered

- public workspace/workstream registry;
- private overlay mechanism outside Git;
- deterministic schema validation and topic-aware routing;
- CONTINUE / EXTEND / CREATE_SEPARATE / AMBIGUOUS classification;
- workspace confidentiality and fail-closed cross-workspace access check;
- typed workstream relationships;
- component conflict detection for concurrent repository work;
- initial safe registry of known HumanOS workstreams;
- topic-driven cross-chat procedure that requires no magic phrase;
- updated foundation workflow/agent/status/index documentation.

Still excluded:

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

## Acceptance criteria — verification result

1. `context_registry.py` strictly validates the public registry — PASSED.
2. Public registry contains a safe HumanOS workspace and useful known workstreams — PASSED.
3. Private overlay can add a client/employer workspace without leaking it through `public_snapshot()` — PASSED.
4. Private overlay cannot redefine a public workspace/workstream — PASSED.
5. Cross-workspace access fails without explicit authorization — PASSED.
6. Routing a model-loader continuation selects HOS-MAL-001 — PASSED.
7. Routing an inbox improvement recognizes the existing inbox stream — PASSED.
8. Explicit separate/new wording preserves the related candidate while returning CREATE_SEPARATE — PASSED.
9. Equal workspace/workstream matches return AMBIGUOUS — PASSED.
10. Unknown relation targets fail validation — PASSED.
11. Overlapping concurrent component scopes are detectable — PASSED.
12. Workflow/AGENTS docs no longer require one global ACTIVE HumanOS slice — PASSED.
13. Full HumanOS regression CI remains green on the exact implementation commit — PASSED.
14. Final implementation diff contains no confidential/private workspace data — PASSED by diff/repository review; example values are fictional placeholders only.
15. Issue #67 is converted from a single-task cursor to a global routing/index surface — PASSED.

## Verification evidence

- HumanOS regression workflow passed on Ubuntu 24.04 and macOS 15 with Python 3.11 and 3.13.
- Encrypted-backup/full-suite workflow passed on Ubuntu 24.04 and macOS 15 with Python 3.11 and 3.13.
- Exact implementation diff from baseline reviewed.
- Dedicated `tests/test_context_registry.py` covers routing, ambiguity, isolation, private overlays, relation validation, and conflict behavior.
- Issue #67 now records the global workspace/workstream routing protocol instead of a global single-task cursor.

## Rollback

Before promotion, delete the branch or reset it to the baseline commit. The current HumanOS runtime is not wired to the registry, so rollback does not mutate Notebook data or production runtime state.

## Known gaps

- deterministic token routing is intentionally simpler than future semantic context;
- registry updates are manual in this slice;
- private overlay storage/encryption policy is not implemented here;
- component conflict detection is advisory and path-scope based;
- runtime capabilities do not yet enforce workspace labels end-to-end;
- automatic repository/workstream discovery is future work and must not be claimed yet.

## Next action

Jon decides whether to promote/merge this verified foundation candidate. Do not merge automatically. If promoted, the next Context Layer increment should be selected by actual development need rather than expanding the layer speculatively.
