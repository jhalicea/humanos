# HOS-CTX-003 — Session Workstream Continuity

Status: IMPLEMENTATION CANDIDATE / VERIFICATION PENDING  
Branch: `feature/context-session-continuity-v1`  
Workspace: `WS-HUMANOS`  
Parent: extends promoted `HOS-CTX-002`  
Baseline: `runtime-0.1` at `3cf3ef1a2346fef583cabfa2844ef57fa65a47d4`

## Outcome

Make short follow-up language inherit the immediately preceding verified HumanOS workstream context inside the same HCID/session without creating a second memory system.

This is the next bounded primitive in the same lineage that should eventually become the broader HumanOS Context Engine / "Brain".

## Design rule

HumanOS keeps one evolving context architecture:

- Life Notebook = durable chronology/evidence/provenance;
- Context Engine = determine what verified context is relevant now;
- Mirror = human-facing interaction;
- models/agents/tools = consumers of bounded context, never the authority that creates it.

Future context/memory capabilities should extend this lineage instead of creating competing per-feature memory systems.

## Scope delivered

- short explicit continuation phrases such as `do it`, `continue`, `keep going`, and `go ahead` may inherit a verified prior workstream;
- inheritance is limited to the immediately preceding transaction in the same HCID;
- the prior transaction must be `CHECKPOINTED` and contain a deterministic non-ambiguous `CONTEXT_ROUTE` event;
- fresh explicit routing evidence always wins over inherited session context;
- an intervening ordinary or unfinished turn breaks implicit inheritance;
- file/plan reference bindings and delegated-work bindings disable implicit workstream inheritance because they are more specific authorities;
- archived/superseded workstreams are not inherited;
- inherited route provenance is stored host-side with `CONTEXT_SESSION_CONTINUED`;
- the model sees only `origin: SESSION_CONTINUITY`, not the source transaction ID;
- no tool permission, branch switch, merge, file write, or execution authority is granted by continuity.

## Security invariants

1. Session continuity never overrides an explicit current route.
2. Ambiguous current workspace/workstream routing still fails closed.
3. Only the immediately preceding verified transaction can seed implicit continuity.
4. An unfinished prior transaction cannot seed continuity.
5. Bare acknowledgements such as `yes` do not silently become workstream continuation.
6. Source transaction IDs remain host/audit data and are not injected into model prompts.
7. Private overlay details remain subject to HOS-CTX-002 redaction.
8. Existing file/plan reference authority is not widened by workstream continuity.
9. Existing delegated WorkBoard authority is not widened by workstream continuity.
10. Exact human input remains unchanged in the Life Notebook.

## Acceptance criteria

1. A verified model-loader turn followed immediately by `do it` resolves to `CONTINUE / HOS-MAL-001`.
2. The inherited route is marked `SESSION_CONTINUITY`.
3. The source transaction is recorded only in host audit evidence.
4. The source transaction ID is absent from model route context.
5. An intervening ordinary turn prevents stale implicit inheritance.
6. An unfinished immediately prior turn prevents inheritance.
7. A fresh explicit route to another workstream wins.
8. Bare `yes` does not inherit.
9. Same-HCID continuity survives Notebook close/reopen.
10. Existing HOS-CTX-002 routing/security tests remain green.
11. Full HumanOS regression matrix passes.
12. Encrypted-backup/full-suite matrix passes.

## Deliberate boundaries

This slice does **not** implement:

- cross-HCID or cross-session semantic continuation;
- automatic selection among old Notebook transactions;
- human-friendly recovery UX for unfinished transactions;
- entity/relationship graph memory;
- temporal relevance beyond the immediately preceding verified turn;
- automatic context summarization;
- semantic/vector context retrieval;
- delegated WorkBoard routing;
- broad "Brain" inference.

Those should extend this Context Engine lineage in later bounded workstreams when concrete needs justify them.

## Relationship to future HumanOS Context Engine

HOS-CTX-003 is not a convenience patch to be replaced later. Its verified-session-binding rule becomes one primitive beneath the future Context Engine.

Likely future layers may add temporal context, entity/relationship context, Notebook evidence resolution, goals/project state, permission boundaries, and context-package composition. Exact numbering/scope should be driven by real development needs rather than speculative implementation.

## Rollback

Revert this branch. HOS-CTX-001 and HOS-CTX-002 remain promoted on `runtime-0.1`. No Notebook schema migration is introduced.

## Next action

Run focused tests, full CI, review the diff/security boundaries, then leave promotion pending for Jon. Do not merge automatically.
