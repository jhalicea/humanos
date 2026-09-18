# HOS-CTX-006 — Local Temporal Context Boundary

Status: REVIEW  
Branch: `feature/context-local-time-v1`  
Workspace: `WS-HUMANOS`  
Parent: extends promoted `HOS-CTX-005`  
Baseline: `runtime-0.1` at `2e4bd3056e1f0c489b33fabbc1b6c0c3f0d25ea9`

## Relationship classification

**EXTEND as a new bounded Context Engine workstream.**

CTX-005 established deterministic temporal relevance using canonical UTC Notebook evidence. CTX-006 separates evidence time from human meaning by projecting canonical timestamps into an explicitly supplied IANA timezone.

## Outcome

- Notebook evidence remains canonical and unchanged.
- Temporal interpretation accepts an explicit IANA timezone.
- Historical record timestamps are projected to local calendar dates only for relevance filtering.
- Default remains UTC for backward compatibility.
- Invalid/unavailable timezone input fails safely to UTC rather than guessing a location.

## Security / authority invariants

No geolocation lookup, IP inference, model timezone inference, embeddings, replay, branch switching, tool permission, or expanded authority. Timezone is an explicit runtime context input in this slice; wiring a trusted owner/workspace timezone source is deliberately separate.

## Acceptance criteria

1. A UTC timestamp crossing a local midnight boundary maps to the correct local date.
2. Invalid timezone names fail safely to UTC.
3. Existing CTX-005 behavior remains backward compatible with default UTC.
4. Existing full regression and encrypted-backup matrices pass.
5. Promotion remains owner-gated.

## Deliberate boundary

This slice creates the timezone-safe primitive only. It does not yet decide where Mirror obtains the trusted active timezone. That source must follow workspace/owner context and privacy rules rather than silently using device/IP/model inference.
