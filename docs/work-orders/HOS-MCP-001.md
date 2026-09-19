# HOS-MCP-001 — ChatGPT ↔ HumanOS Control Room MCP Boundary

Status: IMPLEMENTED CANDIDATE / NOT PROMOTED
Date: 2026-09-18
Workspace: WS-HUMANOS
Branch: `feature/control-room-mcp-v1`
Baseline: `runtime-0.1@2d4b383c6723177a3d1ad6ef3774d79dc8e6b7cd`
Risk: R3
Data class: INTERNAL

## Owner authorization

Jon explicitly authorized implementation of the HumanOS MCP control bridge in the current Control Room session on 2026-09-18. This authorization covers a bounded candidate branch only. It does not authorize merge, deployment, public exposure, new credentials, or production data egress.

## Objective

Create the first deterministic bridge between the ChatGPT Control Room protocol and local HumanOS so:

1. HumanOS can queue an exact owner-approved request for an external ChatGPT/MCP host.
2. The MCP host can read only requests explicitly approved for external handling.
3. A response is bound to the exact request digest and appended immutably.
4. ChatGPT can submit an explicitly Jon-approved Work Order to HumanOS without executing it.
5. Work Orders are bound to a Git baseline and become STALE when the local baseline differs.

## Scope

- `control_room.py`: transport-neutral append-oriented policy/mailbox store.
- `control_mcp_server.py`: narrow MCP v2 Streamable HTTP wrapper.
- `control_room_cli.py`: owner-local queue/read CLI.
- `tests/test_control_room.py`: approval, integrity, idempotency, and staleness tests.
- `docs/control-room-mcp.md`: operational boundary and setup.
- `requirements-control-mcp.txt`: pinned optional MCP SDK dependency.

## Non-goals

- No automatic work execution.
- No shell, GitHub, deployment, migration, browser, secret, or Notebook authority.
- No remote hosting or tunnel deployment in this slice.
- No claim that the current ChatGPT account is connected to this MCP.
- No merge to `runtime-0.1` without review and CI evidence.
- No reuse or merge of the stale `fix/capture-mcp-durable-proof` branch.

## Acceptance criteria

- Unapproved local requests are invisible to MCP.
- RESTRICTED requests cannot be approved for external egress.
- Request/response handoff is SHA-256 digest-bound.
- Exact duplicate responses are idempotent; conflicting responses fail closed.
- Work Orders require explicit Jon approval fields.
- Matching baseline reports READY; changed baseline reports STALE.
- Work Orders are immutable and are never executed by this MCP surface.
- Full repository regression remains green before promotion.

## Security boundary

All MCP-returned content is data, not authority. The bridge exposes no arbitrary file read, shell, credential, merge, deploy, or model-execution tool. Local request egress requires an explicit per-request `external_approved` bit. RESTRICTED data is denied external egress in this v1 slice.

The MCP wrapper may inspect only the configured repository HEAD through the fixed command `git -C <root> rev-parse HEAD`. No model-supplied shell arguments are accepted.

## Evidence so far

Before repository commit, the transport-neutral core was exercised in an isolated scratch directory with:

`python3 -m unittest discover -s tests -v`

Result: 8/8 focused tests passed.

`control_room.py`, `control_mcp_server.py`, and `control_room_cli.py` also passed Python syntax compilation in the isolated scratch environment.

These are pre-push checks, not full HumanOS regression or live MCP evidence.

## Rollback

Delete/revert the feature branch commits. The candidate creates no canonical Notebook migration and does not modify `runtime-0.1`.

## Promotion gate

Before merge:

1. Run full HumanOS CI/regression on the immutable candidate commit.
2. Run a real local MCP Inspector/client round trip.
3. Independently review the R3 trust boundary and tool surface.
4. Verify no secrets/private data were committed.
5. Jon reviews the actual diff and explicitly approves promotion.
