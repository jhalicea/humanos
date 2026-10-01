# HOS-ARCH-001 — Architecture Recovery & Engineering Baseline

Status: **BASELINE / PLAN ONLY — NO RUNTIME REDESIGN AUTHORIZED BY THIS DOCUMENT**  
Branch: `architecture/hos-arch-001-baseline`  
Baseline: `runtime-0.1` @ `eb5824ff533b2569fbe0a1d53617e7a3a6e06f7f`  
Created: 2026-10-01

## Classification

`CREATE_SEPARATE`

This workstream does not replace the Context Engine, Academy, Life Notebook, model-routing, browser, swarm, backup, or other existing workstreams. It establishes the missing software-architecture/engineering baseline that describes how HumanOS is structured, built, verified, operated and evolved.

## Problem

HumanOS already has substantial implementation, tests, governance and architecture concepts, but its public architecture overview is intentionally high-level. The repository does not yet have one evidence-backed architecture layer that systematically records:

- architecturally significant requirements and quality attributes;
- system/domain/component boundaries;
- data ownership and lifecycle;
- trust and authority boundaries;
- runtime/toolchain/dependency baseline;
- repository/folder conventions;
- development/test/release environments;
- build/CI/deployment/rollback workflow;
- C4 views and deployment views;
- architecture decisions and supersession;
- architecture-conformance/fitness checks;
- operational observability, backup/recovery and runbooks;
- proportional GREEN/AMBER/RED architecture-change rules;
- the distinction between engineering roles and autonomous agents;
- a repeatable architecture-reconstruction procedure for future brownfield work.

Without that layer, implementation and documentation can remain individually good while the overall architecture drifts or important decisions live only in conversation/history.

## Owner invariants

1. Human authority remains above model/agent output.
2. Capability is not authority; permissions are enforced outside model self-claims.
3. HumanOS remains provider/model replaceable and local-first by default.
4. Real personal/private state remains outside the public repository.
5. Existing verified runtime behavior is evidence; this workstream must not redesign from memory.
6. **BodyFixOS is a separate software product and repository. It is not a HumanOS module.**
7. A future HumanOS ↔ BodyFixOS relationship, if approved, is an explicit narrow versioned connector/API boundary with independent data ownership and permissions. No shared database, implicit imports, or private-state coupling by default.
8. Architecture rigor scales with reversibility, blast radius and uncertainty.

## Confirmed baseline evidence

At the baseline commit, repository documentation confirms:

- Python terminal runtime with Mirror as the human-facing interface.
- Local Ollama behind a replaceable model adapter boundary.
- SQLite-backed durable Notebook state and recovery records.
- Capability registry, permissions and governed execution for bounded tools.
- Context/workstream routing and ambiguity handling.
- Audit/integrity/recovery mechanisms.
- Unit/regression tests via standard-library `unittest`.
- GitHub Actions regression matrix on Ubuntu/macOS and Python 3.11/3.13.
- Browser bridge and bounded agent/tool-broker work with explicit stated limitations.
- Private learner/personal state excluded from the public repository.

These statements are starting evidence only. The reconstruction phase must verify code paths and runtime behavior before promoting detailed maps as `CONFIRMED`.

## Deliverables

### D1 — Evidence & source-of-truth register
For every architecture claim, record source path/commit/runtime evidence and classify it:

- `CONFIRMED`
- `INFERRED`
- `UNKNOWN`
- `CONTRADICTED`
- `OBSOLETE`

### D2 — Architecturally significant requirements
Document quality attributes and concrete scenarios for at least:

- human authority and approval;
- privacy/isolation;
- provenance/auditability;
- recoverability;
- modifiability/provider portability;
- integrity;
- availability/degraded operation;
- observability;
- performance/latency where relevant;
- operational cost/resource use;
- testability;
- maintainability.

### D3 — Architecture views
Produce evidence-backed views:

1. C4 System Context
2. C4 Containers
3. C4 Components for architecture-significant areas only
4. Deployment/runtime view
5. Domain/bounded-context map
6. Data ownership/lifecycle map
7. Trust/authority boundary map
8. Agent/tool capability and authorization map
9. Build/test/release/rollback map

### D4 — Engineering baseline
Record current and target defaults for:

- supported OS/developer environment;
- IDE/editor policy (tool-neutral unless a requirement exists);
- shell;
- language/runtime versions;
- SDKs/external adapters;
- package/dependency management;
- formatting/lint/type checking;
- tests/evals/architecture checks/security checks;
- Git/branch/worktree conventions;
- CI/CD;
- environments/config/secrets;
- database/storage/migrations;
- logging/metrics/tracing/alerting;
- backups/restore drills;
- release/versioning/rollback;
- documentation/runbooks.

A baseline must distinguish `CURRENT`, `TARGET`, `OPTIONAL`, and `NOT YET ESTABLISHED` rather than pretending planned tooling exists.

### D5 — Architecture Decision Record policy
Establish an ADR directory and template. Use ADRs only for significant decisions. When a decision changes, supersede it; do not rewrite history.

### D6 — Architecture-change risk lanes

**GREEN — reversible/local**
- normal implementation + automated tests;

**AMBER — meaningful/recoverable**
- small spec + acceptance criteria + tests + review;

**RED — architecture/security/data/authority/contract one-way-ish door**
- problem/evidence + quality attributes + alternatives/tradeoffs + threat/failure analysis + ADR + migration/rollback/recovery + adversarial review + explicit approval.

Examples of RED decisions: canonical data model, authentication/authorization, encryption/key strategy, public API contracts, agent authority, irreversible migration, deployment trust boundary.

### D7 — Architecture fitness/conformance checks
Identify important prose-only rules that can become automated checks, for example:

- forbidden dependency directions;
- private-data paths excluded from Git;
- domain/runtime layers cannot bypass permission broker;
- model/agent code cannot grant itself capabilities;
- schema/version compatibility rules;
- public repo cannot contain private Academy/Notebook state.

No check should be invented merely to increase test count; each must defend an architecture invariant.

### D8 — Workspace/repository policy
Define canonical local placement for:

- repositories;
- Git worktrees;
- private runtime state;
- generated evidence;
- temporary files;
- backups;
- exports/migrations;
- personal documents.

This policy must prevent the home directory from becoming the default artifact sink.

## Architecture reconstruction procedure

Before proposing target structure:

1. Capture repository commit/tree and Git/worktree state.
2. Inventory entry points, modules, schemas, data stores, external adapters, tests and CI.
3. Run the documented test/build path in an isolated environment.
4. Trace one normal Mirror request end-to-end.
5. Trace one governed tool/write transaction end-to-end.
6. Trace one Notebook persistence/recovery lifecycle.
7. Trace one Academy request without exposing private learner state.
8. Trace one CI/release/promotion path.
9. Map dependencies and state ownership.
10. Compare code/runtime evidence against existing architecture/security docs.
11. Mark drift/unknowns; do not silently resolve them by assumption.
12. Only then propose target architecture changes.

## Proposed documentation layout

The exact layout is a target to validate, not an automatic migration:

```text
docs/
  architecture/
    README.md
    as-built/
      SYSTEM_CONTEXT.md
      CONTAINERS.md
      COMPONENTS.md
      DEPLOYMENT.md
      DOMAIN_MAP.md
      DATA_FLOW.md
      TRUST_AUTHORITY.md
      BUILD_RELEASE.md
    requirements/
      QUALITY_ATTRIBUTES.md
      CONSTRAINTS.md
    decisions/
      ADR-0000-template.md
      ...
    engineering/
      ENGINEERING_BASELINE.md
      REPOSITORY_STRUCTURE.md
      ENVIRONMENTS.md
      TEST_EVAL_STRATEGY.md
      OBSERVABILITY_RECOVERY.md
    governance/
      ARCHITECTURE_CHANGE_POLICY.md
      FITNESS_FUNCTIONS.md
      DRIFT_REVIEW.md
```

Existing `docs/architecture.md` remains the concise public overview until replacement/splitting is deliberately approved. Historical foundation documents remain authoritative according to their own status and are not silently moved or rewritten.

## Acceptance criteria for this workstream's first promotion

- As-built maps are derived from repository/runtime evidence, not conversational memory.
- Each significant claim has provenance and confidence/state.
- Current vs target architecture is visually and textually separated.
- Engineering baseline explicitly covers IDE/editor, runtime, SDK/API, package/build/test/CI, environments, repository/folders, deployment, observability and recovery.
- Quality attributes and RED one-way-door decisions are defined.
- ADR and architecture-drift policies exist.
- Human/AI engineering roles are defined separately from agent implementations.
- BodyFixOS separation invariant is explicit.
- Local workspace cleanup has a reversible inventory/quarantine plan; no destructive cleanup is performed by architecture documentation alone.
- Relevant existing tests remain green; documentation does not claim unimplemented capability.

## Out of scope for this first slice

- rewriting the runtime architecture;
- changing canonical storage formats;
- moving the owner's local files;
- deleting worktrees/backups/evidence;
- introducing microservices, Kubernetes, React, cloud infrastructure or new SDKs merely for architectural appearance;
- implementing a BodyFixOS connector;
- changing BodyFixOS from inside the HumanOS repository.

## Current next action

Perform the read-only as-built reconstruction and local-workspace inventory, then return the evidence-backed baseline and proposed migration plan for owner review before any structural code or filesystem change.
