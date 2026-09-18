# HOS-CTX-011 — Mirror Host Intent & Runtime Identity

Status: REVIEW  
Branch: `feature/context-host-intent-runtime-identity-v1`  
Workspace: `WS-HUMANOS`  
Parent: extends promoted `HOS-CTX-010`  
Baseline: `runtime-0.1` at `24458559d7755eeb40d89cadff5e9401d71e4c3c`

## Relationship classification

**CREATE_SEPARATE within the Context Engine lineage.**

The local Mirror transcript exposed a distinct control-plane problem rather than a
continuation bug in the graph bridge: deterministic host/runtime questions were being
sent through workstream routing or left to model tool selection. This slice fixes that
boundary without reopening CTX-010 or changing graph semantics.

## Outcome

Make current-turn host facts deterministic and higher-priority than development
workstream routing.

Host-direct intents in schema v1:

- local time;
- current-session Notebook status;
- runtime capability/tool inventory;
- Mirror/runtime model identity.

The base runtime resolves those facts with host tools before the model can improvise.
The Context Router does not create a `CONTEXT_ROUTE` for those turns.

## Runtime identity

`runtime_identity` reports:

- Mirror as the HumanOS human-facing interface;
- the exact model name bound into the current durable task state;
- the default runtime provider as local Ollama.

The answer does not infer model identity from HOS-MAL-001, HOS-MR-001, prior
conversation, or model self-report.

## Capability truthfulness

Capability questions such as `can you code?` resolve from the HumanOS capability
registry. The deterministic answer distinguishes:

- creating/writing code files inside the selected workspace after exact-request approval;
- HumanOS self-modification/source-write, which is not connected in this runtime.

## Tool-selection boundary

`current_time`, `read_notebook`, `runtime_capabilities`, `runtime_identity`, and
`recall_notebook` are host/human-only runtime tools. They are omitted from model tool
instructions. If a model nevertheless proposes one without a direct human-derived
request, authorization fails closed and the denial is audited.

This prevents an ordinary turn such as `yes, continue with the app` from causing an
irrelevant clock lookup.

## Scope

Implementation:

- `runtime_info.py`
- `capabilities.py`
- `engine.py`
- `server.py`
- `tests/test_runtime_info.py`
- `tests/test_runtime.py`
- `tests/test_context_runtime_bridge.py`
- `docs/work-orders/HOS-CTX-011.md`
- `config/context_registry.public.json`

## Acceptance

1. `what model are you?` returns host-grounded runtime identity without a model call.
2. Runtime identity reports the model bound to the current durable transaction.
3. Host identity/tool questions do not create a development `CONTEXT_ROUTE`.
4. `what tools do we have?` returns the deterministic capability registry without routing to Browser/other workstreams.
5. `can you code?` truthfully distinguishes workspace code creation from HumanOS self-modification.
6. A model-proposed `current_time` on a non-time request is denied and audited.
7. Existing explicit time/Notebook/capability commands remain compatible.
8. No new source-write, shell, network, merge, or execution authority is granted.
9. Full regression and encrypted-backup matrices pass.
10. Promotion remains owner-gated.

## Deferred

This slice does **not** solve:

- durable ambiguity selection / `confirmed!` candidate choice;
- duplicate ambiguity display;
- ordinary conversational-goal continuity such as `the app`;
- semantic references such as `that file`;
- human-friendly recovery of the 22 unfinished transaction warnings;
- graph runtime consumption.

Those remain separate bounded slices.

## Rollback

Before promotion, switch back to `runtime-0.1` or delete this branch. No Notebook
evidence, workspace files, or canonical graph data is migrated by this slice.
