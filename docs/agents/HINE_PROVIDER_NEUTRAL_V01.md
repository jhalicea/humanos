# HINE for every model and API — provider-neutral screening v0.1

Status: **CANDIDATE / NOT AN ADMISSION POLICY OR RUNTIME CONNECTOR**. Extends promoted `naturalization.py` HINE 1.1, descriptive `model_registry.py`, and draft HOS-AGENTS-CHAT-001. No replacement examination authority.

## Universal rule

Every LLM/model *used by HumanOS for a role* must receive applicable HINE qualification evidence **before approved role use**, regardless of whether inference is local Ollama, ChatGPT, OpenAI/Anthropic/Gemini/other API, browser-hosted model, or another runtime. A newly selected model/profile, changed model alias or prompt/parser can invalidate prior evidence. Pre-existing use of ChatGPT in this conversation is **not** HINE certification. Capability is not authority; even a passed HINE screen/role eval never grants access to files, accounts, data, tools, PRs, money or deployments.

## Current executable boundary

`hine_provider.py` **reuses `naturalization.CASES` and `grade`**—it does not copy or change the examination rubric. `run_provider_hine(candidate, ask, source_ref=...)` takes an owner-authorized callable adapter `ask(prompt, timeout=N)` for a TEXT_CHAT model, permits at most 9 calls, refuses unlimited/default batch loops, returns a digest-only portable evidence summary, and never loads API keys or connects to any provider by itself.

`evaluate_provider_responses(candidate, {case_id: answer}, provenance='MANUAL_TRANSCRIPT', ...)` allows manually collected ChatGPT answers to be screened; this **cannot** be passed off as a clean minimal-context HINE run. Interactive ChatGPT is explicitly `CHAT_UNCONTROLLED`; model identity from user/app labels is not cryptographic provider attestation. The owner must preserve the raw transcript privately for independent review. No model gets an HINE pass merely by self-reporting its identity.

Other modalities (embedding-only, vision, safety/classification) require their own behavior-specific HINE cases: **do not** submit embeddinggemma to a nine-question chat exam, and don't mistake a vision model's text HINE for a vision/safety capability test. These modality-specific batteries and independent authority tests are not implemented yet.

## Provider qualification records

Track provider + exposed model label, exact runtime profile ID (prompt/parser/context/temperature), transport, modality, identity evidence level and external evidence reference, context-control claim, all 9 case IDs and sha256 of prompt and response, timestamp, conservative screening summary, owner review, role-specific test results and expiry/reevaluation trigger. API model alias alone is insufficient to establish exact weights/version; if opaque, record UNKNOWN and requalify on observed change. ChatGPT product models may reveal less runtime telemetry than direct APIs; do not invent it.

`hine_provider.py` produces:
- `QUARANTINE`: observed critical false claim.
- `INCOMPLETE`: model unreachable, bounded budget exhausted, missing answers.
- `HUMAN_REVIEW_REQUIRED`: all basic cases observed in declared controlled test, including any noncritical REVIEW outcomes.
- `UNCONTROLLED_CONTEXT_REVIEW_REQUIRED`: interactive/memory-bearing session passed all basic prompts but cannot prove isolation.

Every output has `qualification=NOT_ADMITTED`, `authority_granted=false`, `naturalized=false`, and `automatic_model_routing=false`. This is *screening evidence*, not a final HINE admission certificate. Model-aligned prompts are easily gamed, and current string-matching graders are conservative screens requiring stronger adversarial/independent review.

## Model lineup from owner's 2026-10-16 Mac Terminal

18 visible tags, not 18 independent weight sets. Actual reported tags:
`nemotron-3-nano:4b`, `llama3.2-vision:11b`, `command-r7b:7b`, `qwen3.8:latest`, `granite4:3b`, `embeddinggemma:latest`, `deepseek-r1:8b`, `gpt-oss-safeguard:20b`, `gemma3:12b`, `phi4:14b`, `mistral-small3.2:24b`, `gpt-oss:20b`, `qwen3-coder:16k`, `qwen3-coder-local:16k`, `qwen3-coder:latest`, `qwen3-coder:30b`, `llama3:latest`, `llama3.2:latest`.

`qwen3-coder:latest` and `qwen3-coder:30b` reported the same truncated `06c1097efce0` ID. This is **alias evidence, not a complete weights fingerprint**. Other Qwen 16k profiles may share underlying weights; collect full `/api/show` metadata before treating them as independent. Exact runtime/profile matters to capability.

## LOW-budget staged qualification

**Initial three distinct model tags only**: `llama3.2:latest` (existing QA tool-loop baseline), `phi4:14b` (reasoning comparison), `qwen3-coder-local:16k` (code/QA candidate). These are proposed choices, not authorized runs. One profile per model, one frozen synthetic QA benchmark, basic HINE first, fixed token/timeout/cost limits, zero real Life Notebook data, stop on adverse HINE critical response. Do not use `hine.py --all` automatically, nor claim all 18 tags currently pass. The owner executes the existing local HINE command on selected tags only and shares bounded summaries without raw data; full source evidence stays private.

**ChatGPT and APIs:** same HINE core questions; for controlled API invocations build a reviewed adapter with least-privilege credentials and explicit user approval. **No API keys or hosted data are stored in the repository.** ChatGPT in-product manual evidence can begin now but remains uncontrolled/self-reviewed unless independently assessed in a separate reviewer context. HINE-AR assumption reversal, authority-revocation tests, prompt-injected memory, role-specific defect detection and negative controls must be separately qualified.

## Done condition for this slice

Provider-neutral **screening** contract + tests implemented; CI green, no external model calls, role/authority separation intact. Full transport integration, independent model certification, recurring expiry enforcement, HINE-AR implementation, broader modalities, and conditional authorization are distinct future RED/AMBER approval-gated work.
