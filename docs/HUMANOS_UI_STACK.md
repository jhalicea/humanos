# HumanOS UI Stack Decision — Local First

Status: **ACTIVE CANDIDATE ARCHITECTURE** on `feature/adaptive-learning-academy-v1`

## Decision

HumanOS does **not** adopt React as a default architectural dependency.

React remains part of Jon's web-engineering reactivation curriculum because it is useful prior knowledge and still relevant in the market, but HumanOS should use the simplest stack that preserves local-first operation, auditability, portability, and failure isolation.

## Preferred stack

### Core runtime

- **Python** — authoritative runtime and application logic
- **SQLite** — authoritative local transactional state where appropriate
- explicit file artifacts for human-readable/exportable records where already part of the HumanOS design
- existing audit, integrity, recovery, capability and model boundaries remain authoritative

### Local interface boundary

- **FastAPI** only when HumanOS needs a stable local HTTP/API surface
- bind to loopback/local interfaces by default
- keep API adapters thin; the API must call existing domain/runtime services rather than re-implement authority rules
- use typed request/response schemas and explicit error/status contracts

FastAPI is an adapter, not the HumanOS core. HumanOS domain logic should remain usable without starting the web server.

### Human-facing UI

Default:

- server-rendered HTML templates
- **HTMX** for partial updates, forms, polling/SSE/WebSocket-style interactions where justified
- small, explicit **vanilla JavaScript** modules only where browser-side behavior is genuinely needed
- local static assets; do not require a public CDN for normal operation
- CSS kept simple and owned by HumanOS; avoid a large component framework until there is a concrete need

This approach minimizes duplicated client state and avoids requiring React, Redux, a Node build pipeline, or a second application architecture merely to expose HumanOS controls.

### Optional future desktop shell

A browser on `localhost` is the preferred first interface because it is transparent and easy to debug.

If HumanOS later needs a packaged native desktop application, evaluate **Tauri 2** as a shell around the local UI. Do not introduce Rust/Tauri until packaging, tray integration, native notifications, auto-start, or OS-level desktop integration provide real user value.

The desktop shell must not move canonical HumanOS authority into the frontend.

## Proposed architecture

```text
Human
  ↓
Local browser UI
HTML + HTMX + small vanilla JS
  ↓
Thin local HTTP adapter (FastAPI when needed)
  ↓
Existing HumanOS Python domain/runtime
  ├── Mirror / interaction services
  ├── Life Notebook
  ├── Audit / integrity
  ├── Recovery
  ├── Capability registry
  ├── Work executor
  └── Model/provider adapters
  ↓
SQLite + governed local files
```

## Why this stack

### Local-first

The system works on the user's computer without requiring a hosted frontend or cloud database. SQLite is a disk-based database that does not require a separate server process, fitting the current HumanOS runtime model.

### Fewer moving parts

A React SPA would introduce client routing, client-side state synchronization, Node/npm build tooling, dependency updates, hydration/rendering decisions, and another failure surface. HumanOS does not currently need those costs.

### Inspectable

HTML responses, HTTP requests, SQLite state, Python services and explicit audit events are easy to inspect independently. This matters for HumanOS's evidence and recovery goals.

### Failure isolation

The UI can fail without becoming authoritative. Permission checks, recovery decisions and canonical state remain in Python.

### Portable

The Python/domain layer can later be exposed through a web UI, CLI, desktop shell, mobile client, external API or another model interface without rewriting the HumanOS core.

## Build ladder

### HUI-01 — Local Status Page

Read-only page showing:

- runtime state
- current model/provider
- current session/HCID
- incomplete transactions
- recovery-required state
- test/build/version information

Teaching value: HTML, HTTP, FastAPI routing, templates, HTMX refresh/polling, explicit loading/error states.

### HUI-02 — Life Notebook Explorer

Read-only views for:

- conversations/pages
- USER / ASSISTANT chronology
- transaction IDs and timestamps
- verification/integrity state
- recovery markers
- search/filter/pagination

Teaching value: URLs, route parameters, queries, templates, database reads, HTTP errors, progressive enhancement.

### HUI-03 — Transaction & Recovery Inspector

Visualize:

`request → scope → model/tool execution → persistence → final output → recovery state`

Initially read-only. Later recovery/resume actions must pass the existing runtime authority/approval layer.

### HUI-04 — Capability & Approval Center

Display capabilities, argument boundaries, scopes and approval requirements. Later provide approval/rejection forms.

The browser is never trusted to authorize an action; Python validates again server-side.

### HUI-05 — Model / Usage Observatory

Present model/provider/version, task role, latency, token/cost evidence, test evidence and quality/correction notes.

### HUI-06 — Adaptive Learning Academy

Expose courses, skill graph, evidence, four grading dimensions, historical exposure versus current mastery, labs and next action.

### HUI-07 — Inbox / Attention Center

Expose normalized email/calendar/alert/work items, importance, required action, provenance, defer/snooze and later human-approved actions.

### HUI-08 — Automation / Research Control Room

Expose n8n/Make workflows, browser/research tasks, run state, failures, retries, evidence and approvals when those subsystems are mature.

## React policy

Use React in HumanOS only if a specific future surface demonstrates that server-rendered HTML + HTMX + small JavaScript is materially inadequate—for example, an unusually complex visual editor or highly interactive canvas-like application.

If that happens, React may be introduced for that bounded surface without becoming the HumanOS core UI architecture.

## Deployment policy

The authoritative HumanOS application remains local-first.

Cloud platforms such as Vercel may be used for:

- public documentation
- sanitized demos
- portfolio/personal sites
- non-sensitive public interfaces

Do not deploy the canonical Life Notebook, private audit data, credentials, permissions, local model authority, or private HumanOS control plane to Vercel merely for convenience.

## Dependency rule

Add FastAPI, HTMX, Tauri or any other dependency only when the next selected HumanOS slice needs it. Do not pre-install or pre-architect unused components.
