# HOS-LEARN-002 — Adaptive Academy Kernel & Runtime Vertical Slice

Status: REVIEW_CANDIDATE
Workspace: `WS-HUMANOS`
Project: Learning and Mastery
Classification: `EXTEND` existing Academy/Mastery lineage
Branch: `feature/academy-kernel-runtime-v1`
Baseline: `runtime-0.1` at `a85462ccde61ea84e8f1cb680c7fdeefe04c97bf`
Related: `HOS-LEARN-001`, `HOS-MASTERY-001`
Public PR: `#118`
Private content candidate: `jhalicea/humanos-academy-private#1`

## Desired outcome

Create the first serious HumanOS Academy runtime slice as part of HumanOS rather than as a disconnected course application. The Academy must separate reusable machinery from real learner curriculum/state, preserve HumanOS governance and privacy boundaries, and provide a portable provider-neutral substrate that any authorized AI can use.

## Architectural decision for this slice

HumanOS public repository owns reusable Academy machinery: schemas, loaders, teaching protocol, state/event engine, CLI/runtime interfaces, generic documentation, and synthetic fixtures/tests.

Real curricula, labs, certification mappings, job-specific educational packs, learner progress, grades, assessments, evidence, and personalized state remain in `jhalicea/humanos-academy-private` or another explicitly authorized private store. The public runtime loads those definitions through a path/interface; it must not embed them.

The append-only Academy event ledger is authority for runtime learner-state transitions. Derived state is rebuildable. `unfinished != current`: only an explicit focus-selection event creates current focus; pausing clears current focus without erasing unfinished work.

## Bounded scope

1. Define generic curriculum objects for Course, Module, Skill, Concept, Exercise, Lab, Assessment, Resource, Certification Overlay, and Job Pack.
2. Define and validate a portable JSON Academy package format.
3. Add machine-readable HumanOS Teaching Protocol v1.
4. Add a local-first SQLite Academy event store with append-only event rows and rebuildable derived state.
5. Implement explicit current-focus select/pause/resume semantics.
6. Implement certification overlays and job packs as skill mappings, never duplicate standalone course machinery.
7. Provide a small synthetic public package proving the model.
8. Add an Academy CLI surface that can load a package, list courses, inspect a course, select/pause/resume focus, record an activity event, and show derived state.
9. Add automated tests for validation, focus semantics, persistence/rebuild, overlays, protocol invariants, and CLI flow.
10. Document the architecture and the AI-native teaching/experience model.

## Explicit exclusions

- No real learner curriculum, grades, progress, evidence, job applications, employer pursuit records, or private course state in the public repo.
- No migration of historical Academy evidence in this slice.
- No claim that any certification is earned or exam-ready.
- No automatic curriculum self-promotion from labor-market signals.
- No production web UI, gamification layer, or model-provider dependency in this slice.
- No destructive migration of existing `learning/mastery_engine.py` evidence semantics.
- No automatic resumption of `TTX-001` or any other unfinished activity.

## Risks / authority boundaries

- Privacy: public fixtures must remain synthetic.
- Continuity: historical `feature/adaptive-learning-academy-v1` is preserved and not force-rebased or overwritten.
- Authority: AI may propose curriculum changes but may not promote them automatically.
- State integrity: event history is append-only through the Academy store API; derived views may be rebuilt.
- Human agency: current focus is explicit owner choice, never inferred from oldest unfinished work.
- Portability: standard-library implementation only for this slice; no cloud/provider lock-in.
- Local privacy: default learner-state database is outside the repository at `$HOME/.humanos/private/academy/academy.sqlite3` unless explicitly overridden.

## Observable acceptance criteria

A fresh HumanOS checkout can, using only synthetic public fixtures:

1. load and validate an Academy package;
2. list courses and their modules/skills;
3. show certification and job-pack mappings to existing skills;
4. select one current learning focus explicitly;
5. record an activity as an append-only learning event;
6. pause the activity so unfinished work remains known but no longer becomes current;
7. reopen the SQLite store and rebuild the same derived state;
8. explicitly resume/select a focus again;
9. reject invalid package references and unsupported schema versions;
10. expose the ordered Teaching Protocol and invariant that AI must not perform the cognitive work the lesson is intended to develop.

All existing regression tests plus new Academy tests must pass in CI before promotion is considered.

## Implemented components

- `learning/academy_models.py`
- `learning/academy_loader.py`
- `learning/academy_store.py`
- `learning/teaching_protocol.py`
- `learning/academy_cli.py`
- `learning/protocols/humanos-teaching-v1.json`
- `schemas/academy-package-v1.schema.json`
- `examples/academy/synthetic-academy-v1.json`
- `docs/academy/ACADEMY_ARCHITECTURE.md`
- `docs/academy/ACADEMY_EXPERIENCE_BLUEPRINT.md`
- `docs/academy/HUMANOS_TEACHING_PROTOCOL.md`
- `docs/academy/HUMAN_IN_THE_AI_AGE.md`
- `tests/test_academy_kernel.py`
- `tests/test_academy_store.py`
- `tests/test_academy_cli.py`
- `humanos.py` Academy command routing

## Verification evidence

Public kernel candidate code head: `a3a74a3fdf824aa116d8a03b2833da2b4655047d`

GitHub Actions run `36756402100`:

- Ubuntu 24.04 / Python 3.11 — PASS
- Ubuntu 24.04 / Python 3.13 — PASS
- macOS 15 / Python 3.11 — PASS
- macOS 15 / Python 3.13 — PASS
- full suite result on verified matrix job: **606 tests, PASS**

The suite includes Academy package-reference validation, teaching-protocol invariants, certification-as-overlay behavior, CLI integration, append-only database enforcement, explicit current-focus behavior, restart/rebuild, evidence idempotence including semantic retries without a repeated timestamp, and fail-closed completion of unknown activities.

Private compatibility candidate: `jhalicea/humanos-academy-private` head `c953a8bfcc63c0e2f44d8dffee5cd883a2ef81b0`.

Private validation run `36756552647` checked the real curriculum package against public kernel code head `a3a74a3fdf824aa116d8a03b2833da2b4655047d` on the same macOS/Ubuntu and Python 3.11/3.13 matrix. All four jobs passed. The validated package reports:

- 11 courses;
- 134 shared skills;
- 20 nested labs;
- 10 Course 01 certification overlays;
- 8 job-training packs;
- `current_focus: null`;
- schema `humanos.academy.package.v1`;
- status `VALID`.

Routing/status evidence was also recorded in Work Router issue `#67`. No merge or promotion has occurred.

## Review findings

- Public Academy fixture is synthetic; real curriculum remains private.
- Default real learner-state DB was moved out of the repository into the private HumanOS home path.
- Coverage output is labeled `COVERAGE_NOT_CREDENTIAL_READINESS`.
- Evidence events do not silently promote a learner stage.
- Labs and certification overlays are subordinate to parent courses.
- Historical continuation data is preserved separately in the private repo; it is not silently imported as new live state.
- `TTX-001` remains historical unfinished work and is not current focus.

## Remaining pre-promotion gates

1. Owner review/approval of public PR `#118` and private PR `#1`.
2. Reconcile the public context registry entry for `HOS-LEARN-002` at promotion so the canonical registry points to the promoted commit and resume point rather than a moving feature head.
3. Merge/promote only after explicit owner authorization; then record final merge SHAs and checkpoint/resume state.

## Rollback

The slice is isolated to `feature/academy-kernel-runtime-v1`. Before promotion, rollback is branch deletion. After a future approved merge, rollback is revert of the promotion commit; no Life Notebook or existing mastery migration is performed by this slice.

## Current next action

Owner review of the two green candidate PRs. If approved, reconcile the canonical workstream registry at the exact promotion point, merge/promote in the governed order, record final SHAs, and then begin the next bounded Academy slice rather than expanding scope inside this workstream.
