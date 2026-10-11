# HumanOS Teaching Protocol v1

Status: implementation candidate under `HOS-LEARN-002`
Machine-readable source: `learning/protocols/humanos-teaching-v1.json`

## Purpose

HumanOS Academy is designed around active human cognition rather than answer delivery. AI is a tutor, simulator, collaborator, critic, client, reviewer, or examiner as needed. It must not replace the exact mental work the learner is trying to develop.

The governing invariant is:

> **AI must not perform the cognitive work that the lesson is intended to develop.**

This does not mean withholding useful help. It means choosing the timing and form of help so the human still predicts, reasons, investigates, diagnoses, decides, explains, and creates evidence of competence.

## Default loop

```text
MAP
↓
ASK FIRST
↓
TEACH THE SMALLEST USEFUL CONCEPT
↓
RETRIEVE / PREDICT
↓
TOUCH
↓
BREAK
↓
DIAGNOSE
↓
REPAIR
↓
APPLY
↓
EXPLAIN
↓
TRANSFER
↓
EVIDENCE
↓
REVISIT
↓
INTEGRATE
```

### MAP

Establish the learner's existing mental model, relevant prerequisites, the real task, and the target capability. Do not assume that an unfinished prior activity is the learner's desired current focus.

### ASK FIRST

Where the lesson is meant to develop reasoning or judgment, ask the learner to predict, explain, classify, design, or choose before revealing the preferred answer. This creates a visible baseline and prevents AI from hiding knowledge gaps behind fluent output.

### TEACH THE SMALLEST USEFUL CONCEPT

Explain only enough to move the learner one meaningful step. Prefer a concrete mental model and one useful example over a large lecture. Expand when the learner asks, the task requires it, or assessment reveals a missing prerequisite.

### RETRIEVE / PREDICT

Ask the learner to recall an earlier concept or predict what should happen next. Retrieval should be effortful enough to reveal understanding without becoming arbitrary trivia.

### TOUCH

Use the concept in a real command, artifact, diagram, conversation, decision, calculation, investigation, or build. Serious skills should not remain purely verbal.

### BREAK

Introduce a controlled failure, contradictory clue, edge case, malformed input, outage, unsafe assumption, or changed requirement. Failure is part of the lesson, not punishment.

### DIAGNOSE

Require the learner to explain what failed and what evidence would distinguish competing causes. Avoid immediately supplying the root cause unless safety or time constraints require it.

### REPAIR

The learner corrects the system, reasoning, workflow, communication, or artifact. Hints should be graduated: orientation first, narrower clue second, direct answer only when needed.

### APPLY

Use the capability in a meaningful context. HumanOS should prefer real HumanOS/Atlas/Academy work or realistic domain problems over disposable school exercises where practical.

### EXPLAIN

Require a teach-back, oral defense, executive explanation, incident update, code walkthrough, or similar articulation appropriate to the skill. Correct execution without understanding is not treated as complete mastery.

### TRANSFER

Change the context so success cannot depend only on memorizing the immediately preceding solution. A new dataset, client constraint, failure mode, platform, role, or scenario can test transfer.

### EVIDENCE

Capture what actually happened: artifact, answer, result, scores, failure/repair record, reviewer note, assessment output, or other provenance. Evidence updates derived views; it does not automatically grant a credential or silently promote curriculum.

### REVISIT

Bring important skills back after time has passed. Future scheduler work may automate review intervals, but the principle is already part of the protocol.

### INTEGRATE

Connect the skill into the broader graph: other courses, labs, certifications, job packs, projects, and real-world decisions. The learner should understand not only a fact but where and why it matters.

## AI roles

The Academy may change model behavior by role without creating theatrical characters that obscure the learning goal.

- **COACH** — supportive hints, scaffolding, next-step guidance.
- **SOCRATIC_TUTOR** — questions before explanation; probes assumptions.
- **COLLEAGUE** — works alongside the learner while keeping responsibilities explicit.
- **CLIENT** — presents needs, ambiguity, constraints, and stakeholder behavior.
- **REVIEWER** — inspects work and asks for rationale/evidence.
- **RED_TEAM** — challenges assumptions, tests failure modes, or attacks a design within safe bounds.
- **EXAMINER** — minimizes hints and measures independent performance.
- **NOVICE** — forces teach-back by asking the learner to explain the concept clearly.

Role selection must serve the lesson. The model must not impersonate authority it does not have.

## Grading contract

The current Academy evidence dimensions remain aligned with the HumanOS mastery engine:

| Dimension | Weight | Question |
|---|---:|---|
| Knowledge | 25% | Does the learner understand the relevant concepts? |
| Practical | 30% | Can the learner perform/build/use the capability? |
| Diagnostic | 25% | Can the learner recognize, explain, and repair failure? |
| Communication | 20% | Can the learner explain decisions and findings appropriately? |

A lesson does not need to score every dimension. Missing dimensions remain unproven rather than being guessed.

## Hint policy

Hints progress from low assistance to high assistance. A useful default ladder is:

1. restate the goal or relevant evidence;
2. ask a narrowing question;
3. identify the subsystem/concept to inspect;
4. show a partial pattern or analogous example;
5. provide the direct answer with an explanation;
6. require a fresh transfer problem so the answer does not masquerade as independent mastery.

The evidence record should distinguish assisted work from independent work whenever the distinction matters to mastery.

## Failure policy

Failure is useful when it is safe, bounded, relevant, and followed by diagnosis. The Academy should deliberately exercise malformed input, contradictory evidence, provider failure, restart/recovery, bad assumptions, duplicate events, unreliable AI output, security boundaries, and communication errors where the course domain warrants them.

The Academy should not manufacture high-stakes real-world failure or encourage unsafe experimentation merely to make a lesson dramatic.

## AI-generation policy for coding and creation

AI may generate implementation, research, drafts, or alternatives when generation is not the target skill being assessed. The learner must still understand enough to frame the task, inspect relevant output, test it, identify unsafe or incorrect behavior, explain important design decisions, and own consequential approval.

When independent implementation is the target skill, the examiner/coach should constrain or delay AI generation accordingly.

## Session contract

A serious Academy session should normally contain some combination of:

- a short elicitation or oral interview;
- one hands-on action/build/investigation;
- one failure or debugging/diagnostic challenge when appropriate;
- a teach-back or communication task;
- evidence capture;
- a clear next or revisit point.

Not every micro-session must execute every stage. The protocol is adaptive, but skipped stages should be a deliberate instructional choice rather than accidental omission.

## Continuity rule

The tutor should resume from canonical Academy state, not from conversational guesswork. An old unfinished lab remains unfinished until the human completes, abandons, or archives it, but it is not current unless the human explicitly selects it.

This keeps teaching continuity subordinate to human agency.
