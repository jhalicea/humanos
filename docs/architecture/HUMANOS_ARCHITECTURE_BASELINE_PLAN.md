# HumanOS Architecture Baseline Plan

Status: **CANDIDATE / HOS-ARCH-001**  
Baseline: `runtime-0.1` @ `eb5824ff533b2569fbe0a1d53617e7a3a6e06f7f`  
Date: 2026-10-01

This document is a public-safe architecture baseline plan. It does not contain private filesystem roots, learner state, Notebook content, credentials, employer/client data, or personal workspace details.

## 1. Why this layer is being added

HumanOS already has architecture decisions embedded in code, foundation documents, work orders, tests and operating rules. What is missing is a single architecture discipline that continuously reconciles those sources into an evidence-backed `AS-BUILT` view and a separately approved `TARGET` view.

The purpose of the new architecture layer is therefore not to invent a new HumanOS. It is to prevent architecture knowledge from living only in conversations or becoming stale while implementation changes.

## 2. Current evidence-backed architecture — preliminary

The following is confirmed by the baseline repository documentation and must be re-verified against code/runtime traces during reconstruction.

| Area | Preliminary as-built statement | State |
|---|---|---|
| Human interface | Mirror is the human-facing coordination/interface layer. | CONFIRMED BY DOCS |
| Runtime | Python terminal-first runtime. | CONFIRMED BY DOCS |
| Model boundary | Local Ollama is the implemented inference provider behind an adapter boundary. | CONFIRMED BY DOCS |
| Durable state | Notebook/session/transaction/recovery state is SQLite-backed with readable projections. | CONFIRMED BY DOCS |
| Tool execution | Capabilities, permission checks and governed executor mediate bounded tool actions. | CONFIRMED BY DOCS |
| Context | Context registry/runtime resolves workspace/workstream routing and ambiguity. | CONFIRMED BY DOCS |
| Integrity/recovery | Audit/integrity and explicit recovery states are part of the runtime. | CONFIRMED BY DOCS |
| Agent/tool broker | A bounded JSON proposal/tool broker exists; it is not a general autonomous worker scheduler. | CONFIRMED BY DOCS |
| Browser | A governed Browser Bridge exists; local end-to-end pairing requires separate verification. | CONFIRMED BY DOCS |
| Academy runtime | Generic mastery/catalog runtime exists publicly; real curriculum/progress remain private. | CONFIRMED BY DOCS |
| Testing | Standard-library `unittest` regression suite with isolated test state. | CONFIRMED BY DOCS |
| CI | GitHub Actions runs the regression suite on Ubuntu/macOS with Python 3.11/3.13. | CONFIRMED BY WORKFLOW |
| Public/private boundary | Public repository excludes real learner state, private Notebook records, credentials and confidential workspace data. | CONFIRMED BY POLICY |

`CONFIRMED BY DOCS` is not the same as code/runtime proof. HOS-ARCH-001 promotes detailed claims to `CONFIRMED` only after tracing the implementation or immutable test/runtime evidence.

## 3. Existing architecture strengths to preserve

- human authority above model output;
- replaceable model/provider boundary;
- explicit capability and permission checks;
- durable evidence and recovery rather than hidden conversational state;
- privacy boundary between public code and private personal state;
- isolated tests and evidence-oriented SDLC;
- explicit distinction between implemented, specified and planned capability;
- workstream routing rather than one global task assumption.

The architecture baseline must strengthen these properties, not create a parallel governance system.

## 4. Architecture gaps to close

The current short architecture overview does not yet serve as a complete engineering map. HOS-ARCH-001 will add or reconcile:

### Requirements and tradeoffs
- architecturally significant requirements;
- quality-attribute scenarios;
- explicit constraints;
- one-way/two-way-door classification;
- build-vs-buy and portability reasoning where relevant.

### Structural views
- C4 System Context;
- C4 Containers;
- selected component views;
- domain/boundary map;
- data ownership and lifecycle;
- trust/authority boundaries;
- deployment/runtime map;
- build/release map.

### Engineering baseline
- supported developer/runtime environments;
- editor/IDE assumptions vs tool-neutral requirements;
- language/runtime versions;
- external SDK/API adapters;
- dependency/package policy;
- repository/folder rules;
- formatting/lint/type-check strategy;
- tests, AI evals, architecture checks and security checks;
- CI/CD and release/rollback;
- config/secrets/migrations;
- observability and operations;
- backup/restore/runbooks.

### Decision memory
- ADR template and registry;
- supersession rather than history rewriting;
- decision provenance;
- explicit current vs target state.

### Architecture conformance
- fitness/conformance tests for high-value boundaries;
- release-time architecture drift review;
- no architecture claim promoted solely because multiple models agree.

## 5. Roles before agents

HumanOS engineering should define responsibilities first:

```text
Human owner / accountable engineer
        |
        +-- product / requirements
        +-- architecture
        +-- research
        +-- implementation
        +-- test / QA
        +-- security
        +-- independent review
        +-- release / operations
```

A responsibility may be performed by the human, deterministic automation, one model, a workflow, or a specialist agent. The architecture does not create an autonomous agent simply because a role exists.

If/when agents are used, identity, scoped capabilities, permission enforcement, resource/spend limits, evidence, evals and approval gates remain external controls.

## 6. Architecture change policy

### GREEN
Local and easily reversible. Normal implementation + tests are usually sufficient.

### AMBER
Meaningful but recoverable. Require a bounded spec, acceptance criteria, relevant tests and review.

### RED
Architecture/security/data/authority/public-contract decisions with high migration cost or blast radius. Require:

`evidence → quality attributes → alternatives/tradeoffs → threat/failure analysis → ADR → migration/rollback/recovery → adversarial review → explicit approval`

This policy supplements the existing HumanOS SDLC; it does not replace `DEFINE → BASELINE → DIVIDE → PLAN → IMPLEMENT → TEST → COMPARE → VERIFY → PROMOTE → PRESERVE`.

## 7. Architecture reconstruction before target redesign

The first HOS-ARCH-001 implementation slice is read-only reconstruction:

1. inventory entry points/modules/schemas/adapters/data stores/tests/workflows;
2. trace a normal Mirror request;
3. trace a governed write/tool transaction;
4. trace Notebook persistence/recovery;
5. trace one Academy request across the public/private boundary;
6. trace CI/promotion flow;
7. derive dependency and state-ownership maps;
8. compare implementation evidence with existing architecture/security/foundation docs;
9. classify every disagreement or missing area as drift/unknown rather than guessing;
10. propose the target architecture only after the as-built baseline is reviewed.

## 8. HumanOS ↔ BodyFixOS boundary

BodyFixOS is an independent product. It is outside the HumanOS repository, runtime, domain model and private state boundary.

A future integration, if approved, should look conceptually like:

```text
HumanOS                         BodyFixOS
   |                               |
   |  explicit versioned contract  |
   +------ connector / API --------+
          scoped permission
          minimal data
          audit trail
          revocable access
```

It must not become:

```text
HumanOS imports BodyFixOS internals
HumanOS and BodyFixOS share a database
BodyFixOS private records become HumanOS Notebook state by default
one repository owns both products
```

Each product owns its own architecture, storage, releases, tests, documentation and security context.

## 9. Local development-workspace rule

HumanOS should not use the user's home directory or Documents root as a default artifact sink. The target policy will separate:

- canonical repositories;
- worktrees;
- private runtime state;
- generated evidence;
- backups;
- imports/migrations;
- temporary files;
- personal documents.

Before any cleanup, the actual machine must be inventoried in a read-only pass. Every existing item must be classified as active repository, active worktree, canonical private state, evidence/artifact, backup, migration/import, temporary/generated, legacy candidate, or unknown. Git worktrees and uncommitted changes must be identified before moving anything.

Cleanup is staged: `inventory → manifest/checksums → proposed destination → quarantine/move → verify repos/tests/runtime → archive/delete only with explicit approval`.

## 10. Definition of success

The architecture layer is successful when a future engineer or AI can answer, from current repository evidence rather than chat memory:

- What does HumanOS do and not do?
- What are the major components and boundaries?
- Where is canonical state?
- How does data move?
- Where are trust and authority boundaries?
- Which decisions are expensive to reverse?
- Why were significant choices made?
- What is implemented vs planned?
- How do I build, test, release, observe and recover the system?
- What architecture rules are automatically enforced?
- What changed since the last baseline?
- How can I reconstruct the system if documentation drifts?

That is the anti-drift architecture layer HOS-ARCH-001 is intended to establish.
