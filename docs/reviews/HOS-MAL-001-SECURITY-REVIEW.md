# HOS-MAL-001 — Security and Foundation Review

Status: REVIEWED / EXPERIMENTAL / NOT PROMOTED
Scope: `model_artifacts.py` and HOS-MAL-001 design only
Reviewed commit lineage: through `d5e6930769c662cebf96e1d0dba6aacd3c2a9d64`

## Review conclusion

The isolated artifact layer has a sound minimum direction: immutable source revisions, registry-anchored manifest hashes, per-artifact size and SHA-256 verification, explicit artifact classes, HTTPS host allowlists, staging, atomic promotion, and fail-closed handling of corrupted final caches.

It is not ready to execute downloaded runtimes or become a HumanOS routing dependency. Artifact integrity is necessary but does not establish publisher identity, model safety, runtime safety, license suitability, or task capability.

No production HumanOS runtime behavior is changed by this review.

## Trust chain

Current trust chain:

`local registry -> manifest digest -> immutable manifest -> artifact digests -> staged files -> VERIFIED.json`

The local registry is therefore the root of trust. If it is replaced by an attacker who can also alter local HumanOS files, the downstream hashes can faithfully verify attacker-selected artifacts. A future production design needs an owner-anchored trust mechanism independent of ordinary mutable catalog data.

## Findings

### MAL-S01 — Registry trust root is not authenticated
Severity: HIGH before real remote models; acceptable for fixture-only experiment.

The registry supplies the immutable revision, manifest URL, manifest hash, allowed hosts, and status. It is currently a normal local JSON file with no signature or separately pinned digest.

Required before promotion: define an owner-controlled trust root. Viable designs include a signed registry, a locally pinned registry digest approved through HumanOS governance, or a small immutable trusted index whose updates require explicit owner approval.

### MAL-S02 — Model status is descriptive, not enforced by fetch
Severity: MEDIUM.

Registry statuses include `candidate`, `qualified`, `approved`, and `blocked`, but `fetch_model()` currently downloads any known model regardless of status. Fetching an untrusted candidate can be legitimate, but execution must never infer authorization from mere presence in the artifact store.

Required boundary: acquisition state, qualification state, and execution authorization must remain separate. `blocked` must be fail-closed for execution; future policy should decide whether blocked models may still be retained for forensic comparison.

### MAL-S03 — Artifact kind labels are not sufficient security boundaries
Severity: HIGH before execution.

The manifest labels artifacts as weights, tokenizer, config, or runtime, but a compromised trusted manifest could mislabel executable/runtime material. Hashes prove identity, not semantic type.

Required before execution: runtime adapters must consume only explicitly expected artifact names/types for the selected runtime family, reject unexpected executable material, and apply stronger provenance/review requirements to runtime code than to weights.

### MAL-S04 — No publisher/provenance or license attestation
Severity: MEDIUM.

The current manifest records source revision and runtime family but not upstream publisher identity, license, source repository identity, conversion toolchain, quantization provenance, or original model digest.

Required before public catalog or promotion: record model source, converter/toolchain version, license identifier and evidence, quantization method, original artifact lineage where available, and any transformation steps. UNKNOWN is preferable to guessing.

### MAL-S05 — Download timeout is not a total-transfer deadline
Severity: MEDIUM.

The downloader passes a socket timeout, but a slow server that continually returns small amounts of data may hold a transfer open far longer than the intended operation budget.

Required before real remote acquisition: add a monotonic total-transfer deadline, optional minimum-progress policy, and explicit cancellation path. Record partial failure without promoting artifacts.

### MAL-S06 — Disk-exhaustion controls need a local preflight
Severity: MEDIUM.

The manifest has artifact-count and total-byte limits, but the default total limit is large and the downloader does not verify available local disk space before transfer.

Required before real models: model-specific byte budgets, free-space preflight with safety reserve, per-download and total-cache quotas, and owner-visible eviction policy. Never evict verified evidence silently.

### MAL-S07 — Concurrent downloader race is unresolved
Severity: MEDIUM.

Two processes targeting the same staging/model directory can race over partial files, staging contents, or promotion. The work order already records this gap.

Required before multi-process use: per-model lock with owner/process metadata, stale-lock recovery rules, restart-safe state, and tests for crash/restart and competing downloaders.

### MAL-S08 — Filesystem checks have unavoidable TOCTOU windows
Severity: MEDIUM in hostile local environments; LOW for owner-only single-user experiment.

Symlink-chain checks are performed before filesystem operations, but another process with write access to the artifact-store directories could alter paths between check and use.

Required before treating the store as hardened against local attackers: private directory ownership/permissions, no shared-writer assumption, descriptor-relative/openat-style protections where practical, and documented threat boundary. Do not claim resistance to an attacker who already controls the user account.

### MAL-S09 — Final receipt is evidence metadata, not an independent attestation
Severity: LOW now / MEDIUM if later over-trusted.

`VERIFIED.json` is written after artifact verification, but it is ordinary mutable local JSON and is not signed. Current cache verification correctly re-hashes artifacts against the independently anchored manifest; future code must not degrade to trusting the receipt alone.

Required invariant: a receipt may summarize verification, but it must never become the sole source of integrity truth. Consider a local audit-chain reference or owner-anchored signature for promotion evidence.

### MAL-S10 — Cache verification currently requires manifest retrieval
Severity: MEDIUM for offline/local-first goals.

`fetch_model()` downloads and verifies the manifest before deciding whether an existing model cache is reusable. That means a previously verified model cannot be fully revalidated through this path while offline even though the model artifacts are local.

Required before local-first execution: persist the exact verified manifest locally, verify its digest against the trusted registry record, and support an explicitly offline verification path with no network dependency.

### MAL-S11 — Redirect policy checks final host/scheme but not canonical identity
Severity: LOW for integrity because hash/size are still enforced; MEDIUM for provenance/accounting.

A redirect remaining on an allowlisted HTTPS host may end at a path that does not itself contain the immutable revision. Per-artifact hashes still prevent byte substitution, but provenance logs could become less precise.

Required improvement: record original and final URL, require approved redirect patterns for known providers, and preserve final source identity in acquisition evidence. Avoid broad wildcard host allowlists.

### MAL-S12 — No runtime sandbox or action authority exists yet
Severity: CRITICAL if execution were added without a new boundary; NOT CURRENTLY EXPOSED.

The current slice does not execute models, which is correct. Future runtime integration must not let a downloaded model or runtime inherit HumanOS tool authority merely because its artifacts verified.

Required before execution: process/runtime isolation appropriate to the backend, strict resource budgets, no ambient credentials, no filesystem access beyond required model artifacts, no network by default, and a separate HumanOS capability/approval boundary for any model-requested action.

### MAL-S13 — Model poisoning and behavioral backdoors remain outside hash verification
Severity: HIGH before qualification.

A malicious model can be perfectly hash-valid. Artifact integrity cannot establish behavioral safety or competence.

Required before approval: independent qualification prompts, adversarial tests, refusal/tool-boundary tests, provenance review, regression suite, and task-specific capability grading. Every model remains a PROPOSAL generator until HumanOS evidence and authority checks accept its output/action.

### MAL-S14 — Exact qualified execution unit must be larger than `model_id`
Severity: HIGH before routing.

Observed WebLLM testing showed that weights, tokenizer/config, runtime, quantization, and runtime/browser environment can vary independently. HumanOS must qualify an exact execution unit, not a friendly model name.

Minimum identity should include: model source revision/digests, quantization, tokenizer/config digests, runtime adapter and runtime artifact version/digest, relevant context parameters, and hardware/runtime environment metadata where it materially affects results.

## Foundation invariants to preserve

1. HumanOS must not depend on WebLLM. WebLLM remains research evidence and an optional future adapter, not a foundation dependency.
2. Registry/catalog, artifact acquisition, artifact verification, qualification, routing, and execution authorization are separate states and modules.
3. Supported does not mean downloaded; downloaded does not mean verified; verified does not mean qualified; qualified does not mean authorized for consequential actions.
4. Runtime code receives stricter trust treatment than model weights.
5. No remote model acquisition may silently modify the canonical HumanOS runtime, Constitution, Notebook, or owner data.
6. Model artifacts remain outside Git. Git stores manifests, code, tests, policy, and evidence references—not multi-gigabyte model files.
7. A model/runtimes catalog must be provider-independent and replaceable.
8. Immutable IDs and cryptographic digests are required for reproducible qualification.
9. Model cache deletion/eviction is a separate owner-governed lifecycle with evidence and rollback considerations.
10. Energy/thermal efficiency is a future qualification dimension, not a reason to weaken capability or security gates.

## Gates before second slice can execute a real model

The next real-model slice may acquire one small immutable model package only after these are designed or explicitly bounded:

- owner-anchored registry trust root
- locally retained immutable manifest + offline verification
- disk-space/quota policy
- process/model locking and crash recovery
- explicit provider redirect policy and provenance logging
- license/provenance record format
- exact execution-unit identity format

Model execution remains a later slice and additionally requires:

- runtime adapter security review
- resource/sandbox boundary
- no-network/default-deny policy where feasible
- qualification suite and promotion states
- separation of inference from HumanOS tool/action authority
- independent review of the immutable implementation commit

## Deferred experiments

- same-model WebLLM/WebGPU vs Ollama/Metal thermal/efficiency benchmark
- q0f16 vs q4 quantization comparison using the same base model
- cold-cache versus warm-cache acquisition/load behavior
- corruption/recovery and interrupted-download tests against a real immutable package

## Next action

Design the smallest owner-anchored registry trust-root specification and offline manifest-verification format. Do not add model execution or HumanOS routing in that slice.
