# MLAB-P2-B-55-CAL1 — GPT-5.5 Usage Calibration

**Model:** GPT-5.5  
**Trial:** Trial B Stage-1 replication / usage calibration  
**Surface:** Work  
**Effort:** Light  
**Date:** 2026-09-15  
**Status:** CALIBRATION RUN COMPLETE / SHORT SETTLE OBSERVED / LONGER-LAG POSSIBILITY NOT EXCLUDED  

## Corrected timing

Owner clarified that the run **started at approximately 14:35**, not 14:42.

Raw snapshots:
- **14:35 pre-run / start:** 92% left on 5-hour meter, 52% left weekly
- **14:42 first post-run snapshot:** 83% / 50%
- **14:44 second post-run snapshot:** 83% / 50%

Therefore the confirmed raw displayed interval for this calibration run is:
- **5-hour: 92% -> 83% = 9 percentage points displayed movement**
- **weekly: 52% -> 50% = 2 percentage points displayed movement**

The two post-run readings were unchanged across approximately two minutes, giving a short-settle observation. This does **not** prove no later delayed posting can occur, because earlier Trial B runs demonstrated meter lag.

## Replication significance

The original GPT-5.5 Stage 2 interval also displayed **9 pp / 2 pp** movement. This calibration run independently reproduced the same visible percentage movement for a substantial PDF-generation task, increasing confidence that `9/2` is a meaningful UI-level usage signal for this class of GPT-5.5 Work task under these conditions.

Do not convert the percentages to tokens, FLOPs, or exact compute cost.

## Artifact replication note

Replication PDF SHA-256: `fb3916d34126a2a9289e3770427bd2fb75611068109ec20aed7889d825573565`

The replication artifact remained substantively strong but showed a layout defect on the Phase 1 score page: score denominators such as `180/180` wrapped awkwardly across lines. Treat this as variance/repeatability evidence, not as a replacement for the original Trial B quality score.

## Screenshot provenance

- 14:35 pre-run screenshot SHA-256: `f49263a86afff8d637b1c84cee7163e8ee6a2f0d25084f58beb5c427bf82eed8`
- 14:42 first post-run screenshot SHA-256: `115d829de6ff48f9feb2049b06424dc0ada33f71f8b617cddff4c1cbba0b34e7`
- 14:44 second post-run screenshot SHA-256: `51acd4fc8eab4f021eb330776d72ae905d4b6ea045d302e85899ea8a7014c1da`

## Interpretation

**Attribution confidence: HIGH for this visible interval**, because the owner identified 14:35 as the run start and supplied two post-run screenshots at 14:42 and 14:44 with no intervening Work/Codex activity reported. Remaining caveats are meter rounding and possible longer-lag posting.
