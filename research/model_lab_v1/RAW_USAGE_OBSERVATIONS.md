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
| 2026-09-15 pre-Luna start | **Pre-Luna usage screenshot / evidence supplied later** | **55%** | **53%** | **-16 pp / -2 pp from 12:59** | **Critical attribution boundary:** this reading was already present before Luna was started. Therefore none of this 16/2 movement was caused by Luna. It is delayed reporting from prior agentic work. With no other relevant Work/Codex activity reported in the interval, Astra Stage 1 + Stage 2 are the strongest likely source, though exact separation from any residual earlier posting cannot be proven from the UI alone. |
| 2026-09-15 13:16 | Luna Stage 1 post | 55% | 53% | **0 pp / 0 pp from confirmed pre-Luna reading** | Luna Stage 1 produced no visible additional meter movement at this snapshot. This does not prove zero usage; usage may be below rounding resolution or delayed. |
| 2026-09-15 13:24 | Luna revised-artifact / Stage 2 snapshot | 55% | 53% | **0 pp / 0 pp from 13:16** | Screenshot SHA-256 `0fb9bda5ca24d1462bcce6a95d1ece3f4a1a1a788212695f2c82ac1736af0420`. Through this snapshot, Luna's two visible post-start intervals produced no additional displayed percentage-point movement. |

## Attribution analysis after pre-Luna evidence

The later screenshot sequence materially sharpens the earlier interpretation:

- The **71/55 -> 55/53** movement happened **before Luna began**. It is therefore impossible for Luna to have caused that visible drop.
- The movement is delayed posting from **prior** Work/Codex activity. Given the immediately preceding runs were Astra Stage 1 and Stage 2, and the owner reported no other relevant agentic activity, Astra is the **most likely dominant source** of the delayed block.
- Exact decomposition is still not available from the percentage UI. A small residual from earlier work cannot be excluded because the meter is demonstrably delayed and rounded.
- Luna Stage 1 is now bounded by a confirmed pre-run value of **55/53** and a post-run value of **55/53**: raw visible delta **0/0**.
- The later Luna revised-artifact snapshot also remained **55/53**, giving another raw visible delta of **0/0**.
- Preserve all earlier screenshots and interpretations as historical evidence; this newer evidence updates attribution rather than deleting prior observations.

## Interpretation state

- **Terra:** observed Stage 2 UI delta preserved as 4 pp 5-hour / 1 pp weekly. Exact compute attribution is not guaranteed because later runs revealed meter lag.
- **GPT-5.5:** observed Stage 2 UI delta preserved as 9 pp / 2 pp. It remains an observed interval, not a token count.
- **Astra:** immediate Stage 1 and Stage 2 observations of 0 pp / 0 pp are preserved. A later **pre-Luna** screenshot already showed 55/53, proving that the 16 pp / 2 pp delayed movement occurred before Luna. Astra is the most likely dominant source, but exact causal accounting remains unavailable.
- **Luna Stage 1:** confirmed raw pre/post visible meter values are **55/53 -> 55/53 = 0 pp / 0 pp**. Do not interpret as zero compute; only zero displayed movement in that interval.
- **Luna Stage 2 / revised-artifact interval:** **55/53 -> 55/53 = 0 pp / 0 pp** through the 13:24 snapshot.

## Measurement lesson

The plan-usage UI is useful provenance but not a real-time accounting API. Preserve every visible reading and timestamp, then model meter latency and rounding as confounds instead of deleting or "correcting" inconvenient observations. Establish a true model boundary using a screenshot **after prior delayed movement has appeared and before the next model begins** whenever possible.
