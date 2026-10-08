# HumanOS Architecture Baseline Plan

Status: **CANDIDATE / HOS-ARCH-001 — OWNER RATIFICATION REQUIRED FOR GOVERNANCE CHANGES**  
Baseline: `runtime-0.1` @ `3f2f25ea09941c8727daac1826e37badf0730d72`  
Baseline date: 2026-10-01; workspace/team reconciliation candidate: 2026-10-08

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

## 6. One human, AI-assisted software company — roles before agents

### Operating model and accountability

HumanOS is designed and developed as **one human owner/founder with a governed AI-assisted engineering team**, not a fiction that every AI is an independently employed or authorized person. The owner is accountable for product value, architecture tradeoffs, meaningful external actions, risk acceptance, security policy, cost ceilings, releases and ratifications. A model, coding agent, search tool, or deterministic script can **perform an assigned task** but cannot become the human authority by capability, confidence or successful tests.

```text
                      HUMAN FOUNDER / PRODUCT OWNER
                Vision · priorities · consent · release/ratification
                                  |
                   HUMANOS ENGINEERING CONTROL
              Workstream → work order → branch/worktree → checks
                                  |
           +----------------------+----------------------+
           |                      |                      |
      AI researcher         AI implementer          AI reviewer/QA
      evidence/options      bounded code diff       tests/adversarial review
           |                      |                      |
           +----------------------+----------------------+
                                  |
                       CI + DETERMINISTIC GATES
                                  |
                          HUMAN REVIEW / PROMOTE
                                  |
                       RELEASE · OBSERVE · RECOVER
                         Notebook/source evidence
```

### Responsibilities; no speculative autonomous staff

| Engineering function | Typical accountable role | Suitable support | Deliverable / decision limit |
|---|---|---|---|
| Founder / Product Manager | Human owner | Mirror summarizes needs and tradeoffs | Chooses why/what matters, priority, acceptance and scope |
| Architect / Technical Lead | Human owner accountable; AI may draft | One or more models compare patterns, trace code, draft ADR | Significant one-way decisions require human ratification |
| Research and requirements | Owner validates claims | Search/research worker with cited sources | Provenance and uncertainty; retrieved text cannot become instructions |
| Software developer | Owner delegates bounded task | Codex/Claude/GitHub tooling or selected capable model | Patch only to granted worktree/files; never direct unreviewed production |
| QA and evaluation | Owner sets acceptance | Deterministic tests, CI, separate reviewer/model when useful | Evidence of covered behavior; not a blanket production guarantee |
| Security/privacy | Owner retains risk acceptance | Threat model, secrets scan, independent hypothesis tests | Can block unsafe promotion; model never grants privileges |
| Release/operations | Owner authorizes release | Deterministic scripts/CI and bounded automation | Verify merge, install/host behavior, backup/rollback and checkpoint |
| Librarian/records | Owner controls retention | Notebook importer, indexer and Mirror | Exact evidence before derived summary; cannot silently ratify output |

Each job is a **role**, which may be completed by one tool, one model, multiple independent reviews, or human work. Do not create a persistent autonomous agent, service, queue, account or infrastructure simply because a role appears in the diagram. Today's actual runtime provides bounded capabilities; a general autonomous AI staff is a **target operating pattern, not a verified current capability**.

### How a real software team works: the repeatable HumanOS cycle

1. **Intake and prioritize:** Human identifies problem and desired human outcome; Mirror finds the existing workspace/workstream. If there is no suitable stream, record a bounded proposal instead of silently creating a new product.
2. **Specify:** A work order describes scope, affected files, acceptance criteria, privacy classification, dependencies, owner, authority lane, reversibility class, spend/time budget, and exact next action.
3. **Baseline:** Read the current code, latest branch `HEAD`, dirty/untracked/stash state, and relevant design/decision records. Choose the one canonical repository, then an isolated feature branch/worktree in the established `~/Developer` headquarters.
4. **Assign/delegate:** Research, implementation, QA and review are separate **functions** with scoped work packets, tools and outputs. Use the least expensive capable resource unless the owner requests stronger reasoning or risk/failures justify escalation. Workers get only needed context, never blanket private Notebook/credentials.
5. **Build:** Developer makes a small diff in the assigned worktree. Code and data may be tested locally, but the model cannot approve its own permission or silently alter the Constitution.
6. **Verify:** Run targeted deterministic tests, regression, security/privacy checks and independent review as proportional to risk. Differentiate unit test, GitHub CI, live owner-host acceptance and production qualification.
7. **Propose promotion:** Open a draft PR containing changed files, reason, evidence, risks, rollback and Judgment Disclosure. Passing CI is necessary when required, but not owner ratification.
8. **Decide/release:** Human reviews consequential changes and ratifies architecture/authority/release decisions as required. An approved merge is followed by deployment/install verification and rollback readiness, not treated as proof of a working app on the Mac.
9. **Preserve/recover:** Update existing work order, dated status, Context Registry and Issue #67 pointers as appropriate. Capture **verified** Notebook evidence/checkpoint or explicitly declare `CHECKPOINT LAG`. Never invent a write receipt.
10. **Continue:** Next conversation/work session recovers from checked-in state, the current owner decisions and the last verified checkpoint, rather than trusting a model's remembered completion claim.

**Illustrative separation of duties:** One model proposes a patch; deterministic tests test it; another reviewer critiques risk where worthwhile; only the owner can authorize an R3 architectural decision. Running multiple models without disjoint roles or evidence does not establish independent verification.

### Human experience and worker economy

Mirror is the single simple front door. Ordinary user sees: **Now · Continue · Notebook · Academy · System**. Work orders, PRs, hashes, model choice, and audit receipts sit underneath, with progressive depth `S0 Direct → S1 Guided → S2 Deep → S3 Audit`; the human can inspect details when desired. The engineering team runs behind this interface **only when genuinely necessary**, not to generate paperwork or consume tokens.

Keep separate (a) **authority lane** GREEN/AMBER/RED, (b) **architecture reversibility** R1/R2/R3, and (c) **resource routing/cost**. Cost optimization never silently overrides the owner's explicit model choice or security requirements.

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

## 11. One developer headquarters: canonical workstation layout

**Target and ratification boundary:** Work from the numbered `~/Developer` structure already reported from the October 2 cleanup, **not a newly invented `HumanOS` root or the earlier generic `~/Developer/repos` proposal**. The detailed single-source candidate is [Local Development Workspace Policy](LOCAL_DEVELOPMENT_WORKSPACE_POLICY.md).

- **One navigation headquarters:** `~/Developer/00_Map.md` points to `10_Repos/` (canonical checkouts), `20_Worktrees/` (Git-registered isolated branches), `30_Labs/`, `40_Artifacts/`, `50_Imports/`, and `90_Archive/`. The local map is a non-authoritative locator, not another task ledger.
- **One canonical HumanOS source checkout:** target `~/Developer/10_Repos/humanos/`. Workstreams use registered folders under `~/Developer/20_Worktrees/humanos/`; branches/worktrees are not new or competing HumanOS projects.
- **Separate ownership and security:** HumanOS public source, HumanOS private state, personal/iCloud documents, managed model/VM caches, independent BodyFixOS resources, and backups need distinct classifications and policies. A visible pointer from `~/Developer` does **not** authorize mixing these bytes into one Git repository. Keep private `~/.humanos/` state in place unless an approved migration with restore verification occurs.
- **Backup exception:** independent restore copies cannot be only on the same internal volume as the live project. When external backup is unavailable, mark **DISASTER RECOVERY UNQUALIFIED**, preserve local recovery packets, and forbid destructive cleanup.
- **No more moves by assumption:** October 2 historical conversation reports three repositories and 12 registered HumanOS worktrees moved, while stale registrations and a V-05 discrepancy remained. Verify on the owner's actual Mac; a chat assistant cannot certify filesystem cleanup by reading GitHub or chat history.
- **Deterministic worker destinations:** code → selected worktree, approved reports → scoped `40_Artifacts`, incoming untrusted data → `50_Imports`, scratch → scoped temp/lab, retained old work → `90_Archive`; no silent output to home, Desktop, Documents or arbitrary current directory. Enforce this in executor/tool configuration when available; otherwise label **DOCUMENTED, NOT ENFORCED**.
- **Protection for Git:** inventory dirty files, unpushed commits, stashes, ignored/private files, worktree registrations and virtual environments before any move; move registered worktrees using Git-aware commands and re-verify paths afterward.

Physical relocation of canonical code, worktrees, Notebook databases, keys or backups is **out of scope until an explicit owner-approved, recovery-safe cutover**. A permanent path convention is an architecture judgment requiring owner ratification. Standardize terminology and documentation now; do not claim host enforcement or cleanup completed from this document.

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
