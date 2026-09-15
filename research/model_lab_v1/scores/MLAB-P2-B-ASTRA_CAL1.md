# Astra CAL1

**Model:** GPT-6 Astra  
**Trial:** Trial B Stage-1 replication / usage calibration  
**Surface:** Work  
**Effort:** Light  
**Date:** 2026-09-15  
**Status:** CALIBRATION RUN COMPLETE / SETTLED THROUGH 15:10

## Raw readings

- **14:54 pre-run / refreshed baseline:** 83% five-hour, 50% weekly.
- **15:01 first post-run / refreshed reading:** 77% five-hour, 49% weekly.
- **15:05 refreshed settle check:** 77% five-hour, 49% weekly.
- **15:10 refreshed settle check:** 77% five-hour, 49% weekly.

Confirmed displayed movement for this calibration run:
- **5-hour: 83% -> 77% = 6 percentage points**
- **weekly: 50% -> 49% = 1 percentage point**

The displayed values remained stable from 15:01 through 15:10, approximately nine minutes after the first post-run observation.

## Refresh-control finding

The owner reported an important procedural difference from the earlier Trial B Astra run: during this calibration, the Usage page was manually refreshed before/while collecting readings. In the earlier run, the page was not refreshed between observations.

This creates a strong alternative explanation for the earlier apparent "delayed posting": the Usage UI may have been displaying stale values until refresh rather than the backend necessarily posting usage many minutes late.

Current interpretation:
- **Do not erase the earlier raw observations.** They remain valid screenshots of what the UI displayed.
- **Downgrade the claim that Astra usage is necessarily asynchronously posted.** The earlier pattern may instead reflect a stale/unrefreshed Usage view.
- Future usage measurements should require an explicit page refresh before every recorded reading.

This calibration does not prove there can never be backend delay; it shows that refresh state is a material confound that must be controlled.

## Comparison signal

For the same frozen Stage-1 PDF task class:
- GPT-5.5 CAL1: **9 pp five-hour / 2 pp weekly**
- Astra CAL1: **6 pp five-hour / 1 pp weekly**

At the UI-telemetry level, Astra displayed lower plan-meter movement in this replication. This is surprising and should be treated as a measured run, not a universal cost conclusion. Percentages are coarse plan telemetry, not tokens, FLOPs, dollars, or exact compute.

## Artifact replication

Replication PDF SHA-256: `0aff0c680688b132f5d9f61c24224cf1e0e05ddd8c6d149b32c10eb10e357fd3`

The six-page replication artifact remained source-disciplined and explicitly separated measured results, owner observations, routing hypotheses, and unresolved questions. It is a replication artifact and does not replace the original Trial B quality score.

## Screenshot provenance

- 14:54 baseline: `12aed926f381dafdcdc325b649fd3108f5edc76f61b5df7fcaff846585c9d238`
- 15:01 first post-run: `9f8ab1400a0f96549535e4766accbb908996308e3b6b66f27836b516d5c7d691`
- 15:05 settle: `472ea6ec97ccd5fc5b37e9402d35c717f1a02cfe06a4e219f0620f77de32a9dc`
- 15:10 settle: `7ec869417bf1b29ac8020b6672037895b70a7140b12e879b374edd65bc0a2448`

The 15:08 screenshot supplied in the same turn shows a Haystack News page rather than the Usage panel and therefore is preserved as contextual evidence but **not** treated as a usage reading. SHA-256: `00e1e60eabfa12cd596ab8b79330b0f31dcb46a09aefbf10aad70293e3d00e9b`.

## Attribution confidence

**HIGH for the visible 83/50 -> 77/49 interval under the refreshed-page protocol.** Remaining caveats are percentage rounding, plan-meter semantics, and the fact that one calibration run cannot establish a universal per-task cost ratio.