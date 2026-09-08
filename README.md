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
An unfinished turn no longer blocks later turns on the same Notebook page. Each
turn keeps its own transaction and recovery state. If an older turn is resumed
later, its response is appended at the time it is actually produced, preserving
the visible chronology. Inputs retained by the fallback recovery ledger are
restored as pending transactions without fabricating assistant responses.
Run `python3 verify_nonblocking_live.py` for an isolated real-model check of this
recovery behavior.

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

Default workspace is `/Users/jhalicea/humanos/workspace`. Read/list require the
scope saved from the human's original request. File creation requires interactive per-request approval and
never overwrites. Absolute paths, traversal, hidden paths, symlinks, hardlinked
files and devices are rejected. UTF-8 text reads allow up to 16 MiB, returned in
16 KiB pages; file creation remains limited to 16 KiB. No shell or arbitrary Python.
This is a narrow file capability boundary, not a general operating-system sandbox.
Only put files you authorize HumanOS to read in the workspace. Never configure it
as your home directory, whole disk, Notebook, or canonical records directory.

Turns are limited to six model calls and 180 seconds of tracked execution; each
model call has a socket timeout of at most 90 seconds. An abrupt process kill may
lose the in-flight elapsed-time increment, but the persisted iteration count still
bounds attempts. Resuming with a different model/workspace requires reconciliation.
Context selection is explicit via `--context filename.md`, with a 24 KB source
budget; unselected governance records and Notebook history are never dumped into
a model prompt. Core ownership and tool rules remain in the small system prompt.
Workspace reads must also be grounded in the current human request.

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
# Verified local information

In the interactive runtime, use `/time`, `/notebook`, or `/capabilities`.
Common questions about the time and this conversation's Notebook are also routed
to these read-only local queries. They do not require a model or an approval prompt.
Notebook results cover the explicitly bound session, include a bounded excerpt,
and distinguish local persistence from unconnected Drive synchronization.
Ordinary model turns receive at most 12 recent checkpointed transcript messages
from this session, within an 8,000-byte budget. Full history remains in the ledger.
Restart an already-running process to load code changes.

## Durable tools and recovery

`capabilities.py` supplies the model's tool contract, argument validation and
`/capabilities` output. Clock, bound-session Notebook and file requests all use the
same executor and authorization audit path. Internet and Drive remain unavailable.

Each new task persists its original input hash, session, workspace, exact allowed
read/list paths, and policy version. Resume validates and reuses that scope;
callbacks can narrow reads, never expand them. Denials and exact write approvals
are saved with their authorization event. Mixed negative file requests fail closed;
use a simple affirmative request such as `read folder/note.txt`.

`CHECKPOINTED` describes verified local capture. Delivery has separate durable
states: `PREPARED_NOT_CONFIRMED`, `DELIVERING`, `OUTPUT_UNCERTAIN`, and
`WRITTEN_TO_OUTPUT_STREAM`. Startup lists saved answers with unconfirmed output,
including older checkpointed tasks. `--status` shows them; `--resume TX-ID` retries
the exact saved final without rerunning completed tools or appending transcript.
An uncertain output retry may repeat terminal text. Confirmed output is not emitted
again by a duplicate resume. Output-stream confirmation does not prove human receipt.
Unconfirmed assistant messages remain preserved but are excluded from model history.

Older unfinished tasks without saved scope require explicit reconciliation; the
runtime does not infer new permissions for them. An interrupted file creation with
unknown outcome still stops for inspection, never replays automatically. A guided
reconciliation interface is not yet implemented.

The recovery schema gains a `scope` column without changing existing records.
Before an installed upgrade, stop the running process and retain a private backup
of its vault. The code rollback baseline is `2cf2c98`; prior code can read the
additive database schema but does not implement the new delivery distinctions.
Keep the upgraded vault as evidence rather than reverting data to an older backup.

Validation:

```sh
python3 -m unittest discover -s tests -v
python3 verify_durable_live.py
```

The first command is offline and includes real process-death/restart tests. GitHub
Actions runs it on Linux and macOS with Python 3.11 and 3.13. The second is opt-in,
uses configured local Ollama, and always creates an isolated temporary test vault
and workspace. It checks five real turns including exact final output/readback.
CI does not prove local-model quality. Branch protection and auto-deployment are
not configured. See `REVIEW.md` for the milestone and reviewer guidance.

## Reading and organizing a selected folder

Choose one dedicated folder explicitly when starting HumanOS:

```sh
python3 server.py --workspace "/absolute/path/to/your/chosen/folder"
```

The whole home directory, system root, runtime source directory and overlapping
Notebook/governance directories are rejected. The default remains the existing
`workspace` folder. Selecting a folder does not authorize moving its files.

Inside the conversation:

```text
/files
/read "notes.txt"
/duplicates
/duplicates "Receipts"
/organize
/move "Old folder" "Archive/Renamed folder"
/apply PLAN-ID-FROM-PREVIEW
/undo PLAN-ID-FROM-PREVIEW
/source server.py
```

`/organize` previews top-level files grouped by extension, preserving existing
subfolders. `/move` previews one file or folder move. Apply and undo each show
the exact paths and require typing `yes`. Nothing overwrites existing destinations.
Plans and progress stay in the private Notebook database, with audit evidence and
the selected folder's identity. Restart does not apply any plan automatically.
`--status` lists interrupted plans. An explicit `/apply` or `/undo` reconciles a
completed in-flight rename by its saved identity/content proof before continuing.

Undo restores unchanged moved items; empty destination folders created by the
plan may remain. Files edited since preview or after moving require inspection.
Do not edit the selected tree concurrently while applying a plan: each rename is
atomic and non-overwriting, but the complete multi-file operation is not one
filesystem transaction. A change in the final check/rename window can leave an
uncertain outcome, which is preserved and reported rather than overwritten.

Duplicate checks compare complete SHA-256 hashes and byte counts and never delete
anything. Scans exclude hidden/protected paths, links and special files. Limits:
2,000 entries, depth 20, 512 MiB of hashing and 20 seconds per hashing operation;
plans allow at most 100 moves. Incomplete results are labeled. Text reads support
Text reads use UTF-8. Contextual understanding also has bounded local extractors
for accessible PDF literal text and common Office XML archives (`.docx`, `.xlsx`,
`.pptx`, `.odt`). Image context is limited to verified format and dimensions;
no OCR or visual interpretation is claimed. Binary files can still be listed,
moved by an approved plan, and checked for duplicate content.
Natural language recognition is deliberately narrow. Use quoted slash commands
when specifying a subfolder, filename with spaces, or exact destination.

## Contextual file intelligence

Runtime 0.1 can make a local-model suggestion about where files belong while
keeping the file manager and approval boundary in charge. Start with one
explicitly selected folder:

```sh
python3 server.py --workspace "/absolute/path/to/your/chosen/folder"
```

Then use:

```text
/understand "notes.md"
/smart-organize
/apply PLAN-ID-FROM-PREVIEW
/undo PLAN-ID-FROM-PREVIEW
```

`/understand` reads a bounded UTF-8 excerpt (up to 4 KiB) plus file metadata and
returns a classification, rationale, and confidence. It also extracts bounded
local context for accessible PDF literal text and standard Office XML content
in `.docx`, `.xlsx`, `.pptx`, and `.odt` files. Files larger than 4 MiB,
malformed documents, unsupported formats, and archive structures beyond the
safety limits remain metadata-only. Images provide only file format and
dimensions: OCR and visual interpretation are not connected. The excerpt is
used for the model call but is not written into the audit event; hashes and the
exact source proof are retained for provenance.

`/smart-organize` analyzes at most 10 top-level files and produces a durable
preview. The local Ollama model proposes short relative folders; the proposal
is evidence, not authority. No file moves during analysis. Applying a plan
shows every source and destination and requires you to type `yes`; the move is
non-overwriting, verified against the preview proof, and undo remains available.
Every turn, model decision, tool request, approval, observation, and final
response follows the existing Life Notebook transaction and readback rules.

“Whole computer” is implemented as explicit folder-by-folder permission
compartments. The runtime rejects the home directory, system root, its own
source, the Notebook/vault, and overlapping governance paths. A future
multi-location registry can enroll several separately approved folders without
changing these transaction semantics. Duplicate detection remains report-only
and never deletes files.

Contextual limits are intentionally bounded: one file is at most 16 MiB, a
contextual plan is at most 10 top-level files and 120 seconds, and existing
scan/hash limits still apply. The plan is idempotent by transaction and path;
repeating a request does not call the model or move files twice.

## Inbox Librarian

The selected workspace can contain an `inbox/` folder for unsorted files. Use
the librarian preview to classify its top-level contents:

```text
/organize-inbox
```

For each file, Mirror records the available bounded context, proposes a
relative project or research folder, and checks whether the name is generic
(`internet.pdf`, `document.pdf`, `IMG_1234.jpg`, and similar). A generic name
gets a clearer filename proposal while preserving its extension. The preview
shows the original path, proposed path, explanation, confidence, and rename
suggestion. It does not change the inbox.

Applying the saved plan still requires the exact plan ID and a separate human
approval. Moves and renames are non-overwriting, hash-checked, reversible, and
logged with the original name, final name, content proof, model, decision, and
Notebook transaction. Repeating the same turn is idempotent. Files with no
extractable content remain metadata-only and are flagged for review rather than
being assigned a fabricated meaning. Automatic background moves and whole-home
scans are not enabled.

`/source` reads only an allowlist of HumanOS code/documentation, separately from
personal workspace files. It cannot read configuration, secrets, vaults or Git
internals. Mirror's capability answers come from the actual registry.

Failed requests now save a truthful final response and allow conversation to
continue. Capture success does not turn a failed operation into a successful one.
To close an older unfinished task without further tool execution:

```sh
python3 server.py --close-task TX-ID-FROM-STATUS
```

This is an administrative CLI control, not an in-conversation `/close` command.
It records failure closure and preserves original input, steps and uncertain
effects. It does not resolve an uncertain file mutation by itself.

Run the new real-model acceptance separately from the automated suite:

```sh
python3 verify_files_live.py
```

It uses temporary synthetic files and a separate Notebook, including simulated
human approval input passed through the real approval/capture implementation.
Rollback code baseline for this milestone: `6f8656c`. Keep newer Notebook evidence;
the additive `file_plans` table must not be discarded by restoring an old vault.
