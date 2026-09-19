# HumanOS Status Snapshot

Status: HOS-BROWSER-001 PROMOTED / LOCAL PAIRING PENDING
Date: 2026-09-19
Workspace: `WS-HUMANOS`
Workstream: `HOS-BROWSER-001 — Browser Broker and Tools`
Branch: `feature/browser-activation-v1`
Baseline: `runtime-0.1@b45f4eb94be026660ed3415f3213d132bda7955d`
Verified implementation: `b1ceadb7fe2d0165b98cce2f8463e932f72049c3`
Promotion commit: `02869089cd336ffac17751a771bd61adcf21229d`
Promotion PR: #91
Global router/index: GitHub issue #67
Work order: `docs/work-orders/HOS-BROWSER-001.md`

## Outcome

Continue the existing Browser Broker workstream and make the already-merged browser
capability operably installable/configurable for local Mirror without weakening owner
authority or browser safety boundaries.

The slice adds owner-only local setup, stable unpacked-extension identity,
`nativeMessaging`, native-host launcher/manifest generation, runtime discovery,
governed browser search, selected-tab sentinel handling, exact task-scope/approval
gates, extension-failure propagation, tests, and updated operating documentation.

## Responsibility boundaries

- Owner: implementation/promotion authority and unavoidable browser UI extension load/tab selection.
- Context Router: routes WS-HUMANOS -> HOS-BROWSER-001; grants no execution authority.
- Work Order/SDLC: bounds scope, tests, rollback, and evidence.
- Local setup: writes only HumanOS-owned pairing artifacts outside Git.
- BrowserBroker: host/capability/action/byte/time/HMAC/audit policy boundary.
- Native host: authenticated transport only.
- Extension: selected-tab executor only.
- Mirror/model: requests only runtime-ready registered tools.
- Runtime approval gate: exact effectful browser approval.
- CI: evidence, never authority.

## Verification evidence

- Regression workflow `35454724814`: SUCCESS on Ubuntu 24.04/macOS 15 × Python 3.11/3.13.
- Representative regression suite: 528 tests, 8 skipped, no failures.
- Encrypted-backup/full-suite workflow `35454724812`: SUCCESS.
- Exact implementation diff reviewed; no local owner paths, Notebook content, credentials, or secret bytes found.
- Current Chrome native-messaging constraints cross-checked against official Chrome documentation.
- Real browser end-to-end connectivity is not yet claimed; it requires local post-promotion pairing/readback on Jon's Mac.

## Rollback

Revert the eventual promotion commit or reset to canonical baseline
`b45f4eb94be026660ed3415f3213d132bda7955d`.
No Life Notebook migration is part of this slice. Local uninstall removes only
HumanOS-owned browser pairing artifacts.

## Next action

Repository promotion is complete. On the owner Mac: pull `runtime-0.1`, run `humanos --browser-setup`, load
`browser-extension/` once as an unpacked extension, click the extension on the
selected tab, run `humanos --browser-status`, and execute one bounded browser test.
