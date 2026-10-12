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
one-turn Codex JSONL rollout and owner-only destination directories:

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

**Limitations:** This does not verify host provenance independently of the
selected file, perform provider-side completeness attestation, protect a
compromised operating system, support automatic/multi-turn bulk rollout import,
prove provider-defined turn completeness, or silently capture any provider. An import error after ledger append can preserve
ledger evidence without having completed Notebook projection; rerun only with
the same selected source and review the recovery evidence. Neither local owner
installation nor private-vault restoration is qualified by repository CI.

## Documentation policy

Specifications and roadmaps describe intended work. They must not be presented as implemented or verified until corresponding code and evidence exist.
