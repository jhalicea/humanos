# HOS-FND-002 — Cross-Project Engineering Hardening Review

Status: REVIEW CANDIDATE — DOCUMENTATION ONLY
Workspace: WS-HUMANOS
Project: Foundation
Relationship: EXTENDS HOS-FND-001
Branch: foundation/engineering-hardening-review-v1
Baseline: runtime-0.1 @ 2d4b383c6723177a3d1ad6ef3774d79dc8e6b7cd
Owner: Jon Alicea

## Outcome

Capture engineering lessons surfaced while red-teaming BodyFixOS that could strengthen HumanOS without changing verified runtime behavior or reopening promoted Context Engine slices.

## Scope

This slice records reusable engineering principles, maps them to existing HumanOS surfaces, and separates:
- aligned practices already present;
- low-risk foundation improvements worth adopting;
- implementation candidates that require a new bounded workstream and local test evidence.

## Exclusions

- No runtime code changes.
- No changes to Life Notebook data, private workspaces, credentials, provider accounts, or production behavior.
- No merge, release, branch-protection change, or external service enrollment.
- No assumption that BodyFixOS-specific health/compliance requirements apply to HumanOS.

## Findings to carry forward

1. **Sovereign core / replaceable infrastructure.** External providers should remain adapters, not owners of HumanOS domain concepts or canonical state.
2. **AI no-authority design.** Model output is proposal/evidence. Deterministic code or explicit human approval performs consequential state changes.
3. **AI-off operability.** Core HumanOS functions should degrade safely when a hosted/local model is unavailable.
4. **Executable outbound-data policy.** Hosted providers/tools should have declared allowed data classes; future CI/runtime checks should fail closed on disallowed flows.
5. **Idempotent side effects.** Durable work, retries, webhooks, tool calls, and delegated actions should tolerate duplicate delivery/replay without duplicate effects.
6. **Untrusted-input boundary.** Browser content, email, files, retrieved text, and model-generated instructions must not gain tool authority merely by being read.
7. **Risk-tiered review.** Money, auth, permissions, encryption, cross-workspace boundaries, destructive actions, migrations, and AI policy changes need stronger review than docs/UI changes.
8. **Read-access evidence.** Sensitive reads can be consequential, not only writes; future access logging/break-glass design should account for this where applicable.
9. **Prompt/model provenance.** Model/prompt versions and eval evidence should be preserved for AI behavior changes that affect decisions or actions.
10. **Recovery as a first-class acceptance test.** Restart, duplication, partial failure, restore, and fallback belong in acceptance criteria for durable capabilities.
11. **Enforced module boundaries.** Architectural boundaries should eventually be checked mechanically rather than relying only on folder names/documentation.
12. **Incident/fallback runbooks.** Security, provider outage, restore, and degraded-mode procedures should be explicit for production-grade capabilities.

## Existing HumanOS alignment

HumanOS already has strong partial coverage:
- owner promotion authority and evidence-first SDLC;
- workspace isolation and fail-closed routing;
- provider neutrality in the workflow standard;
- append-only/provenance-oriented records;
- independent model review as proposal rather than proof;
- regression, restart/recovery, duplication, security, and privacy review requirements;
- private data kept out of Git.

These lessons should extend the existing foundation, not create a competing methodology.

## Review-later implementation candidates

### Candidate A — Provider/Data-Class Gate
Inspect current model, browser, file, email/inbox, and future connector boundaries. Define a machine-readable vendor/tool register with allowed data classes and fail-closed checks.

### Candidate B — Consequential Action Boundary
Inspect work_executor, capabilities, permissions, swarm, browser tooling, and delegated work. Verify that untrusted/model-originated content cannot directly authorize consequential actions.

### Candidate C — Idempotency Contract
Inventory durable side-effect paths and define atomic deduplication/replay rules before adding more autonomous execution.

### Candidate D — AI Evaluation Gate
Define prompt/model/version provenance plus adversarial evals for capabilities whose AI output can influence actions, permissions, routing, or durable records.

### Candidate E — Risk-Tiered Repository Controls
Review CODEOWNERS/rulesets/status checks for sensitive paths. Current canonical branch protection was observed as disabled on 2026-09-18; changing repository controls requires owner approval.

### Candidate F — Operational Runbooks
Add bounded restore, degraded-mode, provider-outage, incident-response, and break-glass runbooks where the corresponding runtime capability exists.

## Acceptance criteria for this review slice

- Durable review/work-order artifacts exist on the review branch.
- No runtime behavior changes.
- Every candidate is explicitly proposal/review-later unless backed by separate implementation evidence.
- No BodyFix/private client data is copied into HumanOS.
- Next action remains one bounded implementation candidate, selected by owner need.

## Rollback

Delete the review branch. Canonical runtime-0.1 remains unchanged.

## Next action

When a concrete HumanOS need intersects one candidate above, inspect the affected branch/components locally and create a separate bounded implementation workstream with tests and rollback.
