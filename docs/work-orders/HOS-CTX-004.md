# HOS-CTX-004 — Notebook Context Recovery / Human-Friendly Continuation

Status: IMPLEMENTED / VERIFICATION PENDING  
Branch: `feature/context-notebook-recovery-v1`  
Workspace: `WS-HUMANOS`  
Parent: extends promoted `HOS-CTX-003`  
Baseline: `runtime-0.1` at `c2d4643df58c226fe24fbbe66b5264e029344129`

## Relationship classification

**EXTEND as a new bounded workstream.**

Repository discovery found related historical branches `feature/recovery-ledger-continuation`, `feature/local-notebook-recall`, `feature/context-reference-engine-v1`, `feature/conversational-reference-binding`, and `fix/nonblocking-recovery`. They are behind or diverged from the canonical runtime and are not resumed wholesale. Canonical `references.py`, `notebook.py`, HOS-CTX-002, and HOS-CTX-003 already contain the verified evidence/binding patterns this slice extends.

## Outcome

Let Mirror resolve explicit historical continuation requests from verified Life Notebook evidence without making Jon manage TX/HCID/LN identifiers.

Examples:
- `continue what we were doing earlier`
- `go back to that model thing from earlier`
- `continue what we were doing yesterday`

## Scope

- search checkpointed historical `CONTEXT_ROUTE` evidence across HCIDs;
- verify Notebook integrity before historical binding;
- keep source transaction IDs host-only;
- use fresh deterministic routing as a narrowing signal;
- support a bounded UTC `yesterday` filter;
- resolve automatically only when one verified eligible workstream remains;
- if several remain, fail closed and show human-readable workstream topics/titles;
- preserve exact human transcript;
- record `CONTEXT_NOTEBOOK_RECOVERED` host evidence;
- reject unfinished/unverified historical transactions;
- preserve existing immediate-session, file/plan, and delegated-work authority boundaries.

## Security invariants

1. Notebook verification must pass before historical evidence is trusted.
2. Only CHECKPOINTED transactions with non-ambiguous CONTEXT_ROUTE evidence are eligible.
3. Archived/superseded workstreams cannot be recovered.
4. Raw source TX IDs never enter model route context or human disambiguation text.
5. Historical recovery never grants branch/tool/merge authority.
6. Ambiguity prevents model/tool execution.
7. Workspace hints constrain historical candidates; no implicit cross-workspace selection.
8. Ordinary conversation does not trigger historical recovery.
9. Exact human input remains immutable.
10. No embeddings, semantic vector store, or competing memory subsystem is introduced.

## Acceptance criteria

1. Historical continuation can recover a verified workstream across HCIDs.
2. One eligible historical workstream resolves to CONTINUE / NOTEBOOK_RECOVERY.
3. Multiple eligible workstreams require human-friendly confirmation.
4. Confirmation text contains topic/title labels, not raw transaction IDs.
5. Model is not called while confirmation is required.
6. Tampered Notebook evidence fails closed.
7. Unfinished/unverified transactions cannot seed recovery.
8. Source transaction provenance remains host-only.
9. Ordinary conversation bypasses historical recovery.
10. Existing HOS-CTX-003 immediate continuity remains intact.
11. Focused tests pass.
12. Full HumanOS CI matrices pass before promotion.

## Deliberate boundaries

No semantic embeddings, broad entity graph, automatic summary generation, whole-Brain inference, or recovery execution/replay. This slice resolves verified workstream context only.

## Promotion gate

Do not merge or release automatically. Promotion requires Jon's explicit approval after verification evidence is recorded.
