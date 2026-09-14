# EXP-R3-A-001 — Qwen 16k controlled rerun

**Date:** 2026-09-14
**Status:** HOST EXECUTED / RAW FROZEN LOCAL PARTIAL
**Participant:** local `qwen3-coder:16k` via Ollama

## Controlled variable change

After the same model tag passed the neutral smoke test at a small context but returned no visible text in the earlier large-context Pass A attempt, the host reran the exact frozen Pass A input with a reduced context/output envelope:

```text
--context-cap 16384
--max-output-tokens 6500
--min-output-tokens 5000
```

The frozen Pass A text, model tag, seed, temperature, and chat path were otherwise unchanged.

## Host-observed result

```text
status: RAW_FROZEN_LOCAL_PARTIAL
response SHA-256: 728fddb99e8137744662d6182fd504959bdf03caef6489b58c9da9d4365d426d
response bytes: 25923
response lines: 425
elapsed_seconds: 863.5
elapsed_human: about 14m23.5s
done_reason: stop
eval_count: 4958
```

The reduced context therefore resolved the prior empty-visible-response failure and produced a substantial visible answer.

## Structural checker result

The v2 literal marker checker reported the following markers missing:

- `TRIAL 1` through `TRIAL 12`
- `TRY TO KILL THE CONSTITUTION`
- `PROPOSE THE MINIMUM CHANGE SET`

It did **not** report these later required markers missing:

- `SCORE THE CONSTITUTION`
- `THE ONE EXPERIMENT`
- `FINAL VERDICT`
- `STRONGEST CONSTITUTIONAL IDEA`
- `MESSAGE TO THE OTHER FRIENDS`

## Interpretation boundary

This proves the earlier empty-response problem was sensitive to the requested runtime context size. It does **not** yet prove that Qwen omitted the first twelve trials: the checker is literal and may have missed semantically equivalent headings. The raw answer should remain sealed from substantive comparison until the blind cohort is complete.

Next step: perform a structure-only inspection of headings/section labels without reading or comparing the findings themselves. Until then, blind-scoring eligibility remains **PENDING STRUCTURAL REVIEW**.
