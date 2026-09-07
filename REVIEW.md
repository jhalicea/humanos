# Durable permissions and delivery recovery

## Problem and scope

Before this change (`2cf2c98`), CLI resume bypassed the current-input authorization
callback and inherited permissive workspace reads. Saved answers could be omitted
from startup recovery while entering model history before confirmed output. Clock
and Notebook queries used a separate authorization path from model file tools.

This milestone extends the existing runtime: one capability contract/executor,
durable per-task permission scope, and explicit output recovery. No internet tool,
Drive synchronization, new model backend, or competing record store is introduced.

## Acceptance evidence

Run `python3 -m unittest discover -s tests -v` at the exact commit under review.
The suite includes:

- Restart with no original callback: a newly requested out-of-scope file is denied,
  while the originally authorized file succeeds.
- Atomic authorization state and audit commit; persisted denial survives restart.
- Unknown/unavailable tools, extra session arguments, altered permission scope,
  and explicit negative file requests fail closed.
- Process death after file creation: resume stops with unknown outcome and leaves
  the artifact untouched, without another model/tool execution.
- Process death during output: resume emits only the saved exact final, retains
  two primary transcript entries, and closes output recovery.
- Partial write, flush failure, missing legacy delivery metadata, additive schema
  migration, idempotent recovery, and omitted undelivered assistant history.

`python3 verify_durable_live.py` separately exercises the configured local Ollama
backend with synthetic data. Initial implementation testing passed four turns and
hit the iteration bound on the file turn. A diagnostic repeat reproduced nested
`parameters` output rejected by the flat tool schema. The model instructions now
generate valid flat request examples from the registry. Keep these initial failures
distinct from the final commit's recorded local and CI results; refer to the pull
request for exact runs.

## Review focus and limits

Review the same immutable commit in each external reviewer. Ask for reproducible
findings, file/line references, severity, and a suggested regression case. Treat
model reviews as analysis; verify findings with code and tests. Do not include
private vaults or credentials in review attachments.

The phrase recognizer remains a convenience for ordinary clock/Notebook questions;
it now produces requests for the shared executor. File request parsing is narrow
and may reject complex phrasing. A saved callback cannot grant broader read scope.
The host controls code and storage; this is not protection against a malicious
process that can rewrite the local database and recompute its audit chain.

The terminal has no transactional acknowledgement protocol: after a crash between
flush and confirmation, output may repeat on an explicit retry. Tool effects and
primary transcript entries are not repeated. Unknown interrupted writes and legacy
unfinished tasks lacking scope require manual reconciliation. No automatic merge
of Notebook pages or canonical Drive capture is claimed.

## Rollback

Code baseline: `2cf2c98` on `runtime-0.1`, before this milestone. Preserve the
private vault before installation. The added recovery.scope column is compatible
with existing stored rows; old code ignores the new output-recovery semantics.
Revert the code change through Git while retaining new Notebook evidence. Do not
restore an old database over newer conversation records. Re-test isolated state
before resuming the owner's live session.
