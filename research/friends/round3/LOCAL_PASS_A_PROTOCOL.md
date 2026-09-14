# FRIENDS Round 3 — Local Model Pass A Protocol

**Status:** IMPLEMENTED CANDIDATE / HOST VERIFICATION REQUIRED
**Experiment:** EXP-R3-A-001
**Purpose:** Run the Blind Constitutional Convention against local Ollama models without exposing them to prior FRIEND answers or HumanOS runtime context.

## Isolation model

Each local run receives exactly two textual inputs from the checked-out research branch:

1. `research/friends/round3/PASS_A_CLEANROOM_PROMPT.md`
2. `core/constitution.md`

The harness opens a fresh Ollama `/api/chat` request for each model and sends no prior conversation history, no Life Notebook context, no other FRIEND answer, no repository summary, and no HumanOS architecture material beyond what is present in the Constitution itself.

The harness is research-only. It does not modify HumanOS authority, permissions, canonical state, or the Constitution.

## Evidence captured per run

- exact requested Ollama model name;
- locally reported model digest when available;
- model family, parameter size, and quantization when available;
- locally reported context length when available;
- prompt SHA-256;
- Constitution SHA-256;
- combined-input SHA-256;
- sampling seed and temperature;
- start/end timestamps;
- runtime duration;
- prompt/evaluation token counts when Ollama reports them;
- raw response path;
- raw response byte count, line count, and SHA-256;
- completion reason;
- failure or skip reason if the model cannot run fairly.

## Context safeguard

The full Pass A prompt plus Constitution is large. The harness estimates input size conservatively and checks the model's reported context length. A model is skipped rather than silently truncating the experiment when fewer than 3,000 output tokens remain after the input and a safety reserve.

This means an older local model may be scientifically ineligible for the full Pass A even if it is otherwise useful. A shortened local challenge would be a different experiment and must receive a different experiment ID.

## Sampling

For initial local runs:

- temperature: `0`
- seed: `424242`
- maximum requested output: `8000` tokens
- loopback Ollama endpoint only

These values make local reruns more reproducible. They do not imply deterministic byte-identical output across model/runtime updates.

## Recommended first cohort

Run the strongest context-capable representatives first:

- `llama3.2:latest`
- `qwen3-coder:16k`

Then, if resources permit:

- `qwen3-coder:30b`
- `qwen3-coder:latest`
- `llama3:latest` only if the harness reports sufficient context; otherwise preserve the skip as evidence rather than forcing truncation.

## Safe host procedure

Use a separate git worktree so the main HumanOS working tree is not switched or disturbed:

```bash
cd /Users/jhalicea/humanos
git fetch origin
git worktree add ../humanos-r3 origin/research/friends-round3-sovereignty-gauntlet
cd ../humanos-r3

python3 research/friends/round3/run_local_pass_a.py \
  --model llama3.2:latest \
  --model qwen3-coder:16k
```

The harness prints the installed local model inventory first. It writes raw outputs and JSON metadata beneath:

`research/friends/round3/local_runs/`

Do not show one model the other model's response. The harness does not do so.

## Status discipline

- A committed harness is **IMPLEMENTED CANDIDATE**.
- Successful Python syntax validation off-host is **not** local inference verification.
- A Mac run that reaches Ollama and writes a raw response is **HOST EXECUTED**.
- A raw response plus metadata/hash is **RAW FROZEN LOCAL**.
- It becomes an official Pass A participant only after contamination status and input identity are reviewed.

No convergence analysis should begin until the chosen blind cohort is frozen.
