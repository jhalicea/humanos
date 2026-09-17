# HOS-MAL-001 — Verified Sharded Model Artifact Loader

Status: EXPERIMENTAL / NOT PROMOTED
Branch: `experiment/webllm-inspired-model-loader`
Owner approval: authorized to build the isolated experiment; no merge or release approval implied.

## Outcome

Prototype a HumanOS-owned model artifact layer inspired by the useful parts of WebLLM without depending on WebLLM itself. The slice proves registry lookup, immutable manifest identity, sharded artifact download, cache reuse, SHA-256 verification, staging, and a final verification receipt. It does not execute a model or alter HumanOS routing.

## Baseline

Branch created from HumanOS `runtime-0.1` at commit `9ddc6477bba70dd4c86104a0565da848d7cbacff`.
Existing repository guidance requires the standard-library test suite and keeps real Ollama checks separate from simulated model tests.

## Scope

Included:

- local JSON model registry
- exact model ID and immutable 40–64 hex source revision
- manifest URL, expected byte length, and SHA-256 anchored in the registry
- HTTPS-only source URLs containing the immutable revision
- explicit source-host allowlist and redirect/final-host enforcement
- rejection of mutable path segments such as `main`, `master`, `latest`, and `head`
- artifact classes: `weights`, `tokenizer`, `config`, `runtime`
- many sharded weight files per model
- per-artifact expected size and SHA-256
- bounded artifact count and total byte budget
- safe relative artifact paths and path-traversal rejection
- staging directory with `.partial` cleanup on failed transfers
- reuse of already-complete staged shards only after hash and size verification
- final `VERIFIED.json` receipt after all artifacts validate
- fail-closed behavior for corrupted existing final caches

Excluded:

- model execution
- WebLLM dependency
- Ollama replacement
- HumanOS model routing
- automatic qualification or promotion
- signed registry/manifest trust roots
- public model catalog
- browser integration
- HTTP range-resume of partial files
- concurrent downloader locking
- destructive quarantine or automatic repair

## Security model

A remote model is untrusted input until its exact manifest and every artifact are verified. Runtime/WASM artifacts remain distinguishable from weights because executable runtimes deserve a stronger review boundary. A hash proves byte identity, not that a model is safe, unbiased, unpoisoned, or capable.

The prototype refuses:

- mutable upstream refs
- non-HTTPS canonical URLs
- unallowlisted source hosts
- redirects outside the allowlist or HTTPS
- manifest/artifact size mismatches
- SHA-256 mismatches
- path traversal and unsafe artifact names
- unknown manifest fields
- duplicate artifact names
- artifact counts or total sizes beyond configured limits
- silent overwrite of an existing final cache that no longer verifies

## Acceptance criteria

1. A fixture model with at least two weight shards, tokenizer data, and a runtime artifact downloads into staging and is promoted only after all hashes validate.
2. A final verification receipt records model ID, immutable source revision, manifest digest, runtime family, artifact kinds, sizes, and hashes.
3. A second fetch reuses verified cached artifacts rather than downloading the shards again.
4. Manifest tampering fails before artifact download.
5. Weight tampering fails without creating a final model directory.
6. A mutable `main` manifest URL is rejected.
7. A URL missing the immutable revision is rejected.
8. A cross-host redirect is rejected.
9. Manifest path traversal is rejected.
10. Resource-size limits fail closed.
11. A corrupted final cache is not overwritten automatically.
12. Full HumanOS regression suite remains green in CI before promotion consideration.

## Files

- `model_artifacts.py` — isolated registry/manifest/parser/downloader/store implementation.
- `tests/test_model_artifacts.py` — network-free fixture tests with simulated HTTPS responses.
- `docs/reviews/HOS-MAL-001-SECURITY-REVIEW.md` — foundation/security review and promotion gates.

## Rollback

This slice is not wired into `server.py` or the runtime. Rollback is branch deletion or restoring the experimental files; the production runtime is unchanged.

## Security/foundation review status

Foundation review completed for this slice. The review found that the current experiment is suitable as an isolated artifact-acquisition prototype but is not ready for model execution or routing.

The review preserves these major gates before any real execution path:

- authenticate or owner-anchor the registry trust root
- keep acquisition, verification, qualification, routing, and execution authorization separate
- retain the exact immutable manifest locally for offline verification
- enforce disk-space/cache quotas and safe eviction policy
- add concurrent-download locking and crash/restart recovery
- strengthen provider redirect/provenance logging
- record license, publisher, conversion, and quantization provenance
- identify the full qualified execution unit, not only the friendly model ID
- review runtime adapters as higher-trust executable code
- sandbox/default-deny runtime access before model execution
- keep HumanOS tool/action authority separate from inference
- independently review immutable implementation commits before promotion

See `docs/reviews/HOS-MAL-001-SECURITY-REVIEW.md` for detailed findings MAL-S01 through MAL-S14.

## Deferred qualification experiment — runtime thermal and efficiency comparison

Status: DEFERRED / DO NOT IMPLEMENT IN THIS SLICE.

Purpose: determine whether the lower observed heat during the WebLLM experiment came primarily from the smaller model, the WebGPU runtime, or both. This is qualification evidence for future HumanOS runtime selection, not a reason to depend on WebLLM.

Controlled comparison:

- use the exact same small model and quantization in both runtimes where technically possible
- compare WebLLM/WebGPU against Ollama/Metal
- use the same prompt set, context size, generation length, and sampling settings
- record model ID, exact revision, quantization, runtime version, browser/runtime version, and machine state

Measurements:

- prefill tokens/second
- decode tokens/second
- wall-clock latency
- RAM and Apple unified-memory usage
- CPU load
- GPU load
- power/energy draw when measurable with repeatable tooling
- thermal impact and temperature behavior when measurable with repeatable tooling
- sustained-performance behavior and throttling
- answer quality against the same acceptance prompts
- idle/resident behavior after inference stops

Interpretation rules:

- do not compare different model sizes and attribute the result to runtime efficiency
- mark measurements NON-COMPARABLE when runtime settings cannot be normalized sufficiently
- separate observed measurements from inferred causes
- repeat runs enough to identify warm-cache versus cold-start effects
- use local measurements as evidence; marketing benchmarks are context only

Future use: qualification may eventually support energy-aware runtime profiles such as ECO, BALANCED, and PERFORMANCE, but no routing policy is approved by this work order.

## Next action

Design the smallest owner-anchored registry trust-root specification and offline manifest-verification format. Keep it documentation/specification first. Do not add model execution, runtime routing, or a real remote model in that slice.
