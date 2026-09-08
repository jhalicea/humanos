# File organization and truthful failure recovery

Baseline: `6f8656c` (private HumanOS repository, `runtime-0.1`). The existing
Notebook, model adapter, command-line interface and capability registry are extended.

The observed conversation denied file-reading capabilities, attempted to read
HumanOS source from the personal workspace, then exhausted its iteration budget.
The new source adapter reads allowlisted runtime code. Capability questions use
the actual registry. Failed turns preserve a final response and permit continued
conversation. File scans, duplicate reports and approved reversible move plans
use the existing executor, task policy and private Notebook database.

## Review and reproduction

Run `python3 -m unittest discover -s tests -v` at the immutable commit under review.
Run `python3 verify_files_live.py` separately for the installed local Ollama model.
The latter never uses personal files or the owner's active Notebook.

Review found and corrected: natural-language folder scope widening; hashing budgets
reset per file; unbounded directory enumeration; stale task state overwriting a
durable failure closure after readback failure; runtime source substitution for
qualified workspace paths. Regression tests reproduce these cases. Native rename
rechecks the pinned source identity and refuses destination overwrite. Interrupted
rename tests prove explicit recovery does not repeat a completed move.

Only command-line `--close-task` is supplied for explicit administrative closure;
the proposed interactive close control was removed because it omitted its human
input from the primary transcript. All supported conversation commands follow
the normal exact-input capture path.

## Remaining limits

- UTF-8 text content only; no PDF/Office extraction, internet or Drive connection.
- Duplicate reports use complete cryptographic hashes and sizes, not fuzzy or
  semantic similarity; duplicate files are never deleted.
- Undo leaves newly created empty folders. Changed items fail closed.
- Each rename is atomic with no overwrite; multiple moves are not one filesystem
  transaction. External concurrent changes in the final validation/rename window
  remain possible. Post-verification records uncertainty; do not edit the tree
  concurrently during a plan.
- Hashes/audit protect against accidental changes, not a hostile process with
  permission to rewrite the database and recompute its evidence.
- Natural-language path recognition is narrow; exact slash commands are supported.
- Local capture/readback and output-stream delivery do not prove human receipt or
  capture of this external Codex conversation.

## Release and rollback

Keep the owner's active files, Notebook, test evidence and backups out of Git.
Before installing, preserve the existing code commit and private vault backup.
Roll back code through Git to `6f8656c`, retaining newer Notebook evidence. The
added file-plan table is ignored by earlier code; earlier code lacks these tools.
The pull request records the exact tested head and remote CI results. The owner
will arrange Claude/Gemini review; no code is sent to those services by this build.
