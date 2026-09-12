# Security and Privacy

HumanOS is designed around data minimization, explicit authorization, local-first execution, and evidence that can be inspected after failure.

## Current controls

- Dedicated workspace boundary for authorized files
- Rejection of traversal, hidden paths, symlinks, hard links, and device files in governed file operations
- Explicit approval for file creation and no silent overwrite
- Persisted request scope used during recovery
- Single-writer coordination for durable state
- Integrity verification for transcripts and projections
- Remote endpoints rejected until a remote-provider policy exists

## Important distinction

Integrity hashes detect accidental alteration and some forms of corruption. They do not protect against an attacker who controls the host, database, and integrity keys. HumanOS is not presented as a hardened multi-user security boundary.

## Never commit

- Notebook payloads or personal transcripts
- Credentials, tokens, API keys, or encryption secrets
- Private client, medical, financial, or identity information
- Real local paths that reveal unnecessary personal information
- Unredacted model-provider exports or audit records

Security claims must remain proportional to verified controls and documented threat assumptions.
