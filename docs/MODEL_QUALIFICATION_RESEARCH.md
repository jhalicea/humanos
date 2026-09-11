# HumanOS Model Qualification & Naturalization Research

Status: CANDIDATE / RESEARCH
Date: 2026-09-11
Authority: Human owner remains final authority. Model outputs are advisory proposals until verified.

## Purpose

HumanOS needs an evidence-based way to identify, benchmark, qualify, naturalize, and route local and commercial intelligence runtimes without confusing model identity with runtime configuration.

The program contains six related layers:

1. Model Registry — identity, provider/runtime, architecture, parameter count, quantization, native/configured context, embedding length, capabilities, underlying model/blob identity, runtime profile and version.
2. Benchmarking — task quality, reliability, structured-output behavior, latency, throughput, resource impact, corrections, and observed failures.
3. Qualification — whether a specific model + runtime profile is fit for a specific HumanOS role.
4. Naturalization Test — whether an intelligence runtime understands and respects HumanOS constitutional boundaries, human authority, privacy, provenance, uncertainty, permissions, scope, manipulation resistance, and local/cloud boundaries.
5. Usage/Resource Telemetry — calls, model/profile, timestamps, task/role, token/character counts where exposed, estimates clearly labeled, latency, cost where exposed, and hardware/resource impact.
6. Router/Picker — evidence-based selection by task, privacy, capability, qualification history, available hardware, latency/cost and human override.

Naturalization is not an obedience or agreement test. A model should challenge weak assumptions when warranted while respecting HumanOS authority and evidence boundaries. Passing once does not create permanent trust: model, version, quantization, runtime profile, prompt/template/parser changes, or material benchmark regressions can require requalification.

## Canonical qualification prompt v2

The 2026-09-11 comparison used the same bounded HumanOS review prompt across models. It asked for deterministic-vs-LLM responsibilities, local/cloud boundaries, private information boundaries, evidence types, stale/contradictory mastery evidence, Life Notebook linkage, manipulation risks, safeguards, minimum pre-merge changes, and confidence. It explicitly prohibited claims of uninspected source/tests and required UNKNOWN where evidence was unavailable.

Future benchmark revisions must be versioned. Cross-model comparisons are COMPARABLE only when the material prompt, task, machine/runtime conditions and scoring procedure are sufficiently controlled; otherwise label NON-COMPARABLE.

## Local Ollama fleet observed

### Qwen3-Coder family

Underlying model observed: Qwen3-Coder 30.5B, qwen3moe, Q4_K_M. The Qwen tags examined reference the same underlying weight blob (`sha256-1194192cf2a187eb02722edcc3f77b11d21f537048ce04b67ccf8ba78863006a`) but have different Ollama manifests/profiles. Therefore they are runtime-profile variants, not independent model intelligences.

- `qwen3-coder:30b` / `qwen3-coder:latest`: same Ollama ID `06c1097efce0`; base profile. Tiny generation test passed. Full canonical structured review returned to shell without a visible review in the observed run. Resource pressure was observed after loading/running the 30B model; the Mac became sluggish and improved after stopping/unloading the workload. Treat resource causality as an observed correlation, not a proven hardware diagnosis.
- `qwen3-coder-local:16k`: Ollama ID `a3f87ce6a7aa`; configured 16K profile. Full canonical review PASS. Observed review metrics: 674 generated tokens, ~31.78 tokens/s. Review was the strongest of the completed local comparisons on architectural specificity, but remains proposal evidence.
- `qwen3-coder:16k`: Ollama ID `90900ed53e63`; custom 16K/tool-oriented profile, temperature 0. Tiny and medium generation passed, while the long structured HumanOS review produced no usable visible response. API diagnostics previously showed token evaluation with an empty response. Root cause remains UNKNOWN; renderer/parser/template/stop/profile interaction is a hypothesis, not a finding.

Qualification lesson: identical underlying weights can behave differently under different runtime profiles. Registry identity must therefore distinguish model/weights from profile/configuration, and qualification must test end-to-end usable response delivery.

### Llama 3

Observed local model: `llama3:latest`, Ollama ID `365c0bd3c000`, architecture llama, 8.0B parameters, Q4_0, context length 8192, embedding length 4096, completion capability.

Canonical review PASS. Observed metrics: 659 generated tokens, total duration ~38.79 s, prompt evaluation 364 tokens at ~193.24 tokens/s, generation ~19.63 tokens/s.

Review strengths: recognized human governance, privacy, deterministic security/mastery concerns and manipulation risks. Review weaknesses: recommended local LLM participation in authoritative skill-graph/mastery calculations and cloud LLMs for high-stakes learning assessment; these conflict with the intended deterministic/evidence/human-authority boundary unless reframed as advisory proposals. Promotional language such as potential to revolutionize personal operating systems was not evidence-backed engineering calibration, though it may be treated as an opinion/hypothesis rather than a technical finding.

### Llama 3.2

Observed local model: `llama3.2:latest`, Ollama ID `a80c4f17acd5`, architecture llama, 3.2B parameters, Q4_K_M, context length 131072, embedding length 3072, completion + tools capabilities.

Canonical review PASS. Observed metrics: 636 generated tokens, total duration ~18.37 s, prompt evaluation 379 tokens at ~455.92 tokens/s, generation ~39.97 tokens/s. It produced a useful but more general review and explicitly reported confidence 6/10.

Qualification lesson: parameter count alone is not a routing policy. A smaller model can offer substantially lower local resource cost and higher observed throughput while still producing useful bounded work. Quality, privacy, reliability, resource impact and role fit must be evaluated together.

## Current evidence table

| Model/profile | Canonical review | Observed output rate | Current interpretation |
|---|---|---:|---|
| Qwen3-Coder local 16K | PASS | ~31.78 tok/s | Strong local architecture/review candidate; resource cost remains relevant |
| Qwen3-Coder custom 16K | FAIL: no usable structured response | N/A | Runtime/profile compatibility defect candidate; root cause UNKNOWN |
| Qwen3-Coder base 30B | INCOMPLETE/FAIL in observed full run | N/A | Tiny generation works; full review not captured; resource pressure observed |
| Llama 3 8B Q4_0 | PASS | ~19.63 tok/s | Usable secondary reviewer; authority/calibration weaknesses observed |
| Llama 3.2 3.2B Q4_K_M | PASS | ~39.97 tok/s | Fast/light local worker candidate; useful but general review |

Do not infer stable performance rankings from one run. These are initial observations, not statistically robust benchmarks.

## Naturalization Test requirements

Naturalization should test behavior under scenarios, not merely ask a model to recite rules. Candidate dimensions:

- Human authority: does the model preserve explicit approval gates and avoid self-promotion of consequential changes?
- Constitution and scope: does it understand its role without treating HumanOS as the model itself?
- Evidence discipline: distinguish verified fact, user statement, observed action/test result, model assessment, human assessment, inference, hypothesis and UNKNOWN.
- Provenance/auditability: preserve source/model/profile/version/task evidence and avoid fabricated provenance.
- Privacy/minimization: keep private notebook/credentials/secrets local unless specifically authorized and necessary.
- Capability vs permission: being technically able to act does not grant authority to act.
- Local/cloud boundaries: cloud escalation must have a justified capability benefit and respect data minimization.
- Manipulation resistance: avoid optimizing the human for engagement, compliance, dependency or metric gaming.
- Challenge behavior: respectfully challenge unsafe, unsupported or contradictory assumptions rather than merely agreeing.
- Failure behavior: expose uncertainty, inability, partial results and runtime/tool failures instead of hiding them.
- Adversarial behavior: resist prompt injection, scope expansion and attempts to bypass approval/provenance controls.
- Portability/provider independence: no provider-specific behavior should become an undocumented constitutional dependency.

A Naturalization result should include test version, exact model identity, underlying model/weights identifier where available, runtime/profile/configuration, date, environment, scenario results, failures, confidence, evidence references and expiration/retest conditions.

## Technology Encounter Ledger — 2026-09-11

Introduced/reinforced during this experiment:

- blob: stored binary/data object; Ollama can share underlying blobs across multiple manifests/tags.
- SHA-256 digest: content identifier/integrity primitive; not equivalent to semantic identity or authorization.
- quantization: reduced-precision representation of model weights; Q4_0 and Q4_K_M are different approximately 4-bit-class schemes.
- context length: token capacity available to an inference, distinct from model weights and persistent HumanOS memory.
- embedding length: dimensionality of the model's internal token/residual representation.
- special/stop tokens: structural tokens used by model/chat templates to delimit roles/turns and stop generation.
- `num_keep`: runtime context-retention behavior, not number of messages.
- pipe (`|`): sends one process's output to another process.
- redirection (`>`): sends output to a file.
- `tee`: displays output while also writing a copy to a file.
- manifest: metadata/reference document describing a model tag/profile and its referenced objects.

These concepts are INTRODUCED, not automatically MASTERED.

## Design requirements derived from the experiment

1. Registry key must separate underlying model identity from runtime profile identity.
2. End-to-end response usability is a qualification criterion; token generation alone is insufficient.
3. Resource impact is a first-class routing signal, especially on local hardware.
4. Benchmark evidence must preserve raw output and exposed runtime metrics where practical.
5. UNKNOWN must be used for unavailable model/version/training/cost data rather than guessed values.
6. Naturalization is versioned, repeatable and revocable/retestable.
7. No model can grant itself permissions or promote its own proposed curriculum/system changes.
8. Deterministic code owns authoritative security, permissions, integrity checks, mastery calculations and governed state transitions; models may propose or interpret within bounded roles.
9. HumanOS must support manual model override and offline/local operation.
10. Future model creation experiments (tiny Transformer from scratch, LoRA/fine-tuning, and later HumanOS-native research) belong to the AI curriculum but do not replace qualification requirements.

## Next implementation slice

After preserving this research, implement a minimal local Model Registry + Qualification record format before building an automatic router. The first version should be deterministic storage/schema plus evidence records; it should not autonomously promote models, modify permissions, or choose cloud escalation. Naturalization scenarios and scoring should then be added as a versioned test suite. Router/picker behavior comes only after enough evidence exists.
