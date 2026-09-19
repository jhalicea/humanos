# HumanOS Status Snapshot

Status: HOS-BROWSER-001 PROMOTED / LOCAL MAC READBACK PENDING
Date: 2026-09-19
Workspace: `WS-HUMANOS`
Workstream: `HOS-BROWSER-001 — Browser Broker and Tools`
Canonical branch: `runtime-0.1`
Canonical promotion: `7c21306aa3dac28cf274e39360d600a7ca7e8abf`
Parent activation: PR #91 / `02869089cd336ffac17751a771bd61adcf21229d`
R1 correction: PR #93 / `7c21306aa3dac28cf274e39360d600a7ca7e8abf`
Work order: `docs/work-orders/HOS-BROWSER-001-R1.md`

## Canonical outcome

HumanOS now has the governed Browser Bridge activation path in the canonical runtime:

- owner-local pairing/config outside Git;
- stable unpacked extension identity and native messaging;
- generated native-host launcher/manifest;
- governed browser search/inspect/navigation/click/type;
- selected-tab control;
- truthful extension failure propagation;
- exact task-scope and interactive approval gates;
- permission-scope v7 only for browser-intent turns, preserving legacy v1-v6 semantics;
- corrected Brave/macOS native-messaging lookup.

## SDLC / router evidence

Route: `OWNER -> WS-HUMANOS -> HOS-BROWSER-001 -> HOS-BROWSER-001-R1 -> branch -> evidence`.

- R1 candidate: `9b6050c3aaccca0032e843652743cb2caf3d470b`.
- Regression workflow `35456032309`: SUCCESS across macOS/Ubuntu × Python 3.11/3.13.
- Encrypted-backup workflow `35456032318`: SUCCESS across the same matrix.
- Exact diff reviewed; no Notebook content, credentials, owner-local paths, secret bytes,
  cross-workspace data, or model-authority widening were introduced.
- Chrome native-messaging behavior was checked against current official Chrome docs;
  Brave/macOS lookup was checked against current Brave source.
- Promotion was performed only after the exact candidate was green.

## Remaining evidence gap

Repository/CI proof cannot establish that Jon's local Brave extension/native host is
paired and the selected-tab bridge is live. That requires local post-promotion readback.

## Rollback

Revert `7c21306aa3dac28cf274e39360d600a7ca7e8abf` for the R1 correction and, if needed,
`02869089cd336ffac17751a771bd61adcf21229d` for the parent activation. No Life
Notebook migration was performed.

## Next action

On Jon's Mac:

1. pull canonical `runtime-0.1`;
2. run `humanos --browser-setup`;
3. load `browser-extension/` once as an unpacked extension in Brave/Chrome;
4. click the HumanOS extension on the tab Jon wants Mirror to operate;
5. run `humanos --browser-status`;
6. run one bounded browser search/inspect through Mirror and verify the result.
