# HumanOS Status Snapshot

Status: HOS-BROWSER-001-R1 ACTIVE
Date: 2026-09-19
Workspace: `WS-HUMANOS`
Workstream: `HOS-BROWSER-001 — Browser Broker and Tools`
Slice: `HOS-BROWSER-001-R1 — Browser Activation Compatibility Correction`
Branch: `fix/browser-activation-r1`
Baseline: `runtime-0.1@856a41b7852e18f19b872e0f0b6f9367e65ee3d6`
Parent promotion: PR #91 / `02869089cd336ffac17751a771bd61adcf21229d`
Work order: `docs/work-orders/HOS-BROWSER-001-R1.md`

## Why this correction exists

The promoted browser activation changed the meaning of legacy permission scope
versions by adding web/internet intent under v4-v6. Preserved task scopes must not
change semantics after upgrade. The correction assigns expanded browser intent to v7
for new Agent tasks while keeping older saved versions stable.

Current Brave source also routes macOS native messaging through Chrome's standard
user NativeMessagingHosts location. The promoted setup used Brave's profile-specific
path; R1 corrects the lookup and adds a regression.

## Responsibility boundary

Owner -> Context Router -> HOS-BROWSER-001 -> R1 Work Order -> focused branch -> tests/evidence.
BrowserBroker, native host, extension, Mirror, and interactive browser approval retain
their promoted responsibilities; R1 does not widen authority.

## Current evidence

- Baseline PR #91 regression and encrypted-backup workflows were independently
  confirmed green on exact head `cd14dec87ca742785d8f3462b701e0c1915458bf`.
- R1 focused/full CI: pending.
- Local Mac browser pairing/readback: pending after canonical promotion.

## Rollback

Revert the R1 promotion commit. No Notebook or local browser-state migration is part
of this correction.

## Next action

Run CI on the exact R1 candidate; resolve any regressions; review diff/privacy; promote
only if verified, then return to the existing local Mac pairing/readback next action.
