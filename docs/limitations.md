# Limitations

HumanOS is an active early-stage project. The current public repository should not be interpreted as a finished consumer product.

## Runtime 0.1 limitations

- Local Ollama inference only
- Terminal interface rather than a finished desktop application
- Narrow governed file capabilities, not arbitrary shell access
- No claim of complete operating-system isolation
- No automatic capture of external ChatGPT or Codex conversations
- No general remote-provider policy or hosted-model bridge
- No proof that output was read by a human
- No complete multi-device merge, provider migration, or conflict-resolution interface
- No guarantee against an attacker who fully controls the host

## Opt-in one-turn Codex import (PR #115 candidate)

PR #115 proposes one **manual**, owner-confirmed capture path reusing the existing
`capture_current_conversation.py`, ledger, and Life Notebook projector. It is
**not on canonical runtime-0.1** and is not automatic account or browser capture.

From the repository working directory with an explicitly chosen **local**
Codex JSONL rollout and owner-only destination directories. First view only
the source message references and roles (the inspection prints **no message content**):

```text
python3 humanos.py inspect-codex --source /absolute/private/path/selected-rollout.jsonl
```

This preview is `UNVERIFIED_METADATA_ONLY`: it does **not** certify that
adjacent messages are a complete provider turn. When Codex omits original
message IDs, it shows deterministic `local-record-v1:<sha256>` references
labeled `LOCAL_DERIVED_RECORD_V1` (not provider IDs). These bind the session,
source record line, and canonical original record; changing the source may
invalidate the reference. They are fingerprints, **not anonymization or
provider authenticity proofs**. Select one consecutive HUMAN/ASSISTANT pair
by its displayed references before importing a larger session.

Then import that one turn:

```text
python3 humanos.py import-codex \
  --source /absolute/private/path/selected-rollout.jsonl \
  --ledger /absolute/private/path/capture/ledger.jsonl \
  --notebook /absolute/private/path/notebook \
  --confirm-observed
```

This rejects files inside the repository, shared destination directories, missing
confirmation, ambiguous/multiple source turns or sessions, unrecognized message
evidence, and destination ledgers containing another session/provider. It accepts one bounded selected Codex session, and imports **one** complete
HUMAN/ASSISTANT pair. For longer rollouts you must specify the two *original*
IDs from one consecutive pair; for example add `--human-source-id human-2
--assistant-source-id assistant-2`. The selected source file has a 16 MiB
upper size limit. It is idempotent for an exact previously imported turn.
The command emits aggregate verification status, not transcript text.
The selected source is parsed into one bounded immutable in-memory snapshot,
which is reused for preflight and ledger append. This prevents mixing different
revisions of the source between selection and capture but does not authenticate
the source provider or prevent concurrent changes to the source file itself.

**Limitations:** This does not verify host provenance independently of the
selected file, perform provider-side completeness attestation, protect a
compromised operating system, support automatic/multi-turn bulk rollout import,
prove provider-defined turn completeness, or silently capture any provider. An import error after ledger append can preserve
ledger evidence without having completed Notebook projection; rerun only with
the same selected source and review the recovery evidence. Neither local owner
installation nor private-vault restoration is qualified by repository CI.

## Documentation policy

Specifications and roadmaps describe intended work. They must not be presented as implemented or verified until corresponding code and evidence exist.

## PR #128 candidate: concurrent ledger writer and private file policy

An isolated follow-up proposes an exclusive advisory writer lock using a
persistent `<ledger>.writer.lock` sidecar. Existing ledger import, observed-turn,
observed-message, and metadata-correction append routes all use the same lock
around source-identity read, duplicate check, and append. The lock inode is
not unlinked after release to avoid splitting competing writers between files.
Synthetic cross-process tests deliberately queue two imports simultaneously
and require one append and one idempotent skip.

The ledger and lock files are created with mode **0600** regardless of umask;
existing group- or other-readable ledger/lock files fail closed instead of
silently changing their permissions or appending private evidence. Existing
owners should review and remediate historical permissions separately.

Capture receipts are additionally written through a bounded, owner-private (0600)
append with an exclusive receipt-file lock. Both successful and failed receipts
omit the selected source's absolute path; failures record a generic
`capture_failed` reason rather than an exception string that might include
user-controlled message identifiers or transcript fragments. Existing exposed
receipt files and symlinks are refused before ledger mutation. Historical
receipts are neither rewritten nor silently migrated.

**Not yet covered:** direct file edits by non-cooperating processes, crash-safe
multi-row appends, atomic ledger/receipt cross-file commits and checkpoint verification, unrestricted
filesystem adversaries, or end-to-end ledger/receipt/Notebook transactions.
The shared ledger and any future receipt operation still require owner-host
acceptance, independent review and explicit promotion approval. This is a
candidate, not part of canonical `runtime-0.1`.

## PR #129 candidate: interruption and recovery qualification

Synthetic subprocess fault injection at three boundaries: abrupt process exit
after ledger+receipt append but before Notebook projection; abrupt exit after
Notebook checkpoint but before CLI result; and abrupt exit after Notebook
HUMAN transaction STARTED but before ASSISTANT append/checkpoint.

- First boundary: the original ledger is durable and a replay should project
  the selected pair exactly once. A ledger-only receipt can still report
  CHECKPOINTED while the Notebook is absent; never interpret this status as
  successful Notebook recovery.
- Second boundary: an already checkpointed pair is verified and skipped on
  replay, preserving ledger bytes and original Notebook transcript.
- Third boundary: partially created Notebook evidence is preserved and
  automatic re-import fails closed; this case **requires manual reconciliation**
  under owner approval. Do not silently overwrite or pretend to automatically
  recover every interruption.

Tests use only generated synthetic fixtures in private temporary directories.
They do not use owner conversation data, real Codex sessions, or owner vaults.
No new recovery subsystem is introduced. Testing these three transitions does
not establish crash-safe atomicity of physical ledger, receipt, and SQLite
writes, nor full backup/restore guarantees. This is a candidate stacked on
PR #128, not canonical or owner-host accepted until separately qualified.
