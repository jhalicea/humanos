# HumanOS Model Registry v1 — Candidate

Status: **CANDIDATE / DESCRIPTIVE ONLY**

The registry separates the identity of an intelligence/model from the runtime profile used to invoke it. This prevents an Ollama alias, context-window variant, system-prompt wrapper, parser, or temperature change from being miscounted as a new intelligence.

## Identity hierarchy

`provider -> model/weights -> runtime profile -> qualification evidence -> human decision`

Qualification never grants authority by itself. HINE and other reviews produce evidence. HumanOS does not automatically naturalize, promote, route to, or authorize a model from registry data.

## Current local evidence

The observed Qwen3-Coder tags `qwen3-coder:30b`, `qwen3-coder-local:16k`, and `qwen3-coder:16k` share the same observed underlying Ollama weights blob and therefore belong to one model identity with distinct runtime profiles. The custom `qwen3-coder:16k` profile showed an end-to-end visible-response failure on the structured HumanOS review despite generating tokens; the local-16k profile completed the review. This is why qualification attaches to the profile as well as the model.

Llama 3 and Llama 3.2 remain separate candidates. Their exact metadata and qualification evidence must be captured rather than inferred.

## Our model friends

HumanOS remains provider-neutral. Model/service roles are advisory and replaceable:

- ChatGPT: first independent analysis, task division, comparison, integration and final review.
- Gemini: architecture and large-context review.
- DeepSeek: coding/debugging and implementation review.
- Grok: adversarial challenge and edge cases.
- Claude: security, architecture and high-risk review.
- Local HumanOS/Ollama models: private/routine work, checks, tests, records and offline operation.

Every model response should preserve provider/model/version when exposed, timestamp, task/role, usage/latency when exposed, estimates explicitly labelled, quality/corrections and relevant repository references. UNKNOWN is preferred to guessing. Outputs remain PROPOSAL until verified and promoted by the human.

## Course integration

Model qualification is also practical evidence for the **AI Systems Engineering & HumanOS** course, especially `ai.systems`, `ai.evaluation`, and `ai.security`. It must not automatically award mastery. Evidence from these experiments can be recorded and later assessed by the Adaptive Mastery Engine.

The current AI lesson continuation remains **Transformer Architecture From the Inside — How one sentence actually moves through an LLM**: tokenization -> embedding -> position representation -> Q/K/V -> attention scores -> softmax -> weighted values -> multi-head attention -> residual stream -> MLP/feed-forward -> repeated Transformer layers -> logits -> token selection; then training-time learned parameters versus inference-time computation and what HumanOS controls versus the model/provider.

The current Cyber/DFIR continuation remains the Windows/Sysmon Event ID 3 investigation. Course continuity must not be overwritten by model-registry work.

## Next bounded implementation

1. Run the same canonical qualification prompt against Llama 3 and Llama 3.2.
2. Capture exact model/profile metadata and benchmark telemetry.
3. Attach evidence to registry identities.
4. Compare results without auto-routing or auto-promotion.
5. Use the evidence to design a later human-controlled picker/router.
