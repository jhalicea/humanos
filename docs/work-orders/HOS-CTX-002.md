# HOS-CTX-002 — Runtime Context Routing Bridge

Status: ACTIVE
Branch: `feature/context-runtime-routing-v1`
Workspace: `WS-HUMANOS`
Parent: extends promoted `HOS-CTX-001`
Baseline: `runtime-0.1` at `aa7a81f00ab21cb6c582391d41603b84b70c5f7f`

## Outcome

Make the promoted development Context Registry operational inside the HumanOS runtime without turning it into a broad speculative Context Layer. A normal HumanOS request can be inspected before model/tool execution, related work can be surfaced, ambiguous workspace/workstream matches fail closed, and deterministic routing context can be supplied to Mirror without altering the exact human transcript.

## Scope

- add one runtime-facing context routing service that reuses `context_registry.py`;
- expose structured route results for Mirror/host use;
- distinguish ordinary non-development conversation from context-managed development/work requests;
- block model/tool execution when a context-managed request is ambiguous;
- pass deterministic routing context into the Agent context packet without rewriting human input;
- preserve public/private registry boundaries;
- add focused tests and full regression evidence;
- update registry/status/index only for this bounded workstream.

## Security invariants

1. Exact human input remains the Notebook transaction input; routing metadata is separate host context.
2. Ambiguous context-managed requests do not reach the model or tools.
3. No cross-workspace private data is copied into another workspace.
4. Private overlay paths/notes/display names are not emitted in routing packets.
5. Routing cannot merge, switch branches, write files, or authorize tools.
6. Ordinary conversation that does not match the development registry is not falsely blocked.
7. Existing `context_registry.py` remains the single registry/routing authority for schema-v1.

## Acceptance criteria

1. A model-loader continuation returns `CONTINUE` / `HOS-MAL-001` with useful resume metadata.
2. A context/runtime integration request extends the promoted context stream rather than reopening HOS-CTX-001 history.
3. Equal client/employer/private workspace matches require confirmation and no Agent invocation occurs.
4. A request with no registry relevance is marked not applicable and proceeds normally.
5. Deterministic route metadata is present in the model context packet while the Notebook transcript preserves the exact original input.
6. Private overlay metadata such as local roots and private display names is absent from the model routing packet.
7. Full HumanOS regression CI remains green.
8. Encrypted-backup/full-suite CI remains green.

## Known exclusions

- semantic/vector routing;
- automatic GitHub branch discovery;
- automatic branch checkout/merge;
- full identity/temporal Context Layer;
- cross-workspace transfer authorization UI;
- speculative expansion beyond current development need.

## Rollback

Delete/revert this branch. HOS-CTX-001 remains promoted on `runtime-0.1` and no Notebook migration is required.

## Next action

Implement the runtime routing bridge and tests, then verify the exact commit before any promotion decision.
