# HumanOS Model Lab v1 — Raw Usage Observations

**Purpose:** Preserve UI telemetry exactly as observed, even when attribution is later found to be delayed, contaminated, rounded, reset, or otherwise unreliable.

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
| 2026-09-15 13:48 | Sol Stage 1 post; 5-hour window has reset | **96%** | **52%** | 5-hour value not comparable to 55 because reset occurred; weekly -1 pp from 53 | Screenshot shows reset countdown **4h55m**, proving the rolling 5-hour allowance reset before this snapshot. Preserve `96/52` exactly. Sol Stage 1 may have crossed the reset boundary, so total Sol 5-hour usage cannot be reconstructed from the endpoints. Screenshot SHA-256 `c057c7c96d80f372a97c02b9171c9e52c40402076e64d9cee713553698143f12`. |
| 2026-09-15 14:03 | Sol Stage 2 post | **92%** | **52%** | **-4 pp / 0 pp from Sol Stage 2 baseline 96/52** | Same reset window: countdown **4h41m**. This is a cleaner same-window raw interval for Sol Stage 2. Screenshot SHA-256 `d225426ce6e12a1c7e301d0d0ba23f62818d1d22f8a963c609e314ccc69f8eca`. Preserve as UI telemetry, not exact compute accounting. |

## Attribution analysis after pre-Luna evidence

The later screenshot sequence materially sharpened the earlier interpretation:

- The **71/55 -> 55/53** movement happened **before Luna began**. It is therefore impossible for Luna to have caused that visible drop.
- The movement is delayed posting from **prior** Work/Codex activity. Given the immediately preceding runs were Astra Stage 1 and Stage 2, and the owner reported no other relevant agentic activity, Astra is the **most likely dominant source** of the delayed block.
- Exact decomposition is still not available from the percentage UI. A small residual from earlier work cannot be excluded because the meter is demonstrably delayed and rounded.
- Luna Stage 1 is bounded by a confirmed pre-run value of **55/53** and a post-run value of **55/53**: raw visible delta **0/0**.
- The later Luna revised-artifact snapshot also remained **55/53**, giving another raw visible delta of **0/0**.
- Preserve all earlier screenshots and interpretations as historical evidence; newer evidence updates attribution rather than deleting prior observations.

## Sol reset-boundary interpretation

The Sol Stage 1 post-run screenshot introduces a different confound: **window reset**.

- Previous stable snapshot: **55% / 53%** at approximately 13:24.
- Sol post-Stage-1 snapshot: **96% / 52%** at approximately 13:48.
- The screenshot says the 5-hour limit resets in **4h55m**, which means a new 5-hour window began roughly five minutes earlier.
- Therefore `55 -> 96` is not usage recovery caused by the model; it is the allowance reset.
- If the new window reset to 100%, the snapshot shows 4 percentage points consumed in the new window by 13:48. That is a useful observed state, but not a valid total-cost estimate for Sol Stage 1 because the task may have begun before the reset and meter posting may lag.
- Weekly usage moved **53 -> 52**, a raw observed 1-point decrease over the broader interval. Sol is the strongest likely source in run order, but exact causal attribution remains subject to known delayed posting.

Sol Stage 2 has a cleaner same-window pair:
- pre-run **96/52**;
- post-run **92/52**;
- raw displayed movement **4 pp five-hour / 0 pp weekly**.

No reset occurred between those Stage 2 endpoints. This improves attribution confidence relative to Stage 1, but it is still rounded UI telemetry and delayed posting remains possible.

## Interpretation state

- **Terra:** observed Stage 2 UI delta preserved as 4 pp 5-hour / 1 pp weekly. Exact compute attribution is not guaranteed because later runs revealed meter lag.
- **GPT-5.5:** observed Stage 2 UI delta preserved as 9 pp / 2 pp. It remains an observed interval, not a token count.
- **Astra:** immediate Stage 1 and Stage 2 observations of 0 pp / 0 pp are preserved. A later **pre-Luna** screenshot already showed 55/53, proving that the 16 pp / 2 pp delayed movement occurred before Luna. Astra is the most likely dominant source, but exact causal accounting remains unavailable.
- **Luna Stage 1:** confirmed raw pre/post visible meter values are **55/53 -> 55/53 = 0 pp / 0 pp**. Do not interpret as zero compute; only zero displayed movement in that interval.
- **Luna Stage 2 / revised-artifact interval:** **55/53 -> 55/53 = 0 pp / 0 pp** through the 13:24 snapshot.
- **Sol Stage 1:** post-run raw observation is **96/52** after a 5-hour reset. The reset prevents a direct 5-hour delta from the prior 55% baseline. Weekly raw movement from the previous snapshot is -1 pp. Exact Sol Stage 1 usage remains unresolved.
- **Sol Stage 2:** confirmed same-window visible pair is **96/52 -> 92/52 = 4 pp / 0 pp**. Cleaner attribution than Stage 1, but not token or exact compute accounting.

## Measurement lesson

The plan-usage UI is useful provenance but not a real-time accounting API. Preserve every visible reading and timestamp, then model meter latency, rounding, and window resets as confounds instead of deleting or "correcting" inconvenient observations. Establish a true model boundary using a screenshot **after prior delayed movement has appeared and before the next model begins** whenever possible.
