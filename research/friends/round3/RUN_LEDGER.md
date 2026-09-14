# FRIENDS Round 3 — Run Ledger

This ledger records experiment execution status. A run is not considered an independent result until its raw response is preserved and contamination status is recorded.

| Run ID | Pass | Participant | Status | Contamination | Input frozen | Raw response preservation | Eligible for blind scoring |
|---|---|---|---|---|---|---|---|
| R3-A-OPENAI-001 | A | OpenAI / ChatGPT | NOT RUN | Must use fresh context | Yes | No | Pending |
| R3-A-CLAUDE-001 | A | Anthropic / Claude | NOT RUN | Unknown until run | Yes | No | Pending |
| R3-A-GEMINI-001 | A | Google / Gemini | NOT RUN | Unknown until run | Yes | No | Pending |
| R3-A-GROK-001 | A | xAI / Grok | NOT RUN | Unknown until run | Yes | No | Pending |
| R3-A-DEEPSEEK-001 | A | DeepSeek | NOT RUN | Unknown until run | Yes | No | Pending |
| R3-A-PERPLEXITY-001 | A | Perplexity Computer | RAW HASH FROZEN | LOW (self-report) | Claimed canonical Pass A | Attachment + SHA-256 frozen | PROVISIONAL YES |
| R3-A-LLAMA-001 | A | Local Llama | NOT RUN | Unknown until run | Yes | No | Pending |
| R3-A-QWEN-001 | A | Local Qwen | NOT RUN | Unknown until run | Yes | No | Pending |
| R3-A-CHAT-CAL-001 | A | Current ChatGPT orchestration thread | CALIBRATION ONLY | CONTAMINATED: challenge designer + architecture exposure | Yes | Not yet | No |

## Status vocabulary

`NOT RUN` → `RUNNING` → `RAW HASH FROZEN` / `RAW FROZEN` → `NORMALIZED` → `ADJUDICATED`

`RAW HASH FROZEN` means the exact returned artifact has been hashed and preservation metadata committed, but a byte-for-byte repository copy of the raw body is not yet present. The hash and original attachment remain the evidence anchor.

Exception statuses:

- `CALIBRATION ONLY`
- `CONTAMINATED`
- `INVALID`
- `PARTIAL`
- `RE-RUN REQUIRED`

## Freeze rule

No Pass A participant may see another Pass A response before its own raw response is frozen or raw-hash-frozen. Pass C begins only after the chosen Pass A/Pass B cohort is frozen.

## First received blind run

`R3-A-PERPLEXITY-001` was received 2026-09-14. Its response self-reports no web access, no repository access, no other HumanOS material, and low contamination. Runtime-attested model identity and runtime-side verification of the input bytes remain UNKNOWN. Substantive analysis is intentionally held until the blind cohort is complete.
