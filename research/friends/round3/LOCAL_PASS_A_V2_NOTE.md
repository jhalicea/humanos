# EXP-R3-A-001 — Local Pass A v2 note

**Status:** HOST EXECUTED / PARTIAL + FAILED / NEXT DIAGNOSTIC IMPLEMENTED
**Reason for v2:** The first host run on 2026-09-14 produced one short Llama response and one Qwen empty-visible-response failure. The original v1 harness is preserved unchanged as experiment history.

## Observed v1 host evidence supplied by the human operator

- `llama3.2:latest` reached Ollama and produced a visible response: 4,364 bytes, 42 lines, 63.1 seconds, `done_reason=stop`, `eval_count=775`, with response SHA-256 `1ca6453e67568f964ee8b10bc7977c07f5cb721bfedc927c6371e13eb9c2fb50`.
- `qwen3-coder:16k` failed in the v1 harness with `RuntimeError: Ollama returned an empty/non-text response`.

These observations did **not** establish either model as a complete official Pass A participant.

## V2 host rerun evidence

The human operator then ran `run_local_pass_a_v2.py` from the isolated worktree.

### llama3.2:latest

Observed:

- status: `RAW_FROZEN_LOCAL_PARTIAL`
- response SHA-256: `1ca6453e67568f964ee8b10bc7977c07f5cb721bfedc927c6371e13eb9c2fb50`
- response bytes: `4364`
- response lines: `42`
- runtime: `50.9s`
- `done_reason=stop`
- `eval_count=775`
- all required Pass A structural markers were reported missing by the v2 compliance checker.

Important observation: the response SHA-256 is identical to the v1 run. With the same frozen input, seed, and temperature, the model reproduced the same short visible output across both runs. This strongly supports that the short result is reproducible model behavior under this harness rather than a one-off transport failure. It remains **PARTIAL / NOT ELIGIBLE AS A COMPLETE PASS A SUBMISSION** until the raw response itself is reviewed for substantive content after blind collection is complete.

### qwen3-coder:16k

Observed:

- status: `FAILED_EMPTY_VISIBLE_RESPONSE`
- terminal: `FAIL: Ollama returned no visible text response`
- response message keys: `['content', 'role']`
- `done_reason=None`
- `eval_count=None`

The absence of `done_reason` and `eval_count`, combined with blank visible content, means the failure should not yet be attributed to constitutional reasoning quality. It may be a model/runtime/template compatibility issue or another local inference failure.

## Interpretation boundary

Do not score Llama on constitutional quality as if it completed the assigned protocol. Do not score Qwen as a substantive refusal or failure of constitutional reasoning. The current evidence is:

- Llama: **reproducible incomplete visible response**.
- Qwen 16k: **local visible-response failure**.

## Next diagnostic

A separate non-HumanOS diagnostic was added at:

`research/friends/round3/diagnose_local_ollama.py`

It sends only the neutral prompt `Return exactly the word OK and nothing else.` through both Ollama `/api/chat` and `/api/generate`. It records model family, parameter size, quantization, reported context length, visible response fields, completion metadata, and whether a hidden-thinking field existed, without storing hidden thinking text.

This diagnostic is explicitly **NOT EXP-R3-A-001** and cannot be scored as a constitutional run. Its purpose is to determine whether Qwen's empty response is caused by the model/runtime/template path or specifically by the long Pass A request.

Recommended diagnostic cohort:

```bash
python3 research/friends/round3/diagnose_local_ollama.py \
  --model qwen3-coder:16k \
  --model qwen3-coder-local:16k \
  --model qwen3-coder:latest \
  --model qwen3-coder:30b
```

After identifying a Qwen variant that returns normal visible text through `/api/chat`, run that exact model through the unchanged v2 Pass A harness in a fresh request.
