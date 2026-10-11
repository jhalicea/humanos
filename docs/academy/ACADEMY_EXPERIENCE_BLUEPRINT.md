# HumanOS Academy Experience Blueprint v0.1

Status: experience candidate under `HOS-LEARN-002`

## Product intent

HumanOS Academy should feel like a living AI training environment rather than a sequence of static lessons. The learner should be able to choose meaningful work, interact with different AI roles, encounter changing evidence and failure, see how skills connect, and produce real proof of capability.

The experience layer is downstream of the Academy kernel. It must not invent learner state, bypass privacy boundaries, or create a second progress system.

## Experience principles

### Agency before forced sequence

The Academy may recommend a next mission based on prerequisites, gaps, retention needs, certification/job mappings, or active projects, but recommendations do not become authority. The human chooses current focus.

### Missions rather than pages

A future Mission Board should offer bounded learning activities such as:

- investigate;
- build;
- debug/repair;
- explain/teach back;
- role-play a client or stakeholder conversation;
- review/red-team an artifact;
- perform a short retention challenge;
- continue a real HumanOS/Atlas/Academy project.

Every mission maps back to course/module/skill objects and recorded evidence. Missions are not a parallel curriculum.

### Real work over disposable exercises

Where safe and practical, Academy activities should improve a real system, investigation, report, workflow, dataset, communication skill, or HumanOS capability. Simulations remain useful when real-world execution would be unsafe, private, expensive, unavailable, or pedagogically premature.

### Difficulty from uncertainty, not trivia

Challenges should become interesting because evidence is incomplete, constraints conflict, systems fail, requirements change, or tradeoffs matter. The Academy should avoid confusing obscurity with rigor.

### Productive failure

A learner should sometimes meet a broken workflow, misleading clue, unsafe design, bad assumption, malformed input, or contradictory result before seeing the solution. The purpose is diagnosis and repair, not humiliation or arbitrary difficulty.

### Visible progression without fake gamification

Future UI may visualize skills, missions, streaks, achievements, or milestones, but the source of truth remains evidence-backed state. A visual reward must never substitute for evidence of capability.

## Experience surfaces

### Mission Board

The Mission Board answers: **what could I meaningfully do right now?**

Each mission should expose:

- course and module;
- target skills;
- mission type;
- estimated time;
- prerequisites/gaps;
- AI role(s);
- assistance level;
- expected evidence;
- whether it is recommended, due for revisit, certification-related, job-pack-related, or project-related.

A recommendation is descriptive, not a forced current focus.

### Skill Universe / Skill Map

A future visual graph should show shared skills across courses, labs, certifications, job packs, and projects. A skill node can expose:

- current stage;
- evidence-derived mastery estimate;
- prerequisites and dependent skills;
- last meaningful evidence;
- review/retention status;
- courses using the skill;
- labs exercising it;
- certification objectives mapped to it;
- job requirements mapped to it.

The graph must make shared learning visible so a skill learned once can support many paths.

### Scenario Simulator

Scenarios should reveal information incrementally in response to the learner's questions or actions. The AI can play clients, incident commanders, founders, analysts, reviewers, adversaries, or other bounded roles.

Examples of state changes:

- a new log contradicts the first hypothesis;
- a provider API fails;
- a client changes the requirement;
- a dataset contains leakage;
- a suspicious transaction turns out to have a benign explanation;
- a stakeholder asks for a decision before evidence is complete.

The simulator should record decisions and evidence boundaries rather than rewarding confident guessing.

### Review and Examiner modes

Review mode may provide critique, hints, and alternative interpretations. Examiner mode minimizes help, preserves the task, and records independent performance. Assistance level should be part of provenance when it materially affects mastery claims.

### Portfolio / proof surface

Evidence-backed artifacts may later be surfaced as a portfolio or competency record. The learner controls what leaves private Academy state. Public portfolio publication is a separate governed action.

## Modern AI interaction model

The AI should be able to switch function without pretending to be multiple authoritative systems:

```text
Tutor       -> build mental model
Coach       -> scaffold and hint
Client      -> create discovery/communication context
Colleague   -> collaborate on real work
Reviewer    -> challenge rationale and evidence
Red Team    -> seek failure or unsafe assumptions
Examiner    -> measure independent performance
Novice      -> trigger teach-back
```

The same model may serve several roles in a session, but each role transition should be explicit enough that the learner understands whether help is being provided or performance is being measured.

## Session shapes

HumanOS should support several session lengths without breaking the teaching protocol:

- **5–10 minute retrieval** — one skill, one prediction/teach-back, one small evidence event.
- **15–30 minute mission** — short concept + hands-on challenge + diagnostic variation.
- **45–90 minute lab** — multi-skill build/investigation with failure, repair, explanation, and evidence.
- **multi-session project** — checkpointed work with explicit current focus and clean resumption across AI providers.

## Adaptive behavior

Future recommendation logic may consider:

- prerequisites;
- evidence gaps;
- retention/revisit timing;
- learner-selected goals;
- current project needs;
- certification overlays;
- job-pack gaps;
- recent failure patterns;
- desired session duration;
- requested challenge/assistance level.

It must not infer that the oldest unfinished activity is the correct next activity.

## Anti-patterns

The Academy should reject these product patterns:

- giant AI lectures before eliciting the learner's thinking;
- automatic completion because content was opened;
- grading based only on fluent conversation;
- certificates implemented as duplicate courses;
- throwaway labs disconnected from skills;
- hidden state living only in chat history;
- fake precision in readiness percentages;
- leaderboard pressure that rewards speed over understanding;
- AI doing the assessed work and then grading the human as if they did it;
- provider-specific features becoming architectural dependencies without a portable abstraction.

## Experience roadmap after the v0.1 kernel

The next experience-oriented slices should be implemented one at a time against the same kernel:

1. private master curriculum package and import qualification;
2. Mission Board recommendation/query layer;
3. richer lesson/session event model and assistance provenance;
4. Skill Universe graph/query API;
5. spaced revisit scheduler;
6. dynamic scenario state machine;
7. Mirror/desktop visual Academy interface;
8. portfolio/certification/job-pack dashboards;
9. multi-model examiner/reviewer qualification and disagreement handling.

Each should use the HumanOS SDLC and preserve the same private/public boundary.
