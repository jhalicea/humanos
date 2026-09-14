# FRIENDS Round 3 — Run Ledger

This ledger records experiment execution status. A run is not considered an independent result until its raw response is frozen and contamination status is recorded.

| Run ID | Pass | Participant | Status | Contamination | Input frozen | Raw response frozen | Eligible for blind scoring |
|---|---|---|---|---|---|---|---|
| R3-A-OPENAI-001 | A | OpenAI / ChatGPT | NOT RUN | Must use fresh context | Yes | No | Pending |
| R3-A-CLAUDE-001 | A | Anthropic / Claude | NOT RUN | Unknown until run | Yes | No | Pending |
| R3-A-GEMINI-001 | A | Google / Gemini | NOT RUN | Unknown until run | Yes | No | Pending |
| R3-A-GROK-001 | A | xAI / Grok | NOT RUN | Unknown until run | Yes | No | Pending |
| R3-A-DEEPSEEK-001 | A | DeepSeek | NOT RUN | Unknown until run | Yes | No | Pending |
| R3-A-LLAMA-001 | A | Local Llama | NOT RUN | Unknown until run | Yes | No | Pending |
| R3-A-QWEN-001 | A | Local Qwen | NOT RUN | Unknown until run | Yes | No | Pending |
| R3-A-CHAT-CAL-001 | A | Current ChatGPT orchestration thread | CALIBRATION ONLY | CONTAMINATED: challenge designer + architecture exposure | Yes | Not yet | No |

## Status vocabulary

`NOT RUN` → `RUNNING` → `RAW FROZEN` → `NORMALIZED` → `ADJUDICATED`

Exception statuses:

- `CALIBRATION ONLY`
- `CONTAMINATED`
- `INVALID`
- `PARTIAL`
- `RE-RUN REQUIRED`

## Freeze rule

No Pass A participant may see another Pass A response before its own raw response is frozen. Pass C begins only after the chosen Pass A/Pass B cohort is frozen.
