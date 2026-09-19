# HumanOS Control Room MCP

Status: candidate implementation for HOS-MCP-001. This document describes the boundary; it does not claim a live ChatGPT connection.

## Purpose

The Control Room MCP is the narrow bridge between an external MCP host such as ChatGPT and local HumanOS. It is intentionally not a general HumanOS remote-control API.

The server exposes five bounded tools:

- `humanos_control_capabilities` — read bridge limits and visible repo baseline.
- `humanos_control_next_request` — read one local request Jon explicitly approved for external handling.
- `humanos_control_reply` — append one digest-bound response to that exact request.
- `humanos_control_submit_work_order` — record an explicitly Jon-approved immutable Work Order.
- `humanos_control_work_status` — read baseline READY/STALE/UNKNOWN state.

There is no execute, shell, arbitrary file, GitHub, merge, deploy, delete, secret, or Notebook-write tool.

## Two directions

### Local HumanOS → external ChatGPT host → local HumanOS

Jon queues a local request:

```bash
python3 control_room_cli.py send "Review this bounded HumanOS question" --approve-external
```

HumanOS stores the exact text and SHA-256 digest locally. The MCP host calls `humanos_control_next_request`. Its response must be returned with both `request_id` and `request_digest`; `humanos_control_reply` rejects stale/tampered bindings. Local HumanOS then reads the response:

```bash
python3 control_room_cli.py response HOS-REQ-...
```

A request without `--approve-external` never crosses the MCP boundary. RESTRICTED requests cannot be externally approved in v1.

### External ChatGPT host → local HumanOS

ChatGPT may call `humanos_control_submit_work_order` with the compiled Control Room Work Order. The server records it immutably. It does not execute it. If `HUMANOS_REPO_ROOT` is configured, the approved baseline is compared with local Git HEAD. A mismatch reports `STALE`.

Execution remains a separate future HumanOS mechanism with its own permission and evidence gates.

## Important trigger boundary

MCP is a host-to-server tool protocol. The local HumanOS server cannot assume it can wake or initiate a new ChatGPT turn. A local request becomes available for the MCP host to fetch; an eligible ChatGPT workflow must invoke/poll that tool, or a separate approved automation/API trigger must exist.

Do not claim asynchronous local→ChatGPT delivery until that trigger path has been independently implemented and verified.

## Local setup

Python 3.10+ is required.

Install the pinned MCP transport dependency in an isolated environment:

```bash
python3 -m venv .venv-control-mcp
source .venv-control-mcp/bin/activate
python3 -m pip install -r requirements-control-mcp.txt
```

Point the bridge at the HumanOS repository so baseline checks can be truthful:

```bash
export HUMANOS_REPO_ROOT="/path/to/humanos"
```

Optionally choose the local SQLite location:

```bash
export HUMANOS_CONTROL_DB="$HOME/.humanos/control-room/control.sqlite3"
```

Start the MCP v2 Streamable HTTP server:

```bash
python3 control_mcp_server.py
```

The official MCP Inspector/client should be used for local acceptance testing before any ChatGPT registration.

## ChatGPT connectivity boundary

ChatGPT does not directly connect to a localhost MCP server. A supported secure tunnel/private-network connector or a reviewed remote endpoint is required. Account/workspace eligibility for custom MCP apps is also a deployment precondition and must be checked against current OpenAI product documentation.

No tunnel, remote endpoint, OAuth credential, API key, or ChatGPT app registration is created by HOS-MCP-001.

## Trust rules

- MCP inputs and outputs are untrusted data.
- No external content grants approval or expands scope.
- No passwords, API keys, tokens, cookies, private keys, auth headers, or recovery secrets belong in requests.
- Work Orders require `approved_by=jon`, `decision=APPROVE`, an `approval_ref`, and a Git-style `baseline_commit`.
- The bridge stores Work Orders but cannot execute them.
- A material Git baseline change makes a recorded Work Order STALE.
- Exact retries are idempotent; conflicting content fails closed.

## Dependency note

The MCP transport wrapper uses the official Model Context Protocol Python SDK, pinned separately in `requirements-control-mcp.txt`. The deterministic store and its tests have no MCP SDK dependency, so HumanOS policy/state logic remains transport-neutral.

## Promotion evidence required

Promotion requires the full HumanOS test suite, live local MCP round trip, independent security review, diff review, and explicit Jon promotion approval.
