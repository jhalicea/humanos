# HumanOS Runtime 0.1

Extends `/Users/jhalicea/humanos/server.py`, retaining HumanOSRuntime and the
Mirror interface. Python 3.9+ standard library; local Ollama already installed.
No new server, cloud upload, package installation, or background daemon.

Start:

```sh
cd /Users/jhalicea/humanos
python3 server.py
```

One useful turn:

```sh
python3 server.py --context runtime.md --message 'Read runtime-check.txt and tell me its verification phrase and code.'
```

Copy the exact HCID displayed at session start to continue that page:

```sh
python3 server.py --session HCID-FROM-YOUR-SESSION
python3 server.py --status
python3 server.py --resume TX-FROM-YOUR-SESSION
python3 -m unittest discover -s tests -v
```

Ctrl-C stops execution. Startup reconciles projections, lists unfinished turns,
and never silently reruns a model or tool. Resume is explicit. Reads may retry;
an interrupted create with uncertain outcome stops for inspection. Do not edit
SQLite task state to force a retry. That manual reconciliation UI remains open.

Configuration is in `config.json`. Relative paths resolve beside that file, so
launching from another directory cannot silently create a different vault.
`HUMANOS_MODEL` and `HUMANOS_ENDPOINT` override inference configuration. Runtime
0.1 implements local Ollama only; the Model protocol isolates provider changes.
Remote endpoints and redirects are rejected until a remote provider policy is added.

## Notebook and boundaries

Old daily Markdown files are unchanged. New local runtime transactions are stored
under the existing `HumanOS_Vault/runtime/`:

- `notebook.sqlite3`: identities, append-only transcript, tasks, transactions,
  append-only hashed events, recovery entries.
- `pages/`: per-conversation JSON (exact text) and readable Markdown projections.
- `active-index.json`, `bindings.json`: verified projections of the ledger.
- `recovery.jsonl`: append-only fallback errors and exact input on capture failure.
- `recovery-copies/`: prior projections preserved before recovery repair.

JSON strings preserve CR/LF, whitespace, Unicode, corrections, and speaker order.
Primary transcript excludes hidden reasoning. Model proposals, selected source
hashes, permissions, tool stdout/stderr/artifacts/errors live in audit/task records.
No derived summaries replace primary transcript. SQLite is local authoritative
runtime evidence; this does not supersede existing canonical Google Drive records.
There is no Drive synchronization in 0.1. The provider boundary is the Notebook
adapter API (start/append/checkpoint/recover), separate from the model protocol.

Final assistant text is stored and read back before emission. Successful output
writes are recorded separately as WRITTEN_TO_OUTPUT_STREAM; this proves output
stream delivery, not human receipt. An interrupted delivery remains uncertain.
CLI session/status/error diagnostics are operational metadata, not assistant chat
messages. Interactive file-approval prompts and answers are captured as transcript.
This runtime does not automatically capture external Codex/ChatGPT conversations.

Local checkpoint verification covers SQLite integrity, transcript hashes, copied
legacy audit chain, complete page/index/binding projections, final response versus
task state, and recovery closure. Hashes detect accidental tampering, not an attacker
who can rewrite the database and recompute them. There is a single-writer lock.
No encryption or full CIBE merge/split/provider migration UI is claimed.

## Tool scope

Default workspace is `/Users/jhalicea/humanos/workspace`. Read/list are authorized
inside that scope. File creation requires interactive per-request approval and
never overwrites. Absolute paths, traversal, hidden paths, symlinks, hardlinked
files, devices, and files over 16 KiB are rejected. No shell or arbitrary Python.
This is a narrow file capability boundary, not a general operating-system sandbox.
Only put files you authorize HumanOS to read in the workspace. Never configure it
as your home directory, whole disk, Notebook, or canonical records directory.

Turns are limited to six model calls and 180 seconds of tracked execution; each
model call has a socket timeout of at most 90 seconds. An abrupt process kill may
lose the in-flight elapsed-time increment, but the persisted iteration count still
bounds attempts. Resuming with a different model/workspace requires reconciliation.
Context selection is explicit via `--context filename.md`, with a 24 KB source
budget; unselected Notebook history is never dumped into a model prompt.

## Preservation and provenance

Original server SHA-256:
`b3a7a53446f26dc828b0d917d60c8361d015efdd40f07d52979e3ad807fb571e`.
Backup: `backups/runtime-0.1-before-20260906/server.py`.
Git rollback tag: `runtime-0.1-before` (commit `419d231`).
Restore the original entry point while retaining new files and Notebook data:

```sh
git restore --source runtime-0.1-before -- server.py
```

`audit.py` is copied unchanged from
`/Users/jhalicea/Downloads/humanos_v018_integrity_scanner-2/humanos_kernel/audit.py`
SHA-256 `2516b3b29c8f4192554849119460a7f7171c80de973501e2ff2f90e3d7d90be0`.
Other legacy packages and their tests are untouched. This is an extension of the
existing local HumanOS front door, not a replacement for the legacy Drive runtime.

The Constitution file is a locally retrieved governance copy with its source link.
`core/runtime.md` is an explicitly labeled implementation note, not a new canonical
decision. Owner's 2026-09-06 request authorizes this bounded local implementation;
older specifications withholding independent deployment remain preserved as history.
