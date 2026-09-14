# FRIENDS Round 3 — Run Ledger

This ledger records experiment execution status. A run is not considered an independent result until its raw response is preserved and contamination status is recorded.

| Run ID | Pass | Participant | Status | Contamination | Input frozen | Raw response preservation | Eligible for blind scoring |
|---|---|---|---|---|---|---|---|
| R3-A-OPENAI-001 | A | OpenAI / ChatGPT | NOT RUN | Must use fresh context | Yes | No | Pending |
| R3-A-CLAUDE-001 | A | Anthropic / Claude | NOT RUN | Unknown until run | Yes | No | Pending |
| R3-A-GEMINI-001 | A | Google / Gemini | RAW FROZEN | NONE (self-report) | Claimed canonical Pass A | Repository raw copy + SHA-256 frozen | PROVISIONAL YES |
| R3-A-GROK-001 | A | xAI / Grok 4.5 | RAW FROZEN | NONE (self-report) | Claimed canonical Pass A | Repository raw copy + SHA-256 frozen | PROVISIONAL YES |
| R3-A-DEEPSEEK-001 | A | DeepSeek | NOT RUN | Unknown until run | Yes | No | Pending |
| R3-A-PERPLEXITY-001 | A | Perplexity Computer | RAW HASH FROZEN | LOW (self-report) | Claimed canonical Pass A | Attachment + SHA-256 frozen | PROVISIONAL YES |
| R3-A-LLAMA-001 | A | Local Llama | NOT RUN | Unknown until run | Yes | No | Pending |
| R3-A-QWEN-001 | A | Local Qwen | NOT RUN | Unknown until run | Yes | No | Pending |
| R3-A-CHAT-CAL-001 | A | Current ChatGPT orchestration thread | CALIBRATION ONLY | CONTAMINATED: challenge designer + architecture exposure | Yes | Not yet | No |

## Status vocabulary

`NOT RUN` → `RUNNING` → `RAW HASH FROZEN` / `RAW FROZEN` → `NORMALIZED` → `ADJUDICATED`

`RAW HASH FROZEN` means the exact returned artifact has been hashed and preservation metadata committed, but a byte-for-byte repository copy of the raw body is not yet present. The hash and original attachment remain the evidence anchor.

`RAW FROZEN` means the raw response has both an evidence hash and a repository-preserved raw copy.

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
