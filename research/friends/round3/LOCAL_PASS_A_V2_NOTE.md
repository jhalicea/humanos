# EXP-R3-A-001 — Local Pass A v2 note

**Status:** IMPLEMENTED CANDIDATE / HOST VERIFICATION REQUIRED
**Reason for v2:** The first host run on 2026-09-14 produced one short Llama response and one Qwen empty-visible-response failure. The original v1 harness is preserved unchanged as experiment history.

## Observed v1 host evidence supplied by the human operator

- `llama3.2:latest` reached Ollama and produced a visible response: 4,364 bytes, 42 lines, 63.1 seconds, `done_reason=stop`, `eval_count=775`, with response SHA-256 `1ca6453e67568f964ee8b10bc7977c07f5cb721bfedc927c6371e13eb9c2fb50`.
- `qwen3-coder:16k` failed in the v1 harness with `RuntimeError: Ollama returned an empty/non-text response`.

These observations do **not** yet establish either model as a complete official Pass A participant. The Llama response is suspiciously short for the required protocol and must pass structural completeness checks. The Qwen failure needs visible-response diagnostics.

## V2 changes

`run_local_pass_a_v2.py`:

1. explicitly requests `think=false` from Ollama;
2. never saves hidden thinking text; it records only whether a thinking field was present and its character count;
3. records top-level and message response keys on failures;
4. preserves non-empty outputs even when incomplete;
5. checks for all 12 trials plus the required terminal sections before assigning `RAW_FROZEN_LOCAL`;
6. labels incomplete visible answers `RAW_FROZEN_LOCAL_PARTIAL`;
7. raises the planned output allowance to 12,000 tokens and requires at least 5,000 tokens of available output context for a fair full Pass A run.

## Host rerun

From the isolated worktree:

```bash
cd /Users/jhalicea/humanos-r3
git pull --ff-only
python3 research/friends/round3/run_local_pass_a_v2.py \
  --model llama3.2:latest \
  --model qwen3-coder:16k
```

Do not delete or overwrite the v1 artifacts. They are part of the experiment history.

If Qwen still returns no visible text, preserve the v2 metadata and test a stronger installed Qwen candidate in a separate fresh run rather than modifying or hiding the failure.
