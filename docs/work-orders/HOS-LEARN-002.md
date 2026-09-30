# HOS-LEARN-002 — Adaptive Academy Kernel & Runtime Vertical Slice

Status: ACTIVE
Workspace: `WS-HUMANOS`
Project: Learning and Mastery
Classification: `EXTEND` existing Academy/Mastery lineage
Branch: `feature/academy-kernel-runtime-v1`
Baseline: `runtime-0.1` at `a85462ccde61ea84e8f1cb680c7fdeefe04c97bf`
Related: `HOS-LEARN-001`, `HOS-MASTERY-001`

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

## Planned components

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
- `config/context_registry.public.json`

## Test / evidence plan

- Run targeted Academy unit tests.
- Run `python3 -m unittest discover -s tests -v`.
- Use GitHub Actions on the exact branch commit as remote evidence.
- Review the diff for private-data leakage, authority widening, destructive state behavior, and accidental coupling to private Academy content.
- Verify the package loader and SQLite state survive process/store restart through tests.

## Rollback

The slice is isolated to `feature/academy-kernel-runtime-v1`. Before promotion, rollback is branch deletion. After a future approved merge, rollback is revert of the promotion commit; no Life Notebook or existing mastery migration is performed by this slice.

## Current next action

Implement the generic package model/loader and teaching protocol, then the append-only Academy state store and CLI, followed by tests and CI verification.
