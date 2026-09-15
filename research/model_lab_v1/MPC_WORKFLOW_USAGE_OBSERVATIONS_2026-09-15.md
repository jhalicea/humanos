# MPC Workflow Usage Observations — 2026-09-15

**Status:** RAW/DERIVED PROVENANCE RECORD — NOT SINGLE-MODEL COST ACCOUNTING

This file supplements `RAW_USAGE_OBSERVATIONS.md`. It preserves a repeated real-work workflow the owner described as:

- **Engineer:** GPT-6 Astra — **Light** effort
- **Coder:** GPT-5.6 Terra — **High** effort
- **Context:** work on the **MPC branch**

The owner clarified that the work proceeds in repeated rounds with this role split. The usage UI reports shared plan allowance, so these intervals measure the **combined workflow**, not either model individually.

## Observed sequence

| Round | Approx interval | 5-hour left | Weekly left | Raw displayed movement | Notes |
|---|---|---:|---:|---:|---|
| 1 | 15:50 -> 15:58 | 69% -> 59% | 48% -> 47% | **-10 pp / -1 pp** | Previously recorded mixed interval. Owner identified both Astra Light and Terra High as participants. |
| 2 | 15:58 -> 16:05 | 59% -> 49% | 47% -> 45% | **-10 pp / -2 pp** | Treated as another round of the same workflow based on the owner's clarification that the rounds use Astra Light as engineer and Terra High as coder. If later evidence shows other Work activity occurred in this interval, attribution must be relabeled without deleting the raw endpoints. 16:05 screenshot SHA-256: `6e1af0ea1f2128ca5ac7ee10221ee3829a8830e7332f999381e614a63e6cc725`. |
| 3 | 16:05 -> 16:12 | 49% -> 43% | 45% -> 44% | **-6 pp / -1 pp** | Another stated round of the Astra-Light-engineer -> Terra-High-coder workflow. 16:12 screenshot SHA-256: `34265f143f5f898e0f3ad75cfb8cd4935e8bebc5630c69b32c0f4a9309184a59`. |

## Aggregate observed workflow movement

Across the three sequential displayed intervals:

- 5-hour allowance: **69% -> 43% = 26 percentage points consumed**
- weekly allowance: **48% -> 44% = 4 percentage points consumed**
- observed mean per round: approximately **8.7 pp five-hour / 1.3 pp weekly**

The mean is descriptive only. Percentage points are coarse shared-plan UI telemetry, not tokens, FLOPs, dollars, or guaranteed linear compute units.

## Interpretation

What this evidence supports:

1. The **Astra Light engineer + Terra High coder** pairing is now a real observed HumanOS workflow candidate, not merely a routing idea.
2. The combined workflow consumed visible shared allowance in every observed round.
3. The displayed cost varied by round (`10/1`, `10/2`, `6/1`), so one round must not be treated as a fixed price for the workflow.
4. The UI cannot decompose how much of each round belonged to Astra versus Terra.
5. Future comparisons should evaluate the entire workflow on **quality, corrections, elapsed time, and combined usage**, then compare it against alternatives such as Sol alone, Sol -> Terra, or Astra alone on equivalent work.

## Provenance rule

Do not rewrite these observations to force a clean model-cost estimate. Preserve the raw endpoints and update only the interpretation if new information appears.
