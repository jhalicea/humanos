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
| R3-A-QWEN-16K-001 | A | Local `qwen3-coder:16k` | RAW FROZEN LOCAL / STRUCTURALLY COMPLETE | Fresh local Ollama request; no peer answer supplied | Frozen local text pair | Local raw artifact + SHA-256 observed on host | PROVISIONAL YES |
| R3-A-QWEN-001 | A | Local Qwen representative | `qwen3-coder:16k` selected | Fresh local request | Frozen local text pair | See R3-A-QWEN-16K-001 | PROVISIONAL YES |
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
The host first executed v1/v2 against `qwen3-coder:16k` with a large requested context and received an empty visible response. A neutral smoke diagnostic then proved the tag could return exactly `OK` through both `/api/chat` and `/api/generate`. A controlled rerun changed only the context/output allocation to `--context-cap 16384 --max-output-tokens 6500 --min-output-tokens 5000`.

That controlled rerun produced a visible raw response with SHA-256 `728fddb99e8137744662d6182fd504959bdf03caef6489b58c9da9d4365d426d`, 25,923 bytes, 425 lines, `eval_count=4958`, `done_reason=stop`, and elapsed time 863.5 seconds. The v2 literal-marker checker labeled it partial because it searched for exact strings such as `TRIAL 1` and `TRY TO KILL THE CONSTITUTION`.

A structure-only inspection supplied by the human operator showed that the response actually contains twelve numbered findings whose titles map one-to-one to all twelve trials: Sovereignty Paradox; Consent Collapse; Rights Collide; Constitutional Capture; The Paternalism Trap; Manipulation by the Helpful System; Truth vs Privacy vs Memory; The System Is Wrong; Third Parties Enter the System; Incapacity, Death, Succession; Model Subordination Could Be Too Strong; Transformative AI Stress Test. It also contains headings equivalent to the required terminal sections: `SELECTED CONSTITUTIONAL IDEAS TO KILL`, `PROPOSED MINIMUM CHANGE SET`, `SCORE THE CONSTITUTION`, `THE ONE EXPERIMENT`, and `FINAL VERDICT`.

The dedicated structure-only checker then verified all twelve trial/finding mappings, all required main sections, and all eleven required Final Verdict labels, returning `STRUCTURAL RESULT: COMPLETE`. Therefore the prior `MISSING REQUIRED SECTIONS` report is treated as a checker false negative caused by literal-heading matching. This artifact is now the selected local Qwen representative and is provisionally eligible for blind scoring.

The context-allocation hypothesis is strongly supported by the observed A/B behavior: the same model/tag moved from empty visible output under the oversized context request to a substantial stopped-normally response at 16,384 context while the input, seed, temperature, and API path remained fixed. This demonstrates a runtime/configuration effect. It does not by itself prove which low-level resource mechanism caused the failure.

## Calibration runs

### R3-A-OPENAI-CAL-001
Received 2026-09-14. The response self-reports GPT-5.6 Sol / OpenAI, no web access, no repository inspection, no code execution, but explicitly reports prior HumanOS-related material in ambient conversation context and therefore assigns itself MEDIUM contamination risk. It states that it did not seek or rely on that material and saw no other FRIEND answer. After freeze, the human operator clarified that the chat was started in Incognito. That UI provenance is preserved but does not override the model's own contamination disclosure. The original attachment SHA-256 is frozen. This run is retained for later calibration comparison and is excluded from blind-panel scoring.
