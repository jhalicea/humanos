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
- portability/exit criteria that can be tested rather than merely claimed;
- implementation candidates that require a new bounded workstream and local test evidence.

## Exclusions

- No runtime code changes.
- No changes to Life Notebook data, private workspaces, credentials, provider accounts, or production behavior.
- No merge, release, branch-protection change, or external service enrollment.
- No assumption that BodyFixOS-specific health/compliance requirements apply to HumanOS.

## Findings to carry forward

1. **Sovereign core / replaceable infrastructure.** External providers should remain adapters, not owners of HumanOS domain concepts or canonical state.
2. **Ports versus connectors.** A replaceable execution/provider boundary is a port; a deliberately supported external system is a connector. They have different portability goals and test strategies.
3. **AI no-authority design.** Model output is proposal/evidence. Deterministic code or explicit human approval performs consequential state changes.
4. **AI-off operability.** Core HumanOS functions should degrade safely when a hosted/local model is unavailable.
5. **Executable outbound-data policy.** Hosted providers/tools should have declared allowed data classes; future CI/runtime checks should fail closed on disallowed flows.
6. **Idempotent side effects.** Durable work, retries, webhooks, tool calls, and delegated actions should tolerate duplicate delivery/replay without duplicate effects.
7. **Untrusted-input boundary.** Browser content, email, files, retrieved text, and model-generated instructions must not gain tool authority merely by being read.
8. **Risk-tiered review.** Money, auth, permissions, encryption, cross-workspace boundaries, destructive actions, migrations, and AI policy changes need stronger review than docs/UI changes.
9. **Read-access evidence.** Sensitive reads can be consequential, not only writes; future access logging/break-glass design should account for this where applicable.
10. **Prompt/model provenance.** Model/prompt versions and eval evidence should be preserved for AI behavior changes that affect decisions or actions.
11. **Recovery as a first-class acceptance test.** Restart, duplication, partial failure, restore, fallback, and provider-exit drills belong in acceptance criteria for durable capabilities.
12. **Enforced module boundaries.** Architectural boundaries should eventually be checked mechanically rather than relying only on folder names/documentation.
13. **Incident/fallback runbooks.** Security, provider outage, restore, and degraded-mode procedures should be explicit for production-grade capabilities.
14. **Independence is exit ability.** Self-operation is optional. Portability is measured by data export, substitutable adapters, redeployability, and tested exit procedures.

## Independence ladder

HumanOS capabilities should be assessed independently rather than labeled simply "portable" or "not portable":

- **L0 — Provider-leaky:** provider concepts or proprietary state leak into the HumanOS domain.
- **L1 — Exportable:** authoritative HumanOS data can be exported in documented/open formats.
- **L2 — Replaceable:** a fake or alternate adapter passes a shared contract and the provider can be switched through a bounded runbook.
- **L3 — Deployable elsewhere:** the capability can run on another compatible host/environment and an exit/restore drill has passed.
- **L4 — Self-operated:** HumanOS operates the underlying infrastructure itself.

Default target: L2 for replaceable providers; L3 for canonical data/storage/compute where justified; L4 only for owner need, security, regulation, or economics.

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
Inspect current model, browser, file, email/inbox, and future connector boundaries. Define a machine-readable vendor/tool register with allowed data classes, export mechanism, fallback provider, estimated switching time, and fail-closed checks.

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

### Candidate G — Portability Exit Drills
Define measurable exit drills for model providers, Notebook storage/backups, browser/tool dependencies, repository hosting, and future connectors. Record observed switching time and blockers rather than inferring portability from interfaces.

### Candidate H — Ports vs Connectors Inventory
Classify current external dependencies. Examples: model/runtime providers and storage backends are candidate ports; Google Drive, GitHub, browser services, calendars, and future app integrations may be connectors whose goal is durable interoperability rather than replacement.

## Acceptance criteria for this review slice

- Durable review/work-order artifacts exist on the review branch.
- Portability is defined with observable exit levels and drills.
- Ports and connectors are distinguished.
- No runtime behavior changes.
- Every implementation candidate remains proposal/review-later unless backed by separate implementation evidence.
- No BodyFix/private client data is copied into HumanOS.
- Next action remains one bounded implementation candidate, selected by owner need.

## Rollback

Delete the review branch. Canonical runtime-0.1 remains unchanged.

## Next action

When a concrete HumanOS need intersects one candidate above, inspect the affected branch/components locally and create a separate bounded implementation workstream with tests, an exit criterion, and rollback.
