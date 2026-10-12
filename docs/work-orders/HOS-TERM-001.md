# HOS-TERM-001 — Terminal delivery contract

Status: IMPLEMENTED CANDIDATE / INDEPENDENT REVIEW AND OWNER PROMOTION PENDING
Workspace: WS-HUMANOS
Baseline: `runtime-0.1` at `0fe4ea5751bb17be30656a5c95809b79d6718636`
Branch: `fix/terminal-delivery-contract-v1`

## Problem and bounded acceptance

A Work answer told Jon to run `python3 scripts/smoke_codex_import.py` from an
arbitrary directory, where that relative path fails. For local Mirror answers,
compile one terminal rule into the system packet, bind it in durable task state,
and reject unsupported shell instructions before Notebook final checkpoint and
stdout delivery. The same rule must apply to delegated Work Supervisor turns.
Keep ordinary non-terminal answers unchanged. Use synthetic fixtures only.

The supported syntax is intentionally small: one bash block containing `set -e`,
one literal absolute `test -f` or `test -d` guard, and one reviewed action. The
actions are the PR #115 synthetic smoke script at the expected owner checkout
path, `/bin/ls` of that checkout, and `/usr/bin/git -C` status of that checkout.
The validator checks the copyable text and known action shape. It cannot prove
the contents of the owner's checkout or script; the smoke block stops if the
script is absent. Other terminal actions are rejected as unsupported pending a
reviewed recipe. Branch mutation, shell operators, placeholders, relative paths,
extra commands, and multiple blocks are rejected.

## Boundaries and evidence

- **Designed:** `docs/architecture/HUMANOS_ARCHITECTURE_BASELINE_PLAN.md` describes
  governed tools and context, but no terminal response delivery validator.
- **Implemented:** canonical `context_registry.py` routes workspace/workstream;
  `execution_contracts.py` validates FRIEND_PACKET objects; `engine.py` builds
  local model packets and checkpoints finals; `server_core.py` delivers stdout.
- **Invoked/enforced locally:** this candidate adds packet binding, delegated
  packet omission rejection, final validation, and delivery sink validation.
  Synthetic integration and full-suite results belong in the PR.
- **External Work:** the inspected create/send/read thread tool schemas expose
  prompts and observation but no verified pre-delivery transform. The
  `terminal_delivery.py` stdin filter is a handoff mitigation for a controlled
  wrapper; it is not evidence of automatic ChatGPT Work interception.

Rollback: revert this candidate commit/PR. An older unfinished task without the
bound policy fails closed and needs explicit reconciliation before resuming.

Next action: independent review of the exact candidate head, then owner decision
on promotion. Do not merge or operate on the owner checkout as part of this slice.
