# Authorized swarm broker

`AUTHORIZED_RED_TEAM_SWARM` is an opt-in runtime profile. The default Mirror,
permissions, governance records, and Life Notebook retain their existing behavior.
The dedicated profile opens no Notebook and never calls the ordinary file executor.
It runs a concrete JSON tool broker, not a model coordinator or exploit framework.

## Trust boundary

The owner starts `python3 server.py --config /absolute/path/swarm.json` in a
separate process. Only trusted host code owns this process and config. Agents are
untrusted JSON producers: they receive observations and submit proposals. They
cannot load Python into the broker, obtain its objects, access files, execute
shell commands, or select tool implementations. The host must keep all tokens,
configuration and state outside model context and any agent-accessible workspace.
Use a dedicated owner-only directory (0700) and config (0600).

This is **not an OS sandbox for arbitrary agent programs**. Same-user native code,
a compromised owner, or root can bypass filesystem permissions, steal tokens, or
replace the ledger and its key/head together. Do not run arbitrary workers under
this account and call them contained. A separate OS identity/container/network
policy and authenticated worker launcher remain prerequisites for that extension.
No arbitrary-code workers are launched by this implementation.

## Configuration

The JSON config has exactly `profile`, `control_state`, `envelope`, `agents`.
`control_state` is an absolute canonical path to the external owner-only control
directory. Each run needs its own directory. Do not place it in a Notebook,
workspace, repository, or an agent-visible directory. No live run is configured
or authorized by installing this code.

The envelope contains:

- `run_id`: unique human-selected run identifier.
- `targets`: exact objects such as `{"ip":"127.0.0.1","port":8080}`. Only
  canonical numeric IPs and integer ports are accepted. No hostnames, CIDRs,
  redirects, proxy settings, or wildcard expansion.
- `authorization`: `human`, `reference`, `provenance_sha256` (64 hexadecimal
  characters), `owner_attested: true`, and `environment` (`owned_system`,
  `authorized_lab`, or `ctf`). The owner must inspect the referenced evidence
  and confirm permission for every target. Evidence is referenced, not imported
  into the Life Notebook; the broker does not independently establish ownership.
- `not_before`, `expires`: integer UTC Unix seconds, with a finite increasing window.
- `permitted_impact`: exactly `connect_only`.
- `stop_conditions`: all of `ambiguous_scope`, `unexpected_privilege`,
  `high_impact`, `scope_escape`, `operator_stop`.
- `max_actions`: 1–100000 attempted actions, including denied requests.
- `max_message_bytes`: 0–10000000 cumulative submitted message bytes.

Each agent manifest has exactly `agent_id`, `model`, `version`, `task`,
`capabilities`, `peers`, and `token`. Generate a unique secret token with at least
32 characters using a cryptographically secure generator. Model/version/task are
trusted host registrations, not values accepted from proposals and not remotely
attested model identities. The host must ensure each model receives only its
own observations; tokens stay in trusted transport code, outside prompts.

Capabilities are a subset of `tcp_probe`, `send_message`, `receive_messages`.
`peers` declares directed send routes to registered agent IDs. Undeclared routes
are denied. There are no direct peer, general file, arbitrary network, or
credential-management tools.

## Broker protocol and actual tools

Supply one JSON line at a time through stdin:

```json
{"token":"HOST_INJECTS_AGENT_TOKEN","request":{"tool":"tcp_probe","arguments":{"ip":"127.0.0.1","port":8080}}}
```

The fixed TCP tool opens one numeric destination, sends no application data,
reads no application data, uses no DNS/proxy/redirect, and closes the socket.
It returns `connected` and `error_code`. A successful connection establishes
reachability only; it is not a vulnerability finding. The socket timeout is at
most one second and is bounded by the remaining authorization window.

`send_message` arguments are `peer` and text `message`; `receive_messages` takes
`{}` and drains that agent's inbox. Routing is mediated by the broker; content is
untrusted data. Mail is bounded by the byte budget and expires on restart.
Its historical delivery observations remain in the ledger. No replay is implied.

Any authenticated agent can submit `escalate` with `{"reason":"high_impact"}`
or another mandatory stop reason. Scope escape, malformed request shape,
unsupported tools, and explicit privilege/high-impact arguments trigger stop
gates before effects. Unsupported argument schemas otherwise deny execution.
These gates implement deterministic tool restrictions; they do not claim to
recognize every semantic risk in arbitrary natural-language observations.

## Stop, audit, recovery

Create `STOP` in the control directory to stop subsequent actions, or terminate
the broker process to abort it. Trusted host code can also call `stop()`.
A detected STOP file becomes a durable ledger stop event. A stop does not undo an
already initiated TCP connection; its socket timeout is at most one second.
Escalated/stopped runs have no model-accessible reset or approval override.
Inspect evidence and create a separately authorized run to proceed.

Every attempt is fsynced before dispatch and every result is recorded before
return. Attribution includes registered agent/model/version/task/capabilities,
human authorization, run ID, request, action ID and resulting observation.
The ledger is external JSONL with an HMAC chain and separately stored head.
Edits and truncation fail verification; only append is exposed to trusted runtime
code. File links, unsafe file modes, and concurrent broker ownership are rejected.
An incomplete attempt or persisted stop blocks execution after restart. Audit
write failures abort the stream; result-audit failure also poisons the live run.
A crash between ledger append and head update requires human reconciliation;
there is deliberately no automatic repair that could bless uncertain effects.
Keep the directory intact for investigation. Full rollback/replacement of all
trusted state requires an independent remote anchor to detect and is not solved.

Budgets survive restart. These are action/message budgets, not provider-token or
monetary budgets: no model provider or multi-agent scheduler is connected.
The profile does not synchronize Drive, amend governance, or promote findings
into canonical personal records. No exploit/payload, high-impact executor,
arbitrary worker sandbox, credential escalation, or automatic approval exists.

## Verification and rollback

Run `python3 -m unittest discover -s tests -v` from the repository. Tests use
isolated temporary state and a local loopback listener, never the owner's
Notebook or external targets. The new suite covers manifest/scope immutability,
capabilities, peer and egress denial, all stop reasons, budgets across restart,
audit corruption/truncation/failure, identity attribution and profile subprocess
integration. Existing Notebook behavior is covered by the full regression suite.

Rollback: return to the default config (which installation leaves unchanged).
After stopping any broker, revert the swarm commit if desired; preserve external
control state for evidence. Existing uncommitted work must not be reset.
