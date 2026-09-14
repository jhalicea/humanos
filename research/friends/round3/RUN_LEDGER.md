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
| R3-A-LLAMA-001 | A | Local Llama | HARNESS READY / NOT RUN | Fresh Ollama request planned | Frozen local text pair | No | Pending |
| R3-A-QWEN-001 | A | Local Qwen | HARNESS READY / NOT RUN | Fresh Ollama request planned | Frozen local text pair | No | Pending |
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

The research branch now contains `run_local_pass_a.py` and `LOCAL_PASS_A_PROTOCOL.md`. These are **IMPLEMENTED CANDIDATE / HOST VERIFICATION REQUIRED**. They use fresh loopback Ollama requests and record model digest, context capacity, input hashes, raw output hashes, and runtime metadata. No local model result is claimed until the Mac executes the harness.

## Calibration runs

### R3-A-OPENAI-CAL-001
Received 2026-09-14. The response self-reports GPT-5.6 Sol / OpenAI, no web access, no repository inspection, no code execution, but explicitly reports prior HumanOS-related material in ambient conversation context and therefore assigns itself MEDIUM contamination risk. It states that it did not seek or rely on that material and saw no other FRIEND answer. After freeze, the human operator clarified that the chat was started in Incognito. That UI provenance is preserved but does not override the model's own contamination disclosure. The original attachment SHA-256 is frozen. This run is retained for later calibration comparison and is excluded from blind-panel scoring.
