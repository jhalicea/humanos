# HumanOS React Build Ladder — Mirror Control Room

Status: **ACTIVE CANDIDATE BUILD PLAN** on `feature/adaptive-learning-academy-v1`

## Architectural decision

React is appropriate for the **human-facing Mirror / Control Room UI**. It is not the HumanOS operating core.

Keep these authoritative responsibilities in the local Python runtime:

- Life Notebook persistence and transcript integrity
- audit/event ledger and provenance
- recovery and uncertain-operation handling
- capability registry and permission validation
- model/provider adapters
- tool execution and approval enforcement
- encryption, backup, restore, and verification
- canonical state transitions

React is a client/presentation layer. It may request actions through a narrow local API boundary, display state, collect human approvals, and visualize evidence. It must never become the source of truth for permissions, ledger state, recovery state, or canonical Notebook data.

Current Runtime 0.1 remains Python/local-first and CLI-first. The web UI is an additive interface, not a rewrite.

## Proposed local architecture

```text
Human
  ↓
React Mirror / Control Room
  ↓
Narrow local HumanOS API boundary
  ↓
Existing Python Runtime 0.1 services
  ├── Notebook
  ├── Audit / Integrity
  ├── Recovery
  ├── Capability Registry
  ├── Work Executor
  └── Model Adapter(s)
```

The exact HTTP/API implementation remains a separate implementation decision. Do not add FastAPI, Flask, WebSockets, or another dependency merely because React needs a backend. First define the smallest read-only contract and choose the least-complex safe adapter.

## Build ladder

### HUI-01 — Runtime Status Panel

**First production-adjacent React slice. Read-only.**

Display:

- runtime up/down state
- current model/provider
- active session / HCID
- unfinished transactions
- recovery-required state
- test/build version metadata when available

Learning coverage:

- React components
- props/state
- fetch/async/await
- loading/error/empty states
- TypeScript introduction later
- HTTP status/error handling

Security rule: no mutation controls yet.

### HUI-02 — Life Notebook Explorer

Read-only browser for HumanOS Notebook projections.

Display:

- pages/conversations
- chronological USER / ASSISTANT turns
- transaction IDs
- captured timestamps
- integrity/verification status
- recovery markers
- transcript search/filtering

Learning coverage:

- routing
- nested views
- dynamic route parameters
- data fetching
- pagination
- accessible tables/lists

Canonical Notebook storage remains Python/SQLite/local files. React only renders returned views.

### HUI-03 — Transaction & Recovery Inspector

Visualize one turn end-to-end:

`request → authorization/scope → model/tool calls → persisted state → output → recovery state`

Display:

- transaction state machine
- tool attempts
- failures
- uncertain outcomes
- readback verification
- explicit resume eligibility

Learning coverage:

- state machines
- conditional UI
- error boundaries
- failure diagnosis
- observability concepts

Initially read-only. Resume/reconcile actions require a separate approval-gated implementation slice.

### HUI-04 — Capability Registry

Show what HumanOS can currently do and why.

Display:

- capability/tool name
- allowed arguments
- scope restrictions
- approval requirement
- current availability
- provenance/version

Later add explicit approval UI for permitted actions.

Learning coverage:

- forms
- validation
- authorization UX
- 401 vs 403 semantics
- secure API design

The React client must never decide authorization; the Python runtime re-validates every request.

### HUI-05 — Human Approval Center

A queue for actions that require Jon's approval.

Examples:

- file creation/update
- external actions
- consequential workflow steps
- recovery decisions
- model/provider changes

Requirements:

- exact action preview
- scope and consequence display
- approve / reject
- idempotency protection
- audit receipt
- safe retry behavior

This becomes a major authentication/authorization/failure-handling lab.

### HUI-06 — Model & Usage Observatory

Display per-provider/model evidence:

- provider
- model/version when exposed
- task/role
- latency
- exact token/cost values when exposed
- ESTIMATED token values when unavailable
- corrections/quality notes
- repository/test evidence links

Learning coverage:

- charts/tables
- aggregation
- API contracts
- provenance
- observability

### HUI-07 — Adaptive Learning Academy

Turn the current curriculum/mastery system into a real interface.

Display:

- courses
- skill graph
- SEEN → INTRODUCED → ASSISTED → PRACTICED → DEMONSTRATED → MASTERED
- Knowledge / Practical / Diagnostic / Communication scores
- historical evidence vs current mastery
- labs tied to HumanOS/Atlas/BodyFix work
- one active learning slice and one next action

This is an excellent React feature because it is highly interactive but does not need to own canonical runtime authority.

### HUI-08 — Inbox / Attention Center

HumanOS's future inbox control surface.

Display normalized items from connected sources such as email, calendar, alerts, work queues, and HumanOS internal events.

Functions may eventually include:

- importance classification
- threads / grouped events
- unread/requires-action states
- defer/snooze
- human-approved reply/action flows
- provenance showing why HumanOS surfaced the item

This should be built after the local UI/API/auth/recovery foundations are proven. External account actions remain approval-gated and connector-specific.

### HUI-09 — Work / Automation Control Room

Display:

- running/completed/failed jobs
- automation schedules
- conditional watches
- human approvals
- retries
- external effects
- rollback/recovery state

This becomes the interface for n8n/Make-style concepts while preserving HumanOS governance above the automation engine.

### HUI-10 — Browser / Research Control Surface

Expose approved browser-bridge status and research artifacts without allowing unrestricted browser control from the frontend.

Learning coverage:

- event streams
- browser extension boundaries
- service workers
- tool contracts
- cross-origin/security considerations

## Build order

Do not build all of these at once.

Recommended order:

`HUI-01 Runtime Status → HUI-02 Notebook Explorer → HUI-03 Transaction/Recovery Inspector → HUI-04 Capability Registry → HUI-05 Approval Center → HUI-06 Usage Observatory → HUI-07 Learning Academy → HUI-08 Inbox → HUI-09 Automation Control Room → HUI-10 Browser/Research`

Each slice must pass:

1. DEFINE outcome/scope/security boundary.
2. BASELINE current runtime/tests.
3. Build the smallest reversible UI/API contract.
4. Test normal, failure, restart/recovery, duplication/idempotency, security and regression behavior.
5. Verify runtime readback; frontend display is not authoritative evidence.
6. Preserve one next action.

## React stack direction

Candidate frontend direction:

- React 19.x
- modern function components/hooks
- React Router current line when routing is needed
- Vite for a lightweight local SPA unless a framework requirement emerges
- TypeScript after the JavaScript/React reactivation diagnostic
- behavior-focused component/integration testing

Avoid recreating the old stack merely for nostalgia:

- no new Create React App project
- no new Enzyme dependency
- no assumption that Webpack must be configured manually
- no React state as canonical HumanOS state

## Vercel decision

Vercel is **current and relevant**, but it is a deployment platform rather than a core HumanOS technology.

### Good HumanOS-adjacent uses

- public HumanOS documentation site
- sanitized public demo UI
- jonalicea.com / jhalicea.com
- portfolio/project pages
- preview deployments for non-sensitive frontend branches
- public educational demos from the React reactivation course

### Do not use Vercel for

- canonical Life Notebook data
- private local HumanOS runtime
- credentials/secrets
- unrestricted Mirror state
- private audit/recovery data
- local model/tool authority

A production public HumanOS service may eventually use cloud infrastructure, but that requires an explicit remote-provider/privacy/security design. Vercel must not silently turn a local-first control plane into a cloud-hosted one.

## First React implementation decision

Do **not** build HUI-01 during Session 1.

Session 1 is a read-only diagnostic using the historical Noteful repository. Once the diagnostic reveals Jon's current React/npm/Router level, choose the smallest HUI-01 implementation slice and the minimum API contract needed to expose runtime status safely.
