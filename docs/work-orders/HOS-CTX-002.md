# HOS-CTX-002 — Runtime Context Routing Bridge

Status: PROMOTED
Branch: `feature/context-runtime-routing-v1`
Workspace: `WS-HUMANOS`
Parent: extends promoted `HOS-CTX-001`
Baseline: `runtime-0.1` at `aa7a81f00ab21cb6c582391d41603b84b70c5f7f`
Verified implementation commit: `ae8edd93c20e6bc98ad3ab32ea500575fc220b6d`
Promotion PR: #69
Promotion merge commit: `cd1075fdf0407588b6808bcc50b08325f8b4130a`

## Outcome

Make the promoted development Context Registry operational inside the HumanOS runtime without turning it into a broad speculative Context Layer. A normal HumanOS request can be inspected before model/tool execution, related work can be surfaced, ambiguous workspace/workstream matches fail closed, and deterministic routing context can be supplied to Mirror without altering the exact human transcript.

## Scope delivered

- `context_runtime.py` provides one deterministic runtime-facing bridge over the promoted `context_registry.py` authority;
- normal Mirror turns are routed before model/tool execution;
- ordinary conversation with no registry relevance proceeds normally;
- related HumanOS development work is surfaced as `CONTINUE`, `EXTEND`, `CREATE_SEPARATE`, or `AMBIGUOUS`;
- ambiguity produces a deterministic host response and zero model/tool execution;
- public HumanOS routing metadata can be injected into the model context without rewriting the exact human input;
- private-overlay workstream details are redacted from model routing packets by default;
- requests matching both public and private workspace workstreams require explicit context confirmation even when scores differ;
- the original runtime implementation is preserved in `server_core.py`; `server.py` is the context-aware composition/entrypoint and re-exports the original public API;
- HOS-CTX-002 is registered as a bounded child of promoted HOS-CTX-001;
- focused tests plus both repository CI matrices verify the implementation.

## Security invariants

1. Exact human input remains the Notebook transaction input; routing metadata is separate host context.
2. Ambiguous context-managed requests do not reach the model or tools.
3. No cross-workspace private data is copied into another workspace implicitly.
4. Private overlay display names, local roots, notes, private titles/projects/branches/work orders/resume text/next actions are not emitted in model routing packets.
5. Routing cannot merge, switch branches, write files, or authorize tools.
6. Ordinary conversation that does not match the development registry is not falsely blocked.
7. Existing `context_registry.py` remains the single registry/routing authority for schema-v1.
8. A private workspace plus any other positively matched workspace fails closed without an explicit workspace hint.
9. Resumed transactions preserve their already-durable execution context instead of being rerouted under changed registry metadata.

## Acceptance criteria — verification result

1. Model-loader continuation returns `CONTINUE` / `HOS-MAL-001` with resume metadata — PASSED.
2. This runtime integration is a bounded child of promoted HOS-CTX-001 — PASSED.
3. Equal client/employer/private workspace matches require confirmation and no Agent invocation occurs — PASSED.
4. Public + private related work requires confirmation even when scores differ — PASSED.
5. A request with no registry relevance is not context-managed and proceeds normally — PASSED.
6. Route metadata reaches the model while the Notebook retains exact original human input — PASSED.
7. Private overlay/workstream details are absent from model routing packets — PASSED.
8. `CONTEXT_ROUTE` evidence is written to the Notebook event ledger for routed normal Mirror turns — PASSED.
9. Full HumanOS regression matrix passed on Ubuntu 24.04 and macOS 15 with Python 3.11 and 3.13 on the exact implementation commit — PASSED.
10. Encrypted-backup/full-suite matrix passed on the same four OS/Python combinations on the exact implementation commit — PASSED.

## Verification evidence

- Exact implementation commit: `ae8edd93c20e6bc98ad3ab32ea500575fc220b6d`.
- Regression workflow run: `35268955403` — all four OS/Python jobs passed.
- Encrypted-backup/full-suite workflow run: `35268955541` — all four OS/Python jobs passed.
- Dedicated tests: `tests/test_context_runtime_bridge.py`.
- Diff review from baseline shows only the bounded context runtime bridge, registry/work order, runtime composition layer, preserved runtime core, and tests.
- PR #69 merged the verified candidate into `runtime-0.1` at `cd1075fdf0407588b6808bcc50b08325f8b4130a` after explicit owner approval.

## Known gaps / deliberate boundaries

- Deterministic token/topic routing is intentionally simpler than the future semantic Context Layer.
- Delegated `WorkBoard` agents created by the existing work-mode path are not yet context-gated by this bridge; this slice covers normal Mirror turns only.
- An already-started/resumed transaction is not rerouted. This prevents registry drift from changing an existing durable execution context, but route context is not re-injected on resume.
- Automatic GitHub branch/work-order discovery is still outside the runtime; the registry remains the durable routing index.
- No automatic branch checkout, merge, or work execution is granted by routing.
- Full identity, temporal context, rich permission graph, and cross-workspace transfer authorization UI remain future Context Layer work.
- `server.py` composes the context gate over the preserved runtime implementation in `server_core.py`; future runtime changes must preserve this layering or deliberately consolidate it in a reviewed slice.

## Rollback

Revert PR #69 / merge commit `cd1075fdf0407588b6808bcc50b08325f8b4130a`. HOS-CTX-001 remains promoted on `runtime-0.1`; no Notebook migration is required. The routing bridge adds no schema migration and does not mutate existing Notebook content during installation.

## Next action

No direct continuation is required. Route future requests through the promoted bridge. Create a new bounded Context Layer workstream only when a concrete runtime need exposes a gap; do not reopen this work order as an unlimited feature stream.
