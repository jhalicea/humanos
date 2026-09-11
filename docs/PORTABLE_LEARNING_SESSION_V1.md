# HumanOS Portable Learning Session v1

Status: candidate implementation contract.

## Purpose
HumanOS learning must work in ChatGPT, Gemini, Claude, Grok, DeepSeek, a local Ollama model, or a future provider without making the provider the owner of the learner record.

The conversation/model is the **teaching surface**. HumanOS is the **record and evidence authority**.

## Session envelope
Every study session that is intentionally recorded should be normalizable to:

```json
{
  "schema": "humanos.learning_session.v1",
  "session_id": "opaque-id",
  "started_at": "timezone-aware ISO-8601",
  "course_id": "ai-systems",
  "goal_ids": [],
  "provider": "openai|google|anthropic|xai|deepseek|local|other",
  "model": "exact identifier if exposed, otherwise UNKNOWN",
  "lesson": "Transformer Architecture From the Inside",
  "concepts_encountered": [],
  "candidate_evidence_ids": [],
  "assessment": {
    "status": "UNASSESSED|CANDIDATE|VERIFIED",
    "grader": "model|deterministic-test|human|mixed",
    "rubric_version": "...",
    "scores": {},
    "confidence": "..."
  },
  "provenance": {},
  "notes": []
}
```

## Grade rule
A provider/model may explain, question, challenge, or propose an assessment. It may not silently mutate canonical mastery.

A grade must preserve:
- what was tested;
- rubric/version;
- raw or referential evidence;
- provider/model identity when relevant;
- whether the result was model judgment, deterministic execution, human assessment, or mixed;
- uncertainty/confidence;
- timestamp and provenance.

The same evidence should produce the same deterministic HumanOS calculation regardless of which LLM is displaying the lesson.

## Portability rule
Provider-specific chat history is not the canonical learner state. The portable state is HumanOS-owned structured data: skills, evidence, encounters, assessments, goals, course versions, and provenance. A new LLM should be able to resume from a bounded Learning Context Packet rather than needing the complete historical conversation.

## Learning Context Packet
A future adapter should be able to export a minimal packet containing:
1. course/version and current lesson;
2. active goals;
3. relevant skill states and confidence;
4. recent evidence references;
5. concepts already encountered;
6. unresolved misconceptions/open questions;
7. next recommended lesson/action;
8. HumanOS grading/governance rules.

This packet is intentionally provider-neutral and privacy-minimized.

## Life Notebook relationship
The Life Notebook may retain the chronological learning event and provenance. The mastery engine retains normalized learning evidence/state. The same event can be referenced by both systems without turning every notebook event into a grade.

## Human authority
The human can study anywhere, decline an assessment, challenge a grade, correct provenance, change goals, or stop a course. Completion is a bounded finish line, not a declaration that the human knows everything.
