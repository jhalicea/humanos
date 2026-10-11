# Adaptive Mastery: Public Architecture

This document describes reusable learning software. It contains no real
learner record, course assignment, assessment result, or progress state.

## Model

The mastery engine separates three concerns:

1. **Catalog structure** describes skills, domains, prerequisites, and courses.
2. **Evidence records** capture dated observations with scores for declared
   dimensions. Evidence is associated with a skill and is not itself authority
   to change a curriculum or take an external action.
3. **Derived views** calculate mastery, completion, and gaps from the available
   evidence. They are estimates with explicit provenance, not grades or claims
   of universal competence.

The public engine provides reusable schemas and calculations. Real curricula,
learner-specific skill maps, grades, assessments, evidence, progress, and course
history belong in a private learning system. Public demonstrations and tests
use synthetic records only.

## Progression

A skill can move through the generic stages `unseen`, `introduced`, `assisted`,
`practiced`, `demonstrated`, and `mastered`. The engine does not infer that a
stage has been reached merely because a course was opened. Evidence updates
dimension scores; a separate governed action may change a stage or curriculum.

Course completion and mastery are distinct measures. Completion reports the
share of catalogued skills that have left `unseen`. Mastery summarizes the
engine's evidence-derived skill scores. Both are bounded estimates whose
meaning depends on the schema, evidence quality, and scoring policy in use.

## Synthetic example

The following identifiers and state are fictional demonstration data:

```json
{
  "course_id": "sample-course-foundations",
  "skill_id": "sample-skill-source-evaluation",
  "stage": "practiced",
  "scores": {"knowledge": 3.0, "diagnostic": 2.0}
}
```

The example illustrates shape only. Applications should keep the identity of a
learner, source evidence, assessment contents, and real score history in the
private system that owns those records.

## Learning loop and boundaries

Reusable software may propose a curriculum update from a set of sources. A
proposal remains a candidate until an authorized human or governed process
reviews and promotes it. Metrics do not promote curricula, establish
credential readiness, or trigger external actions by themselves.

Public HumanOS may contain generic catalog and mastery code, schemas,
architecture, and synthetic fixtures. Real course definitions tied to a
learner, personalized progress, grades, assessments, evidence, and course state
remain private. Job applications, employer pursuit, and interview preparation
belong to private career operations; generic labor-market or workflow models
must use synthetic examples.
