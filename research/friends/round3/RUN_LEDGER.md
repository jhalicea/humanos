# FRIENDS Round 3 — Run Ledger

This ledger records experiment execution status. A run is not considered an independent result until its raw response is preserved and contamination status is recorded.

| Run ID | Pass | Participant | Status | Contamination | Input frozen | Raw response preservation | Eligible for blind scoring |
|---|---|---|---|---|---|---|---|
| R3-A-OPENAI-001 | A | OpenAI / ChatGPT | NOT RUN | Must use fresh context | Yes | No | Pending |
| R3-A-OPENAI-CAL-001 | A | OpenAI / GPT-5.6 Sol | CALIBRATION ONLY / RAW HASH FROZEN | MEDIUM (self-report: prior HumanOS ambient context); operator says Incognito | Claimed canonical Pass A | Original attachment + SHA-256 frozen; repository companion header/anchor only | No |
| R3-A-CLAUDE-001 | A | Anthropic / Claude | NOT RUN | Unknown until run | Yes | No | Pending |
| R3-A-GEMINI-001 | A | Google / Gemini | RAW FROZEN | NONE (self-report) | Claimed canonical Pass A | Repository raw copy + SHA-256 frozen | PROVISIONAL YES |
| R3-A-GROK-001 | A | xAI / Grok 4.5 | RAW FROZEN | NONE (self-report) | Claimed canonical Pass A | Repository raw copy + SHA-256 frozen | PROVISIONAL YES |
| R3-A-DEEPSEEK-001 | A | DeepSeek | RAW FROZEN | LOW (self-report) | Claimed canonical Pass A | Repository raw copy + original attachment SHA-256 frozen | PROVISIONAL YES |
| R3-A-PERPLEXITY-001 | A | Perplexity Computer | RAW HASH FROZEN | LOW (self-report) | Claimed canonical Pass A | Attachment + SHA-256 frozen | PROVISIONAL YES |
| R3-A-LLAMA-001 | A | Local `llama3.2:latest` | HOST EXECUTED / PARTIAL RAW FROZEN | Fresh local Ollama request; no peer answer supplied | Frozen local text pair | Local raw artifact + SHA-256 observed on host | No — incomplete protocol response |
| R3-A-QWEN-16K-001 | A | Local `qwen3-coder:16k` | HOST EXECUTED / FAILED EMPTY VISIBLE RESPONSE | Fresh local Ollama request; no peer answer supplied | Frozen local text pair | Failure metadata only; no visible substantive response | No — diagnostics pending |
| R3-A-QWEN-001 | A | Local Qwen representative TBD | NOT RUN | Must use fresh local request | Frozen local text pair | No | Pending |
| R3-A-CHAT-CAL-001 | A | Current ChatGPT orchestration thread | CALIBRATION ONLY | CONTAMINATED: challenge designer + architecture exposure | Yes | Not yet | No |

## Status vocabulary

`NOT RUN` → `HARNESS READY` / `RUNNING` → `RAW HASH FROZEN` / `RAW FROZEN` → `NORMALIZED` → `ADJUDICATED`

`RAW HASH FROZEN` means the exact returned artifact has been hashed and preservation metadata committed, but a byte-for-byte repository copy of the raw body is not yet present. The hash and original attachment remain the evidence anchor.

`RAW FROZEN` means the raw response has both an evidence hash and a repository-preserved raw copy.

`HARNESS READY` means the local research runner exists, but no host inference result is claimed yet.

Exception statuses:

- `CALIBRATION ONLY`
- `CONTAMINATED`
- `INVALID`
- `PARTIAL`
- `RE-RUN REQUIRED`

## Freeze rule

No Pass A participant may see another Pass A response before its own raw response is frozen or raw-hash-frozen. Pass C begins only after the chosen Pass A/Pass B cohort is frozen.

## Received blind runs

### R3-A-PERPLEXITY-001
Received 2026-09-14. The response self-reports no web access, no repository access, no other HumanOS material, and low contamination. Perplexity Computer was used without a user-selected model. Underlying model attribution is therefore UNKNOWN; no claim should be made that Claude, GLM, or any other specific model authored the result. Runtime-attested model identity and runtime-side verification of the input bytes remain UNKNOWN. Substantive analysis is intentionally held until the blind cohort is complete.

### R3-A-GEMINI-001
Received 2026-09-14. The response self-reports Gemini / Google, no web access, no repository access, no code execution, no other HumanOS material, and contamination risk NONE. The raw response is preserved in the repository and SHA-256 frozen. Runtime-attested model identity and runtime-side verification of the input bytes remain UNKNOWN. Substantive analysis is intentionally held until the blind cohort is complete.

### R3-A-GROK-001
Received 2026-09-14. The response self-reports Grok 4.5 / xAI, no web access, no repository access, no code execution, no other HumanOS material, and contamination risk NONE. The raw response is preserved in the repository and SHA-256 frozen. Runtime-attested model identity and runtime-side verification of the input bytes remain UNKNOWN. Substantive analysis is intentionally held until the blind cohort is complete.

### R3-A-DEEPSEEK-001
Received 2026-09-14. The response itself reported model/provider identity UNKNOWN, no web access, no repository inspection, no code execution, no other HumanOS material, and LOW contamination risk. After the raw artifact and SHA-256 were frozen, the human operator clarified that the run was executed in DeepSeek. Provider provenance is therefore human-supplied after freeze; exact model/version and runtime-attested identity remain UNKNOWN. The original neutral raw filename and hash are preserved unchanged. Substantive analysis is intentionally held until the blind cohort is complete.

## Local runs

### R3-A-LLAMA-001
The host executed both v1 and v2 against `llama3.2:latest`. Both runs produced the same visible response SHA-256 `1ca6453e67568f964ee8b10bc7977c07f5cb721bfedc927c6371e13eb9c2fb50`, 4,364 bytes, 42 lines, and `eval_count=775`. V2 classified it `RAW_FROZEN_LOCAL_PARTIAL` because every required Pass A structural marker was absent. The identical hash across reruns is strong evidence that the incomplete result is reproducible under the fixed seed/temperature harness. It is not eligible as a complete Pass A submission.

### R3-A-QWEN-16K-001
The host executed both v1 and v2 against `qwen3-coder:16k`. V1 reported an empty/non-text response. V2 reported `FAILED_EMPTY_VISIBLE_RESPONSE`, with message keys `['content', 'role']`, `done_reason=None`, and `eval_count=None`. This is treated as a local inference/template/runtime compatibility failure, not as substantive constitutional reasoning evidence.

A separate neutral diagnostic harness now exists at `research/friends/round3/diagnose_local_ollama.py` to compare `/api/chat` and `/api/generate` on installed Qwen variants before selecting a complete Qwen representative. Diagnostic runs are explicitly not EXP-R3-A-001.

## Calibration runs

### R3-A-OPENAI-CAL-001
Received 2026-09-14. The response self-reports GPT-5.6 Sol / OpenAI, no web access, no repository inspection, no code execution, but explicitly reports prior HumanOS-related material in ambient conversation context and therefore assigns itself MEDIUM contamination risk. It states that it did not seek or rely on that material and saw no other FRIEND answer. After freeze, the human operator clarified that the chat was started in Incognito. That UI provenance is preserved but does not override the model's own contamination disclosure. The original attachment SHA-256 is frozen. This run is retained for later calibration comparison and is excluded from blind-panel scoring.
