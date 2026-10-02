# HumanOS Architecture Baseline Plan

Status: **CANDIDATE / HOS-ARCH-001 — OWNER RATIFICATION REQUIRED FOR GOVERNANCE CHANGES**  
Baseline: `runtime-0.1` @ `3f2f25ea09941c8727daac1826e37badf0730d72`  
Date: 2026-10-01

This document is a public-safe architecture baseline plan. It does not contain private filesystem roots, learner state, Notebook content, credentials, employer/client data, or personal workspace details.

## 1. Why this layer is being added

HumanOS already has architecture decisions embedded in code, foundation documents, work orders, tests and operating rules. What is missing is a single architecture discipline that continuously reconciles those sources into an evidence-backed **as-built** view and a separately approved **target** view.

The purpose of this architecture layer is not to invent a new HumanOS. It is to prevent architecture knowledge from living only in conversations or becoming stale while implementation changes.

## 2. Evidence states

Architecture statements must distinguish what is documented from what is demonstrated.

- **DOCUMENTED** — a repository document says the statement is true.
- **IMPLEMENTATION-CONFIRMED** — source code or schema evidence demonstrates the statement.
- **TESTED** — a repeatable automated or local test demonstrates the behavior.
- **ENFORCED** — code, policy checks, or Continuous Integration automation prevents or fails a violating change.
- **INFERRED** — evidence suggests the statement but does not prove it.
- **UNKNOWN** — evidence is insufficient.
- **CONTRADICTED** — current sources disagree.
- **OBSOLETE** — historical statement no longer describes the current system.

A document by itself never counts as enforcement.

## 3. Current evidence-backed architecture — preliminary

The following is documented by the baseline repository and must be re-verified against source code, generated maps, tests, and runtime traces during reconstruction.

| Area | Preliminary as-built statement | Evidence state |
|---|---|---|
| Human interface | Mirror is the human-facing coordination/interface layer. | DOCUMENTED |
| Runtime | Python terminal-first runtime. | DOCUMENTED |
| Model boundary | Local Ollama is the implemented inference provider behind an adapter boundary. | DOCUMENTED |
| Durable state | Notebook/session/transaction/recovery state is SQLite-backed with readable projections. | DOCUMENTED |
| Tool execution | Capabilities, permission checks and governed executor mediate bounded tool actions. | DOCUMENTED |
| Context | Context registry/runtime resolves workspace/workstream routing and ambiguity. | DOCUMENTED |
| Integrity/recovery | Audit/integrity and explicit recovery states are part of the runtime. | DOCUMENTED |
| Agent/tool broker | A bounded JSON (JavaScript Object Notation) proposal/tool broker exists; it is not a general autonomous worker scheduler. | DOCUMENTED |
| Browser | A governed Browser Bridge exists; local end-to-end pairing requires separate verification. | DOCUMENTED |
| Academy runtime | Generic mastery/catalog runtime exists publicly; real curriculum/progress remain private. | DOCUMENTED |
| Testing | Standard-library `unittest` regression suite with isolated test state. | DOCUMENTED |
| Continuous Integration | GitHub Actions is documented as running the regression suite on Ubuntu/macOS with Python 3.11/3.13. | DOCUMENTED; TEST RESULT REQUIRES RUN EVIDENCE |
| Public/private boundary | Public repository excludes real learner state, private Notebook records, credentials and confidential workspace data. | DOCUMENTED |

HOS-ARCH-001 promotes detailed claims to stronger evidence states only after tracing the implementation or immutable test/runtime evidence.

## 4. Existing architecture strengths to preserve

- human authority above model output;
- replaceable model/provider boundary;
- explicit capability and permission checks;
- durable evidence and recovery rather than hidden conversational state;
- privacy boundary between public code and private personal state;
- isolated tests and evidence-oriented Software Development Life Cycle (SDLC);
- explicit distinction between implemented, specified and planned capability;
- workstream routing rather than one global task assumption.

The architecture baseline must strengthen these properties, not create a parallel governance system.

## 5. Architecture gaps to close

### Requirements and tradeoffs
- architecturally significant requirements;
- quality-attribute scenarios;
- explicit constraints;
- one-way/two-way-door classification;
- build-vs-buy and portability reasoning where relevant.

### Structural views
- C4 model (Context, Containers, Components, Code) System Context view;
- C4 Container view;
- selected component views;
- domain/boundary map;
- data ownership and lifecycle;
- trust/authority boundaries;
- deployment/runtime map;
- build/release map.

### Engineering baseline
- supported developer/runtime environments;
- editor / Integrated Development Environment (IDE) assumptions versus tool-neutral requirements;
- language/runtime versions;
- external Software Development Kit (SDK) / Application Programming Interface (API) adapters;
- dependency/package policy;
- repository/folder rules;
- formatting/lint/type-check strategy;
- tests, Artificial Intelligence (AI) evaluations, architecture checks and security checks;
- Continuous Integration (CI) / Continuous Delivery or Deployment (CD) and release/rollback;
- configuration/secrets/migrations;
- observability and operations;
- backup/restore/runbooks.

### Decision memory
- Architecture Decision Record (ADR) template and registry;
- supersession rather than history rewriting;
- decision provenance;
- explicit current versus target state.

### Architecture conformance
- generated/re-runnable dependency and import maps where practical;
- fitness/conformance tests for high-value boundaries;
- release-time architecture drift review;
- no architecture claim promoted solely because multiple models agree.

## 6. Roles before agents

HumanOS engineering defines responsibilities before deciding whether any responsibility deserves a specialist agent.

```text
Human owner / accountable engineer
        |
        +-- product / requirements
        +-- architecture
        +-- research
        +-- implementation
        +-- test / Quality Assurance (QA)
        +-- security
        +-- independent review
        +-- release / operations
```

A responsibility may be performed by the human, deterministic automation, one model, a workflow, or a specialist agent. If agents are used, identity, scoped capabilities, permission enforcement, resource/spend limits, evidence, evaluations, and approval gates remain external controls.

## 7. Separate decision axes — do not collapse authority and reversibility

HumanOS already uses GREEN / AMBER / RED as an **authority/delegation axis**. Architecture must not reuse those colors to mean reversibility or migration cost.

Architecture uses a separate **Reversibility Class**:

### Reversibility Class R1 — two-way door
Local or cheap to reverse. Examples: a helper refactor, an internal rename, a low-coupling presentation change.

### Reversibility Class R2 — coordinated but recoverable
Meaningful change with rollback or migration work. Examples: a new subsystem interface, dependency adoption, or schema change with tested rollback.

### Reversibility Class R3 — one-way or expensive-to-reverse
Architecture/security/data/authority/public-contract decisions with high migration cost, long-lived compatibility obligations, or large blast radius.

R3 requires:

`evidence → quality attributes → alternatives/tradeoffs → threat/failure analysis → Architecture Decision Record → migration/rollback/recovery → independent/adversarial review → explicit human ratification`

### Authority × reversibility matrix

| Delegation/authority lane | R1 — two-way door | R2 — coordinated/recoverable | R3 — one-way/expensive |
|---|---|---|---|
| GREEN authority lane | May execute only within already granted capability and policy | Not automatically executable; bounded approval policy required | **Never independently executable** |
| AMBER authority lane | May recommend or prepare | Recommend + evidence + approval before consequential change | Recommend only; human ratification required |
| RED authority lane | Human-directed as defined by the governing delegation model | Human decision/approval required | Human ratification is mandatory before implementation/promotion |

The authority lane answers **who may decide or execute**. Reversibility Class answers **how expensive/risky the decision is to undo**. They are independent axes.

This architecture policy supplements the existing Software Development Life Cycle (SDLC); it does not replace `DEFINE → BASELINE → DIVIDE → PLAN → IMPLEMENT → TEST → COMPARE → VERIFY → PROMOTE → PRESERVE`.

## 8. Judgment Disclosure and ratification

Delegated architecture/governance work must separate mechanical work from judgment.

A Judgment Disclosure records:

- judgments introduced by the delegate;
- alternatives considered;
- assumptions and uncertainty;
- whether the change is documented, tested, or enforced;
- Reversibility Class;
- authority/delegation lane;
- what requires human ratification;
- rollback/supersession path.

Creating a branch, formatting a document, or generating a dependency map is mechanical. Choosing product boundaries, data ownership, authentication strategy, authority policy, a permanent folder standard, or a public contract is judgment and must be disclosed.

A merge does not automatically prove owner ratification. Ratification must be recorded explicitly where the governing standard requires it.

## 9. Architecture reconstruction before target redesign

The first HOS-ARCH-001 implementation slice is read-only reconstruction:

1. inventory entry points/modules/schemas/adapters/data stores/tests/workflows;
2. generate a re-runnable dependency/import map where tooling permits;
3. trace a normal Mirror request;
4. trace a governed write/tool transaction;
5. trace Notebook persistence/recovery;
6. trace one Academy request across the public/private boundary;
7. trace Continuous Integration and promotion flow;
8. derive dependency and state-ownership maps;
9. compare implementation evidence with existing architecture/security/foundation docs;
10. classify disagreements or missing areas as drift/unknown rather than guessing;
11. propose target architecture only after the as-built baseline is reviewed.

The reconstruction is intentionally timeboxed and evidence-first. New governance prose is not progress unless it closes an observed gap.

## 10. HumanOS ↔ BodyFixOS boundary

BodyFixOS is an independent product. It is outside the HumanOS repository, runtime, domain model and private state boundary.

A future integration, if approved, is an explicit versioned connector / Application Programming Interface (API) contract with scoped permission, minimal data, separate identity, audit evidence, revocation, and independent recovery.

It must not become:

```text
HumanOS imports BodyFixOS internals
HumanOS and BodyFixOS share a database
BodyFixOS private records become HumanOS Notebook state by default
one repository owns both products
```

Each product owns its own architecture, storage, releases, tests, documentation and security context.

A future automated architecture fitness rule should fail source-code changes that introduce a direct BodyFixOS internal import into HumanOS. The repository must label this rule **not enforced** until a concrete test or Continuous Integration check exists.

## 11. Local development-workspace rule

HumanOS should not use the user's home directory or Documents root as a default artifact sink. The target policy separates canonical repositories, worktrees, private runtime state, generated evidence, backups, imports/migrations, temporary files, and personal documents.

Before any cleanup, the actual machine must be inventoried in a read-only pass. Git repositories, worktrees, dirty state, stashes, unpushed commits, ignored/private files, virtual environments, and backups must be identified before anything moves.

Cleanup is staged:

`backup/snapshot → inventory → manifest/checksums → proposed destination → quarantine/move → repair worktrees/recreate environments → verify repositories/tests/runtime → archive/delete only with explicit approval`

## 12. Definition of success

The architecture layer is successful when a future engineer or AI can answer, from current repository evidence rather than chat memory:

- What does HumanOS do and not do?
- What are the major components and boundaries?
- Where is canonical state?
- How does data move?
- Where are trust and authority boundaries?
- Which decisions are expensive to reverse?
- Why were significant choices made?
- What is implemented versus planned?
- How do I build, test, release, observe and recover the system?
- What architecture rules are documented, tested, or enforced?
- What changed since the last baseline?
- How can I reconstruct the system if documentation drifts?

That is the anti-drift architecture layer HOS-ARCH-001 is intended to establish.
