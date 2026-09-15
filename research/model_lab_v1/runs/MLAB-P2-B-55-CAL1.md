# MLAB-P2-B-55-CAL1 — GPT-5.5 usage-calibration replication

**Model:** GPT-5.5  
**Trial:** Trial B Stage-1 prompt replication for usage calibration  
**Surface:** Work  
**Effort:** Light  
**Status:** IN PROGRESS / IMMEDIATE POST SNAPSHOT CAPTURED / DELAY WATCH PENDING

## Purpose

Repeat the exact frozen Trial B Stage-1 PDF task to measure usage-meter posting behavior without replacing the original quality run. This is a replication/calibration run, not a new canonical Trial B score.

## Artifact provenance

- Replication PDF SHA-256: `fb3916d34126a2a9289e3770427bd2fb75611068109ec20aed7889d825573565`
- Untouched completion response preserved in conversation:
  - `Created HumanOS_Model_Lab_Interim_Model_Routing_Brief.pdf as a finished 7-page executive brief.`
  - Model described an editorial research-brief structure, restrained palette, spacious page breaks, score-bar visuals, uncertainty/transition callouts, and a routing table.
  - Model stated it rendered and visually checked all pages.

## Usage observations

### Pre-run boundary — 2026-09-15 14:42 local

- 5-hour left: **83%**
- weekly left: **50%**
- 5-hour reset countdown: **4h01m**
- screenshot SHA-256: `115d829de6ff48f9feb2049b06424dc0ada33f71f8b617cddff4c1cbba0b34e7`

This is the official CAL1 pre-run baseline. It occurs after a prior drop from the Sol 14:03 snapshot (92/52) to 83/50. Because that drop was already present before GPT-5.5 CAL1 began, it must not be attributed to GPT-5.5 CAL1.

### Immediate post-run — 2026-09-15 14:44 local

- 5-hour left: **83%**
- weekly left: **50%**
- 5-hour reset countdown: **3h59m**
- raw immediate delta: **0 pp / 0 pp**
- screenshot SHA-256: `51acd4fc8eab4f021eb330776d72ae905d4b6ea045d302e85899ea8a7014c1da`

Interpretation: no whole-percentage movement was visible immediately after completion. This is not evidence of zero compute. Delayed posting remains a known possibility.

## Replication-quality note

The seven-page replication is substantively faithful to the source packet and preserves the no-universal-winner / GPT-5.5-transitional constraints. However, the rendered Phase 1 score column on page 3 visibly wraps denominators awkwardly (`180/18` then `0`, etc.), making this replication visually weaker than the original GPT-5.5 Trial B artifact. Preserve this as repeatability evidence; do not overwrite the original quality score.

## Next observations required

Capture usage snapshots at approximately:
- +2 minutes after immediate post;
- +5 minutes;
- +10 minutes;
- continue until two consecutive observations remain unchanged a few minutes apart.

Do not start Astra calibration until GPT-5.5 meter movement has settled or the run is explicitly marked unresolved.
