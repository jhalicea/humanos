# HumanOS Runtime 0.1 — local build report

Date: 2026-09-06. Status: implemented and locally tested; not production-qualified.
Installed in `/Users/jhalicea/humanos`. HumanOS and Mirror names are retained.

## Before

The existing 111-line `server.py` had a HumanOSRuntime class, an Ollama chat call
configured as `llama3`, optional constitution loading, and daily Markdown appends.
It stripped input whitespace, intercepted any mention of “notebook,” and had no
session binding, idempotent transaction, governed tool loop, or restart recovery.
The folder was not a Git repository and had no tests. Existing vaults under
`/Users/jhalicea/humanos`, `/Users/jhalicea`, and `/Users/jhalicea/Documents` were
identified; their historical daily files were not moved, merged, or edited.
Legacy HumanOS v0.20 in Downloads was inspected, and its audit code was reused.
Its remaining code/tests and the project’s existing projector work are untouched.

## Files changed or added in the installed runtime

- `server.py`: existing entry point and HumanOSRuntime interface extended with
  stable config paths, CLI session/resume/status, exact input and output capture.
- `notebook.py`: SQLite local Notebook adapter, E1 identity and explicit binding,
  ordered append-only transcript, idempotency, projections, integrity/readback,
  fallback recovery, task persistence, startup reconciliation and writer lock.
- `engine.py`: model-neutral protocol, configurable local Ollama adapter, selected
  context packet, bounded agent loop, deterministic authorization and narrow tools.
- `audit.py`: unchanged audit-chain implementation copied from legacy v0.20;
  exact source and SHA-256 are recorded in README.
- `config.json`: model, endpoint, vault/core/workspace paths and execution limits.
- `.gitignore`: excludes Notebook data, workspace, backups, evidence and secrets.
- `core/constitution.md`: sourced local copy of ratified v0.2, with provenance.
- `core/runtime.md`: explicitly labeled current implementation note.
- `tests/test_runtime.py`: 36 automated tests.
- `verify_live.py`: real Llama subprocess and independent transcript/readback test.
- `README.md`, `BUILD_REPORT.md`: operation, scope, provenance, limitations, rollback.
- `workspace/runtime-check.txt`: non-private verification fixture (outside Git).
- `HumanOS_Vault/runtime/`: new ledger, page/index/binding projections and recovery
  records inside the existing vault; original daily files remain unchanged.
- `evidence/`: final test output and machine-readable live verification results.

A review copy under this Codex project’s `runtime-patch/` is a build artifact,
not a second installed runtime. The start command always targets the original
`/Users/jhalicea/humanos` folder.

## Detected backend and tested flow

Ollama HTTP service was verified at `http://127.0.0.1:11434`. Installed models:
`llama3:latest` (8B, Q4_0) and `llama3.2:latest` (3.2B reported, Q4_K_M).
The existing Llama 3 choice was retained: all live milestone tests use
`llama3:latest`. No new model was downloaded. Python is macOS Python 3.9.6.

The live flow issues an HCID/page, starts the Notebook transaction and preserves
input, loads local governance/context, calls Llama, validates its file request,
authorizes a workspace read, executes and records its observation, continues
Llama, captures the final answer, verifies page/index/binding/checkpoint, writes
the same answer to stdout and records delivery.

Observed answer: `continuity belongs to Jon. HOS-LOCAL-62947.`
The first live attempt rejected mixed tool/final JSON and stopped truthfully.
That transaction was resumed after adding bounded format repair and completed
without duplicating the input. The failure remains in the recovery history.
Fresh live testing also exercises the repair automatically, without human retry.

## Verification commands and results

Run from `/Users/jhalicea/humanos`:

```sh
python3 -m unittest discover -s tests -v
python3 verify_live.py
```

Final installed unit suite: **36 passed, 0 failed**. Includes every requested
category: new/ambiguous binding, exact capture, duplicates, readback, simulated
write/DB failures and fallback recovery, adapter call, unauthorized/authorized
tools, agent completion, surfaced tool failures, resume, backend outage, and
end-to-end final capture/output. Additional tests cover traversal, symlinks,
hardlinks, non-overwrite, writer locking, tamper detection, immutable completed
turns, malformed-model repair, uncertain writes, and bounded iteration/time.

Fresh live verification passed with real Llama and independently matched output
to the final Notebook message. Per-run JSON evidence records transaction/page,
model/tool call counts, event order, status and exact output match.
The initial test command had a staging-directory mistake, corrected before tests
ran. A later test fixture used the unresolved macOS temporary path and failed one
assertion; corrected to the resolved workspace path. All final tests pass.

## Notebook status and open limits

Successful live test transactions are locally CHECKPOINTED. Final model response
capture is proven against actual subprocess stdout, including exact text and
readback of page/index/binding. This proves stream output, not human receipt.

The current Codex development task has a distinct local page:
`LN-20260906-952f8472c36745e081aaeedfe2f583d5`.
Its exposed messages were preserved through the existing Notebook adapter with
readback, under `TX-CODEX-01a0782a-4731-7303-b7e0-cb75d74cffc6`.
It remains DEGRADED CAPTURE / RECOVERY_REQUIRED: this task’s final response cannot
be read back as emitted before the turn ends, and canonical Drive synchronization
is not implemented. No prior Mythos page was rebound by title or similarity.

Other open limits:

- Local prototype, single writer; no unattended service or production claim.
- Drive sync and full CIBE merge/split/reconciliation workflows remain unimplemented.
- Interrupted file creation with unknown outcome requires manual inspection;
  it is deliberately not automatically replayed. No reconciliation UI yet.
- Workspace tools are read/list/create only, not an OS shell sandbox; creation
  never overwrites and needs interactive approval. No shell/Python/Git tools.
- Hashes are not tamper-proof against an owner-level database rewrite; no
  application encryption or multi-user authentication is provided.
- Model outputs can still be inaccurate or violate the response format. Invalid
  proposals are rejected and repaired only within the finite task budget.
- Context is explicitly selected with `--context`; automatic historical retrieval
  is not implemented. Governing source copies need refresh when canon changes.
- Remote/cloud adapters are not implemented. The local-only endpoint rule must
  be extended with an authorized transport policy for future remote compute.
- Socket timeouts plus persisted iteration counts bound normal execution;
  hard process termination can lose the in-flight elapsed-time increment.
- If all storage writes fail, no runtime can promise durable capture; errors
  remain visible and no checkpoint is claimed. Corrupt fallback JSON needs review.

## Start and rollback

```sh
cd /Users/jhalicea/humanos
python3 server.py
```

To test a useful task:

```sh
python3 server.py --context runtime.md --message 'Read runtime-check.txt and tell me its verification phrase and code.'
```

Resume the exact HCID printed on startup with `--session HCID`; resume an unfinished
local model task with `--resume TX`. Inspect all state using `--status`.

Git branch: `runtime-0.1`. Original rollback commit: `419d231`, tagged
`runtime-0.1-before`. A matching dated backup of `server.py` is preserved.
To restore only the original entry point without deleting Notebook evidence:

```sh
git restore --source runtime-0.1-before -- server.py
```

## One next build step

Implement an idempotent adapter that synchronizes verified local Notebook
transactions with the existing canonical Drive page/index/binding/transaction
records, including conflict detection and readback, without changing local
transaction identity or rewriting transcript history.

## 2026-09-06 greeting repair

A real interactive `hi` turn showed that Llama confused the already-loaded
Constitution context with a workspace file and twice requested `constitution.md`.
The file existed in `core/`; the error was a model/tool-boundary defect rather than
missing local data. Runtime context is now strictly opt-in through `--context`,
workspace reads must be grounded in the current human request, and the model prompt
explicitly separates conversational answers, loaded records, and workspace tools.
The prompt also requires all explicit parts of a request to be answered from exact
observations. Automated tests cover empty-context greetings and denied ungrounded
reads. Real isolated-vault tests cover both `hi` and the file-reading exercise.
# 2026-09-07 runtime awareness repair

The reported session contained 14 transactions and 28 saved messages, including
the model's false claims that the Notebook was empty. These historical statements
were preserved. A captured answer does not establish its factual correctness.

Added runtime_info.py for session-bound, read-only Notebook queries, the local
clock, and an explicit capability report. engine.py now routes those requests to
verified runtime answers through the existing final-capture/checkpoint path and
loads bounded recent same-session history for model turns. Query authorization
and results enter the existing provenance ledger. No web/Drive connection added.
tests/test_runtime_info.py adds eight behavioral checks; the complete automated
suite passes 47 tests (`python3 -m unittest discover -s tests`). Existing test
fixtures now use a neutral default request; file tests explicitly request their
target file. README.md documents commands and scope. Rollback source
before this repair: commit 1cf4f80. The user's active notebook was inspected
read-only; live checks use isolated temporary notebooks.

Live verification: initial five-turn run passed recall, clock, Notebook and
capture checks but failed the file-answer assertion (4 passed, 1 failed).
Added a bounded rejection of final answers that skip an explicitly requested
file read. The two-turn Notebook-to-file retest passed both turns, including the
exact phrase/code, output/transcript equality, and checkpoint readback. These are
local results, not proof of semantic correctness for all model answers. Natural
language routing is deliberately limited; slash commands are the reliable entry
points. Final capture in the local runtime is proven by output comparison; capture
of this separate Codex conversation remains degraded/unverified.
