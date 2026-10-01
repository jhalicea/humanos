# HumanOS Adaptive Learning Academy — Architecture v0.1

Status: implementation candidate under `HOS-LEARN-002`
Scope: reusable HumanOS Academy machinery and its boundary with private curriculum/state

## Purpose

The HumanOS Academy is a first-class HumanOS subsystem for adaptive, evidence-based learning. It is not a separate school application and it is not a collection of PDFs. It inherits HumanOS governance, privacy, portability, provenance, human-authority, and SDLC rules.

The Academy must remain useful as model providers, interfaces, storage engines, and deployment environments change. The durable contract is the learning model and evidence/state semantics, not any one AI or database product.

## Separation of concerns

HumanOS Academy is deliberately split into four layers:

1. **Academy Kernel / Blueprint — public HumanOS Git repository**
   - portable schemas and loaders;
   - teaching protocol and policy invariants;
   - reusable curriculum object model;
   - certification-overlay and job-pack semantics;
   - append-only event/state machinery;
   - CLI/runtime integration;
   - tests and synthetic fixtures.

2. **Curriculum Content — authorized private modules/packages**
   - actual courses and modules;
   - real skills and concepts;
   - exercises, labs, assessments and resources;
   - certification objective mappings;
   - job-specific educational packs.

3. **Learner State and Evidence — private local-first store**
   - selected current focus;
   - unfinished and paused activities;
   - learning events;
   - grades and evidence;
   - skill stages and derived mastery;
   - checkpoints and later retention/review events.

4. **Interface — Mirror / CLI / future UI / authorized AI**
   - presents courses, missions, progress and skill relationships;
   - invokes governed state transitions;
   - teaches according to the HumanOS Teaching Protocol;
   - never becomes the canonical source of learner state merely because it has chat history.

The public repository intentionally contains synthetic Academy content only. Real learner curriculum and learning state belong in `humanos-academy-private` or another explicitly authorized private store.

## Universal curriculum model

The reusable model is:

```text
Academy Package
├── Shared Skill Graph
├── Courses
│   ├── Modules
│   │   └── Skills
│   ├── Labs
│   └── Certification Overlays
├── Job Packs
└── Resources
```

A Skill may appear in multiple courses. This is intentional. The learner should not have to relearn APIs, networking, evidence reasoning, communication, or another shared capability merely because a second course uses it.

### Labs

Labs are learning activities inside a parent course. A lab may exercise several skills in the parent course. A lab is not promoted into a disconnected top-level course simply because it is important.

### Certification overlays

A certification is an external validation path layered over a durable course. Certification objectives map to existing skills in that parent course.

```text
Certification Objective
        ↓
Existing Course Skills
        ↓
Labs / Assessments / Evidence
        ↓
Coverage View
```

The Academy may report skill coverage for an overlay. Coverage is **not** credential readiness, exam readiness, certification completion, or a credential claim.

### Job packs

A Job Pack maps a role's educational requirements to the shared skill graph. Employer-specific terminology or interview preparation may be represented as job-pack requirements, but the pack does not silently redesign the durable curriculum. Actual applications, employer pursuit, resumes, recruiter communication, and application status belong to Career Ops rather than Academy.

## Curriculum package vs runtime database

Portable curriculum packages are the exchange and preservation format. Versioned JSON is the v1 runtime format; human-readable Markdown may accompany packages and later tooling may support YAML or other authoring forms.

The database is the operational state engine, not the only copy of curriculum knowledge.

```text
Private curriculum package
        ↓
validate against Academy contract
        ↓
load into HumanOS
        ↓
query/use through Academy runtime

Learning interaction
        ↓
append Academy event
        ↓
rebuild/derive current learner state
        ↓
Mirror / CLI / future UI
```

This permits later movement from SQLite to another database without redefining the Academy itself.

## State and evidence model

The v1 runtime uses an append-only SQLite event ledger. HumanOS derives current state by replaying events. Update/delete triggers reject mutation of ledger rows through the Academy store database boundary.

Important invariant:

> **unfinished != current**

Starting or leaving an activity unfinished does not make it the current focus. Only an explicit human focus-selection event establishes current focus. Pausing clears current focus without deleting the unfinished activity. Resumption is an explicit action.

This prevents stale exercises, old tabletop work, or a previous AI's assumptions from controlling what the learner studies next.

### Evidence and mastery

Evidence is recorded against skills using the existing HumanOS mastery dimensions:

- Knowledge: 25%
- Practical: 30%
- Diagnostic: 25%
- Communication: 20%

Evidence-derived mastery and progression stage are separate. Recording evidence does not silently promote a skill stage. Stage changes are explicit governed events.

Current v1 stages retain the existing HumanOS mastery-engine vocabulary:

`unseen -> introduced -> assisted -> practiced -> demonstrated -> mastered`

A later workstream may evolve the public progression taxonomy, but migration must be explicit and evidence-preserving.

## Teaching execution contract

The machine-readable teaching protocol is stored at:

`learning/protocols/humanos-teaching-v1.json`

Every AI-facing Academy implementation must preserve its core invariant:

> **AI must not perform the cognitive work that the lesson is intended to develop.**

The protocol is provider-neutral. ChatGPT, Claude, a local model, or another authorized model may act as tutor, but the model does not redefine the learning contract.

## HumanOS integration

The first runtime entry point is:

```text
humanos academy ...
```

The Academy CLI supports package inspection, explicit focus selection, activity lifecycle, evidence/stage events, checkpoints, certification coverage, job-pack coverage, and protocol inspection.

Environment-bound defaults are replaceable:

- `HUMANOS_ACADEMY_PACKAGE` — authorized curriculum package path;
- `HUMANOS_ACADEMY_DB` — private local Academy SQLite state path.

The repository default package is synthetic and exists only so a clean public checkout can exercise and test the machinery without private learner data.

## Authority and privacy rules

1. Capability is not authority.
2. An AI may propose curriculum changes but cannot silently promote them.
3. Learner state is private by default.
4. Public HumanOS uses synthetic course/test fixtures only.
5. No external credential, course completion, or job readiness is inferred from coverage alone.
6. Chat history is not canonical Academy state.
7. Current focus is chosen by the human.
8. Evidence/state changes must be attributable through the ledger.
9. Provider-specific tools are implementation environments, not Academy authority.
10. The Academy inherits the HumanOS Constitution and workflow/promotion gates.

## v0.1 acceptance target

A fresh HumanOS instance must be able to load a valid Academy package, list and inspect courses, show nested labs and certification overlays, explicitly select a current focus, start and pause work without confusing unfinished work with current focus, record evidence, rebuild state after reopening the database, and resume an explicitly chosen focus.

That vertical slice is the minimum usable Academy kernel. Mission Board, Skill Universe, dynamic simulations, spaced review scheduling, richer model orchestration, and visual UI are subsequent bounded workstreams built on this state contract rather than parallel replacements.
