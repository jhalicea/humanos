# HumanOS Model Lab v1 — Raw Usage Observations

**Purpose:** Preserve UI telemetry exactly as observed, even when attribution is later found to be delayed, contaminated, rounded, or otherwise unreliable.

## Provenance rule

Raw observations are immutable evidence. Later interpretation may change, but the original meter reading, timestamp, screenshot reference/hash when available, and surrounding context must remain preserved.

Never replace a raw observation with a corrected estimate. Record both layers separately:

1. **Observed telemetry** — what the UI showed at that time.
2. **Attribution / interpretation** — what we currently think caused the movement, with confidence and confounds.

An observation can be valid provenance even when it is not valid causal attribution.

## Trial B observed usage timeline

| Approx local time | Context | 5-hour left | Weekly left | Raw observed change from prior snapshot | Attribution / notes |
|---|---|---:|---:|---:|---|
| 2026-09-15 11:18 | Terra Stage 2 pre-run | 87% | 58% | — | Clean pre-run snapshot. |
| 2026-09-15 11:46 | Terra Stage 2 post-run | 83% | 57% | -4 pp / -1 pp | At the time this was treated as strong Terra-attribution evidence because owner reported no other relevant Work activity. Keep as observed even if later meter-lag findings reduce confidence in exact attribution. |
| 2026-09-15 12:26 | GPT-5.5 Stage 1 post / Stage 2 pre | 80% | 57% | -3 pp / 0 pp from prior comparable reading | Stage 1 attribution provisional because the immediate pre-run baseline was not captured. |
| 2026-09-15 12:42 | GPT-5.5 Stage 2 post / Astra pre | 71% | 55% | -9 pp / -2 pp | Clean immediate before/after pair for 5.5 Stage 2 at the time observed. Preserve raw values; later lag findings mean the UI should still be treated as delayed/rounded telemetry rather than exact compute accounting. |
| 2026-09-15 12:55 | Astra Stage 1 immediate post | 71% | 55% | 0 pp / 0 pp | Immediate UI showed no movement. This remains a valid observation, not evidence of zero usage. |
| 2026-09-15 12:59 | Astra Stage 2 immediate post | 71% | 55% | 0 pp / 0 pp | Immediate UI again showed no movement. Later evidence demonstrated delayed posting. |
| 2026-09-15 between 12:59 and Luna start | Owner visual observation | lower than prior / changing | lower or changing | exact value not frozen | Owner explicitly observed the meter fall before Luna started. This establishes delayed posting from prior work, at least in part. |
| 2026-09-15 13:16 | Luna Stage 1 post | 55% | 53% | -16 pp / -2 pp from 12:59 snapshot | Raw interval preserved. Causal attribution is mixed/unknown because owner saw the drop begin before Luna started; may include delayed Astra plus Luna usage. |
| 2026-09-15 13:24 | Later snapshot supplied with Luna revised artifact | 55% | 53% | 0 pp / 0 pp from 13:16 snapshot | Screenshot SHA-256 `0fb9bda5ca24d1462bcce6a95d1ece3f4a1a1a788212695f2c82ac1736af0420`. Preserve as observed even though immediate model attribution is uncertain. |

## Interpretation state

- **Terra:** observed Stage 2 UI delta preserved as 4 pp 5-hour / 1 pp weekly. Exact compute attribution is not guaranteed because later runs revealed meter lag.
- **GPT-5.5:** observed Stage 2 UI delta preserved as 9 pp / 2 pp. It remains an observed interval, not a token count.
- **Astra:** immediate Stage 1 and Stage 2 observations of 0 pp / 0 pp are preserved. Later owner observation proves those immediate readings were incomplete as causal accounting because the meter fell before Luna started.
- **Luna Stage 1:** observed interval from 71/55 to 55/53 is preserved as 16 pp / 2 pp. It must not be erased merely because attribution is contaminated; instead mark causal attribution **UNKNOWN / MIXED**.
- **Luna later snapshot:** 55/53 is preserved separately rather than collapsed into Stage 1.

## Measurement lesson

The plan-usage UI is useful provenance but not a real-time accounting API. For future experiments, preserve every visible reading and timestamp, then model meter latency as a confound instead of deleting or "correcting" inconvenient observations.
