# EXP-R3-A-001 — Local Qwen diagnostic note — 2026-09-14

**Status:** HOST DIAGNOSTIC OBSERVED / NOT A PASS A SUBMISSION

## Purpose

Separate local Ollama/model-template compatibility from failures caused by the full EXP-R3-A-001 input. The diagnostic prompt was neutral (`Return exactly the word OK and nothing else.`) and therefore is not itself a constitutional evaluation.

## Host observations supplied by the human operator

All four inspected tags reported the same broad model metadata through Ollama: family `qwen3moe`, parameter size `30.5B`, quantization `Q4_K_M`, reported context length `262144`.

| Tag | `/api/chat` | `/api/generate` | Diagnostic interpretation |
|---|---|---|---|
| `qwen3-coder:16k` | `OK`, `done_reason=stop`, `eval_count=2` | `OK`, `done_reason=stop`, `eval_count=2` | basic local runtime path is healthy |
| `qwen3-coder-local:16k` | empty, `done_reason=None`, `eval_count=None` | empty, `done_reason=None`, `eval_count=None` | local tag/runtime path is not producing visible completions even for smoke input |
| `qwen3-coder:latest` | empty, `done_reason=None`, `eval_count=None` | empty, `done_reason=None`, `eval_count=None` | same failure class |
| `qwen3-coder:30b` | empty, `done_reason=None`, `eval_count=None` | empty, `done_reason=None`, `eval_count=None` | same failure class |

## Interpretation boundary

These results do **not** establish that the latter three model artifacts are defective in general. They establish only that, in the observed local Ollama configuration at this time, those tags did not produce visible completions through either tested endpoint for the neutral smoke request.

`qwen3-coder:16k` is therefore the only currently demonstrated healthy Qwen candidate for the full Pass A run.

## New hypothesis from the full-run failure

The earlier full Pass A harness requested a context window up to `131072` because it trusted the model-reported maximum. The neutral diagnostic used only `4096`. Since `qwen3-coder:16k` succeeds on the small-context smoke test but failed on the full run, the next controlled test will keep the **exact same frozen Pass A textual input** while reducing only the requested Ollama context/resource budget.

This is a runtime/resource diagnostic, not a change to the constitutional challenge.

## Next controlled full run

Use v2 with an explicit 16,384-token context cap and 6,500-token maximum output budget:

```bash
python3 research/friends/round3/run_local_pass_a_v2.py \
  --model qwen3-coder:16k \
  --context-cap 16384 \
  --max-output-tokens 6500 \
  --min-output-tokens 5000
```

The frozen input text and seed/temperature remain unchanged. If this produces a complete visible response, it can be reviewed for official local Qwen eligibility. If it still fails or is structurally incomplete, preserve that outcome and do not silently change APIs, prompt text, or model identity.
