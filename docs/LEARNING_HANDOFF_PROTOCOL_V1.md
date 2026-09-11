# HumanOS Cross-LLM Learning Handoff Protocol v1

Status: candidate implementation contract.

## Principle
No LLM is expected to remember the learner across providers. During the manual phase, every teaching model receives a compact HumanOS Learning Passport and returns a structured Session Receipt. The receipt is later reconciled into HumanOS. When connectors exist, the same exchange becomes automatic.

## Canonical ownership
HumanOS owns canonical course state, skill evidence, goals, term/concept ledger, technology encounter ledger, assessments, provenance, and course versions. Provider chat history is a source record, not canonical learner state.

## Learning Passport — input to any LLM
Copy/paste this at the start of a study session:

```text
HUMANOS LEARNING PASSPORT v1
Human authority: learner controls goals, corrections, promotion, and course adoption.
Course: <course id + version>
Active goal: <goal or NONE>
Current lesson: <lesson>
Relevant skills: <skill | stage | mastery estimate | confidence | last evidenced>
Open questions/misconceptions: <items>
Recent concepts/terms: <items>
Recent technologies/tools: <items>
Next intended step: <step>

TEACHING RULES
- Teach naturally; do not optimize for engagement or completion.
- Do not claim mastery from conversation alone.
- Distinguish explanation from assessment.
- If assessing, state the task/rubric and preserve the learner's observable answer/result.
- New terms/concepts and technologies encountered must appear in the Session Receipt.
- Use UNKNOWN rather than inventing prior learner state.
- End the session, or whenever asked for metrics, by returning a HUMANOS SESSION RECEIPT v1.
```

## Session Receipt — output from any LLM

```text
HUMANOS SESSION RECEIPT v1
Provider: <provider>
Model/version: <exact if exposed, else UNKNOWN>
Session date/time: <timezone-aware if known>
Course/version: <course>
Lesson/topic: <topic>
Goal IDs: <ids or NONE>

TERMS / CONCEPTS ENCOUNTERED
- <canonical term> | NEW/REVISITED | short meaning | related skill

TECHNOLOGIES / TOOLS ENCOUNTERED
- <technology> | SEEN/INTRODUCED/PRACTICED/DEMONSTRATED | what happened | related skill

LEARNING EVIDENCE CANDIDATES
- Evidence type: USER_STATEMENT / OBSERVED_ACTION / TEST_RESULT / MODEL_ASSESSMENT / HUMAN_ASSESSMENT / INFERENCE / UNKNOWN
  Skill: <skill>
  K/P/D/C candidate scores: <0..5 only when actually assessed; otherwise UNASSESSED>
  Evidence: <concise observable evidence>
  Independence: ASSISTED / GUIDED / INDEPENDENT / UNKNOWN
  Confidence: <why this evidence is or is not strong>

ASSESSMENTS
- Status: UNASSESSED / CANDIDATE / VERIFIED
- Rubric/version: <id or NONE>
- Result: <result>
- Grader: model / deterministic-test / human / mixed

MISCONCEPTIONS / OPEN QUESTIONS
- <item>

NEXT RECOMMENDED STEP
- <one bounded step>

COURSE EVOLUTION CANDIDATES
- <new information or curriculum improvement; CANDIDATE only>

PROVENANCE / LIMITS
- <what the model observed directly vs what it inferred>
```

## Term / Concept Ledger
Terms and concepts are tracked separately from mastery. Encountering a term does not imply understanding it.

Recommended states:
- SEEN — appeared in material/conversation.
- INTRODUCED — learner received an explanation.
- USED — learner used the concept meaningfully.
- EXPLAINED — learner explained it in their own words with acceptable accuracy.
- APPLIED — learner applied it to a real/new problem.

Each entry should retain first_seen_at, last_seen_at, course(s), related skill(s), source session(s), state, correction/supersession references, and optional learner note.

## Technology Encounter Ledger
Technology/tool states remain:
SEEN -> INTRODUCED -> PRACTICED -> DEMONSTRATED -> MASTERED.
No model may silently promote MASTERED. Technologies may map to several skills and courses.

## Manual workflow now
1. HumanOS/ChatGPT generates the current Learning Passport.
2. Jon pastes it into DeepSeek, Claude, Gemini, Grok, or another model.
3. Study normally there.
4. At the end Jon says: `Generate my HUMANOS SESSION RECEIPT v1.`
5. Jon pastes the receipt back into the HumanOS control conversation.
6. HumanOS validates/reconciles it. Model judgments remain candidate evidence unless corroborated or human-approved.

This manual copy/paste flow is deliberately the same logical protocol future browser extensions, APIs, plugins, and local connectors should automate. The protocol therefore remains useful when the transport changes.

## Privacy
Only send the minimum Learning Passport needed for the lesson. Private Life Notebook content, secrets, credentials, unrelated projects, and personal history are excluded by default. A commercial provider's own chat retention is not HumanOS canonical storage.
