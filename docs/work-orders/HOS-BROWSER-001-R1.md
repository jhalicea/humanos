# HOS-BROWSER-001-R1 — Browser Activation Compatibility Correction

Status: PROMOTED / VERIFIED / LOCAL READBACK PENDING
Workspace: `WS-HUMANOS`
Workstream: `HOS-BROWSER-001 — Browser Broker and Tools`
Branch: `fix/browser-activation-r1`
Baseline: `runtime-0.1` at `856a41b7852e18f19b872e0f0b6f9367e65ee3d6`
Parent promotion: PR #91 / `02869089cd336ffac17751a771bd61adcf21229d`
Privacy class: INTERNAL

## Objective

Correct two post-promotion activation issues without reopening or redesigning the
promoted Browser Bridge:

1. preserve the meaning of already-saved permission scopes by assigning expanded
   web/browser intent to a new scope version instead of silently changing v4-v6;
2. install Brave/macOS native-messaging manifests in the current Chrome-compatible
   lookup location used by Brave, while keeping platform-specific validation testable.

## Routing

`CONTINUE HOS-BROWSER-001`.

This is a corrective slice inside the already-promoted Browser Broker workstream.
No new browser project/workstream is created.

## Scope

- Add task-scope version 7 for new browser-capable transactions.
- Keep versions 1-6 byte-for-byte semantically compatible for browser intent.
- Make browser-intent model tasks use v7 while unrelated new tasks keep their existing v4/v5/v6 selection and preserved tasks validate against their saved version.
- On macOS, use Chrome's user NativeMessagingHosts path for Brave.
- Allow browser setup record validation to accept an explicit platform in isolated tests/status/uninstall.
- Add focused regressions for legacy permission semantics and Brave macOS manifest location.
- Run full regression and encrypted-backup matrices.

## Out of scope

- BrowserBroker redesign.
- Extension protocol redesign.
- Browser UI installation automation.
- New web backends or search providers.
- Notebook schema/data migration.
- Any change to cross-workspace policy or model authority.

## Responsibility boundary

- Owner: approves correction and any promotion.
- Context Router: keeps this request in WS-HUMANOS / HOS-BROWSER-001.
- Saved task permission version: authority for preserved transaction semantics.
- Browser setup module: owns local pairing path selection only.
- BrowserBroker/runtime approval: unchanged.
- CI/tests: evidence only.

## Acceptance tests

- A saved v4 scope for "search the web..." still evaluates browser_enabled=false.
- A new v7 scope for explicit browser/web/internet intent evaluates browser_enabled=true.
- validate_scope accepts v7 and preserves validation of v1-v6.
- New browser-intent Agent tasks persist permission version 7; unrelated tasks preserve their existing version-selection behavior.
- Brave/macOS manifest path resolves to
  `~/Library/Application Support/Google/Chrome/NativeMessagingHosts`.
- Chrome/Chromium paths remain unchanged.
- Browser setup/status/remove isolated tests pass on supported CI platforms.
- Full HumanOS regression matrix remains green.
- Encrypted-backup/full-suite remains green.
- Exact diff contains no secret material, Notebook content, or owner-local paths.

## External evidence

Current Brave source overrides macOS native messaging to Chrome's standard user
NativeMessagingHosts location. Chrome's native messaging documentation requires a
registered manifest with exact allowed origins and an absolute host path on macOS/Linux.

## Rollback

Revert the correction commit. No local or Notebook data migration is required.

## Done condition

Focused and full tests are green on the exact candidate commit, diff review is clean,
the correction is promoted under owner authorization, and local Mac pairing remains
truthfully pending until runtime readback is performed.


## Verification evidence

- Verified candidate: `9b6050c3aaccca0032e843652743cb2caf3d470b`.
- Regression workflow `35456032309`: SUCCESS on Ubuntu 24.04/macOS 15 × Python 3.11/3.13.
- Encrypted-backup workflow `35456032318`: SUCCESS on the same four matrix combinations.
- Promotion PR: #93.
- Promotion commit: `7c21306aa3dac28cf274e39360d600a7ca7e8abf`.
- Exact diff reviewed for authority expansion, Notebook/private data, local owner paths,
  secret material, and unrelated component changes; no such leakage or widening found.
- Parent activation PR #91 exact head `cd14dec87ca742785d8f3462b701e0c1915458bf`
  was independently confirmed green before this correction.
- Real browser end-to-end connectivity remains intentionally unverified until owner-Mac
  pairing and one bounded action readback are completed.

## Post-promotion next action

On the owner Mac, update `runtime-0.1`, run `humanos --browser-setup`, load the
unpacked `browser-extension/` once, click the extension on the selected tab, run
`humanos --browser-status`, then execute one bounded browser search/inspect test.
