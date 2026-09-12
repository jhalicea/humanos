# Life Notebook

The Life Notebook is HumanOS's continuity layer. It preserves what was actually said and what the runtime actually did without replacing the primary record with a generated summary.

## Runtime 0.1 behavior

- Exact chronological transcript capture
- Durable session and transaction identities
- Append-only events and recovery entries
- Human-readable projections derived from authoritative local state
- Explicit distinction between prepared, uncertain, and emitted output states
- Startup reconciliation for incomplete work

## Evidence rules

The Notebook does not invent missing assistant responses or claim that output was received by a human. Operational diagnostics remain separate from chat messages. Model proposals, tool outcomes, permissions, and errors belong in their appropriate audit records.

## Privacy boundary

Public documentation describes structure and behavior only. Real Life Notebook content remains private and local unless the owner deliberately exports a specific record.
