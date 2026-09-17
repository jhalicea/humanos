# HE-0410 — HumanOS Engineering Organization and Delivery Standard v0.1

**System:** HumanOS  
**Instrument ID:** HE-0410  
**Version:** v0.1  
**Lifecycle:** Local Re-Bootstrap  
**Status:** CANDIDATE — NOT RATIFIED  
**Owner / final authority:** Jon Alicea  
**Implementation status:** DOCUMENTED / MANUAL ONLY  
**Provider dependency:** None  
**Parent lineage:** HE-0400, HW-0300, HAI-0600, HOS-GOV-001, current repository testing/evidence guidance

> HumanOS engineering is a human-commanded organization. Intelligence may scale; authority remains governed.

---

## 0. Purpose

HE-0410 defines how HumanOS organizes engineering work when one human principal can command multiple AI, software, and human-assisted workers.

It standardizes:

- who decides;
- who owns delivery;
- who independently challenges delivery;
- who checks governance and security;
- how workers are selected and bounded;
- how token, time, compute, privacy, and cost are managed;
- how work moves from idea to verified result;
- how HumanOS avoids both under-governance and bureaucracy.

HE-0410 is subordinate to the current constitutional/Foundation authority and does not replace HE-0400, HW-0300, or HAI-0600.

---

# 1. Organizational model

HumanOS engineering is a **human-led, AI-augmented engineering organization**.

The organization may be small in human headcount while large in available cognitive and software labor.

```text
                         JON
        Human Principal / Owner / Final Authority
                Final decision + final review
                          |
              +-----------+-----------+
              |                       |
              v                       v
       CHIEF ENGINEER          PRINCIPAL ENGINEER
       Delivery / execution     Independent technical
       organization             challenge / red team
              |                       |
        workers / leads          no normal delivery
              |                  command authority
              +-----------+-----------+
                          |
                          v
                        AEGIS
        Governance / security / privacy / evidence
                 / authority assurance
                          |
                          v
                         JON
```

The diagram describes functions, not permanent provider identities.

A role may be filled by a qualified local model, external model, deterministic service, human collaborator, or future runtime according to policy. Replacing a model does not replace the role.

---

# 2. Human Principal

## 2.1 Role

Jon is the Human Principal, owner, and final authority of HumanOS.

The Human Principal controls:

- mission and product direction;
- priority among competing work;
- constitutional and Foundation ratification;
- consequential approval;
- risk acceptance;
- delegation boundaries;
- final dispute resolution;
- promotion/rejection of major engineering outcomes.

## 2.2 Delegation does not surrender ownership

The Human Principal does not need to perform every intermediate task.

The Human Principal may delegate research, architecture, implementation, testing, review, documentation, operations, and evaluation while retaining the right to inspect, narrow, pause, revoke, reject, or redirect the work.

## 2.3 Final review

For consequential promotion, the Human Principal receives a concise decision packet containing:

- objective;
- current state;
- material changes;
- worker organization used;
- evidence and tests;
- Principal Engineer findings where required;
- AEGIS findings where required;
- actual/estimated resource use;
- unresolved disagreements;
- known limitations and residual risk;
- rollback/recovery path;
- recommended next action.

The Human Principal is not required to reread every intermediate worker transcript before deciding, but the underlying evidence must remain available when material.

---

# 3. Chief Engineer

## 3.1 Mission

The Chief Engineer owns **delivery orchestration**.

The Chief Engineer is accountable for turning an authorized objective into the smallest useful verified result.

## 3.2 Responsibilities

The Chief Engineer SHALL, as applicable:

1. understand the objective and acceptance criteria;
2. inspect the existing system before change;
3. establish the baseline;
4. decompose the work into bounded tasks;
5. classify risk;
6. decide which work is deterministic versus model-assisted;
7. select the least-scarce sufficiently capable qualified workers;
8. define each worker's context, authority, budget, stop conditions, and output contract;
9. supervise progress and failures;
10. reassign/escalate only when evidence justifies it;
11. integrate outputs;
12. ensure required tests are executed;
13. preserve evidence and limitations;
14. report resource usage truthfully;
15. prepare the work for Principal Engineer, AEGIS, and Human Principal review as required;
16. report one clear next action.

## 3.3 Chief Engineer is not sovereign

The Chief Engineer SHALL NOT:

- ratify its own governing authority;
- silently expand permissions;
- weaken review because of token/cost pressure;
- certify its own implementation as independently verified;
- hide failed workers, retries, discarded approaches, or material dissent;
- redefine constitutional or Foundation rules through ordinary engineering judgment;
- make a provider/model permanently synonymous with the Chief Engineer role.

## 3.4 Chief Engineer may delegate management

For larger work, the Chief Engineer may create temporary technical leads or worker groups.

Delegation remains bounded by the invariant:

```text
child_authority ⊆ parent_authority ⊆ owner_grant
```

A worker or lead cannot delegate a permission, tool, data scope, or authority that it does not possess.

---

# 4. Principal Engineer / Independent Technical Reviewer

## 4.1 Mission

The Principal Engineer provides **independent technical assurance**.

The Principal Engineer red-teams the Chief Engineer's design, worker organization, assumptions, resource allocation, tests, integration, and claims.

## 4.2 Parallel, not superior

The Principal Engineer is not a second delivery boss and does not normally command the Chief Engineer's workers.

The Chief Engineer owns execution.

The Principal Engineer owns challenge.

When they disagree materially, the disagreement is preserved and escalated through the applicable workflow rather than resolved by hidden hierarchy.

## 4.3 Review scope

The Principal Engineer asks questions such as:

- Is the architecture simpler than it needs to be?
- Was the problem decomposed correctly?
- Was deterministic software overlooked?
- Were too many workers spawned?
- Was an expensive frontier worker used unnecessarily?
- Was a weak/cheap worker used where repeated failure made it more expensive overall?
- Did a worker receive more private context than necessary?
- Are supposedly independent reviewers actually independent?
- Are tests meaningful, reproducible, and tied to acceptance criteria?
- Did the Chief optimize local cost while creating hidden review/rework cost?
- Is the implementation consistent with the existing system rather than creating a parallel runtime?
- Is the process itself over-engineered?

## 4.4 Principal Engineer output

A technical review SHOULD state:

```text
TECHNICAL REVIEW
work_item:
subject_commit_or_artifact:
reviewer_role: Principal Engineer
independence: independent | non_independent | partial | unknown

architecture: pass | challenge | partial
work_decomposition: pass | challenge | partial
worker_selection: pass | overpowered | underpowered | risky | partial
resource_strategy: pass | wasteful | insufficient | unknown
privacy_context_minimization: pass | challenge | partial
verification_design: pass | challenge | partial
complexity: justified | reduce | unknown

critical_findings: []
recommended_corrections: []
unresolved_disagreements: []
limitations: []
```

## 4.5 No self-certification

The Principal Engineer does not become independent merely because it is labeled Principal Engineer.

If the same exact model/runtime built the work and then reviews it without meaningful independence, the review SHALL be labeled `NON_INDEPENDENT` or `PARTIAL`, not independent certification.

---

# 5. AEGIS

## 5.1 Mission

AEGIS is the independent governance and assurance function around Engineering.

Engineering asks:

> How do we accomplish the mission well?

AEGIS asks:

> Was the work authorized, bounded, secure, privacy-preserving, evidence-backed, auditable, and truthful?

## 5.2 Scope

AEGIS may include or coordinate:

- constitutional review;
- security review;
- privacy review;
- permission/authority review;
- evidence and provenance audit;
- independent verification;
- Investigation;
- FRIENDS/adversarial challenge;
- meta-oversight of reviewers themselves.

## 5.3 AEGIS does not manage delivery

AEGIS SHALL NOT become the Chief Engineer by another name.

It does not normally optimize implementation sequence, assign routine workers, or own feature delivery.

It may block or escalate a transition only where a governing rule, risk gate, permission boundary, or explicit Human Principal decision grants that function.

## 5.4 AEGIS also reviews the Principal Engineer

The Principal Engineer is subject to AEGIS review.

Independent technical review does not place the reviewer outside governance.

---

# 6. Workers

## 6.1 Worker definition

A worker is a bounded participant assigned a specific task, role, context, budget, tool set, authority envelope, and output contract.

A worker may be:

- deterministic code;
- local language model;
- hosted language model;
- research tool;
- coding tool;
- test runner;
- document processor;
- human collaborator;
- future specialist runtime.

## 6.2 Role before model

HumanOS assigns a **role**, then selects a runtime capable of filling that role.

Examples:

- Research Worker;
- Implementation Worker;
- Test Worker;
- Documentation Worker;
- Security Challenger;
- Independent Verifier;
- Local Batch Worker;
- Specialist Reviewer.

A role is stable organizational meaning. The model/runtime is replaceable.

## 6.3 Worker contract

Every nontrivial worker assignment SHOULD define:

```yaml
worker_assignment:
  assignment_id: <stable-or-workflow-local-id>
  workflow_id: <workflow>
  role: <role>
  runtime_or_model: <known id or UNKNOWN>
  provider: local | external | human | deterministic | unknown
  objective: <bounded objective>
  authority:
    allowed_actions: []
    forbidden_actions: []
    allowed_data: []
    forbidden_data: []
  context_refs: []
  budget:
    token_budget: <known | estimated | unlimited_by_workflow | UNKNOWN>
    money_budget: <known | estimated | none | UNKNOWN>
    time_budget: <known | estimated | UNKNOWN>
    compute_budget: <known | estimated | UNKNOWN>
  output_contract: <expected result>
  verification: <how result will be checked>
  stop_conditions: []
  escalation_conditions: []
```

Unknown metadata remains `UNKNOWN`.

---

# 7. Resource-aware engineering

## 7.1 Optimization objective

The Chief Engineer SHOULD optimize for the **best verified result at the lowest total task cost consistent with required quality, privacy, security, and authority**.

Total cost is broader than API price.

```text
TOTAL TASK COST ≈
  token usage
+ monetary cost
+ elapsed time
+ local compute / energy
+ retry cost
+ supervision cost
+ review cost
+ correction / rework cost
+ privacy exposure
+ operational risk
+ opportunity cost of scarce high-capability workers
```

The formula is conceptual. It does not require false precision.

## 7.2 Least-scarce sufficiently capable worker

HumanOS SHOULD use the **least-scarce sufficiently capable qualified worker**.

This means:

- exact deterministic tasks go to deterministic code when reliable;
- repetitive low-risk work should prefer qualified local/inexpensive workers;
- ambiguous or specialized work should go to an appropriate specialist;
- frontier/high-cost intelligence should be reserved for work that benefits materially from it;
- independent high-risk review uses a reviewer appropriate to consequence and uncertainty.

It does **not** mean always choose the cheapest worker.

A cheap worker that causes repeated failures, retries, contamination, or expensive cleanup may have a higher total cost than a stronger worker used once.

## 7.3 Privacy eligibility precedes price

Resource routing SHALL evaluate at least:

```text
privacy / data eligibility
      -> authority eligibility
      -> required capability
      -> qualification evidence
      -> specialization fit
      -> total expected cost / scarcity
      -> availability / latency
```

A cheaper worker that is not eligible to receive the data is not a valid option.

## 7.4 Scarcity invariant

Scarcity may reduce:

- speed;
- depth;
- convenience;
- parallelism;
- model capability;
- scope of optional analysis.

Scarcity SHALL NOT silently reduce:

- human authority;
- constitutional rights;
- privacy boundaries;
- required permissions;
- security controls;
- required evidence;
- required independent review;
- truthful status;
- rollback/recovery requirements.

When resources are insufficient, HumanOS should wait, narrow, defer, reroute, or request a decision rather than fake completion.

---

# 8. Risk-tiered review

Risk-tiered review prevents both unsafe speed and bureaucratic paralysis.

The highest applicable risk factor determines the lane unless a governing rule explicitly says otherwise.

A worker may recommend raising its lane. It may not lower its own lane to bypass review.

## 8.1 GREEN

Typical characteristics:

- reversible;
- low consequence;
- bounded scope;
- no secrets/private data or only already-authorized local handling;
- no authority changes;
- no destructive external action;
- normal documentation, tests, formatting, deterministic maintenance, or small code fixes.

Default process:

```text
Chief Engineer / delegated worker
  -> implementation
  -> tests/readback
  -> evidence
  -> promote within standing authority
```

Principal Engineer and AEGIS may sample/audit GREEN work rather than review every item.

## 8.2 AMBER

Typical characteristics:

- new module or meaningful architecture choice;
- significant refactor;
- external service/model involvement;
- private or sensitive context;
- nontrivial migration;
- meaningful cost/resource use;
- uncertain behavior or integration risk;
- broad worker organization.

Default process:

```text
Chief Engineer
  -> workers
  -> tests/evidence
  -> Principal Engineer technical review
  -> targeted AEGIS review as applicable
  -> Jon approval where consequence/privacy/external action requires it
  -> promote
  -> runtime verify
```

## 8.3 RED

Typical characteristics:

- Constitution/Foundation/authority changes;
- permission/security boundary changes;
- secrets/credentials;
- destructive or difficult-to-reverse actions;
- consequential privacy changes;
- financial/legal/public identity effects;
- unattended agent authority;
- major release or migration with material rollback risk;
- high-impact external action.

Default process:

```text
Chief Engineer
  -> bounded implementation/evidence
  -> Principal Engineer independent technical review
  -> AEGIS full applicable review
  -> Jon explicit approval
  -> promotion
  -> runtime verification
  -> evidence closure / rollback if needed
```

RED review does not mean every reviewer has veto sovereignty. It means the required evidence and findings must be visible before the Human Principal decides.

---

# 9. Development operating method

HumanOS uses a hybrid operating method rather than rigid adherence to one framework.

## 9.1 Lean

Prefer:

- smallest useful reversible change;
- fewer handoffs;
- less duplicate documentation;
- deterministic automation where justified;
- work that produces measurable value;
- removal of process that no longer prevents meaningful failure.

## 9.2 Kanban

Engineering work SHOULD be visually representable as flow.

The canonical workflow state remains HW-0300; a board is only a view.

Suggested operational view:

```text
BACKLOG
  -> READY
  -> ACTIVE
  -> REVIEWING
  -> VERIFYING
  -> READY_FOR_PROMOTION
  -> PROMOTED
  -> VERIFIED
  -> ARCHIVED
```

Side states:

```text
WAITING
BLOCKED
CANCELLED
REOPENED
```

These map to existing HW-0300 concepts and SHALL NOT create a second source of workflow truth.

## 9.3 Work-in-progress limit

During bootstrap, HumanOS SHOULD keep **one primary implementation slice active at a time**, while allowing bounded research/review/support tasks necessary to complete that slice.

The purpose is focus, not artificial scarcity.

A larger WIP limit may be explicitly chosen when parallelism has demonstrated value and sufficient review capacity exists.

## 9.4 Agile incremental delivery

Large goals SHOULD be divided into inspectable increments that can produce evidence before the entire roadmap is complete.

Feedback from working behavior may change later plans without silently rewriting historical decisions.

## 9.5 Formal SDLC

HumanOS engineering SHALL preserve the semantic sequence already established by HE-0400/HW-0300:

```text
REQUEST / INTAKE
  -> AUTHENTICATE / AUTHORITY CHECK
  -> INSPECT
  -> BASELINE
  -> WORK ORDER / PLAN
  -> ISOLATED CHANGE
  -> IMPLEMENT
  -> TEST
  -> TECHNICAL REVIEW
  -> AEGIS REVIEW AS REQUIRED
  -> HUMAN APPROVAL AS REQUIRED
  -> PROMOTE
  -> RUNTIME VERIFY
  -> CLOSE / ARCHIVE / ROLLBACK
```

## 9.6 DevSecOps

Security, privacy, evidence, recovery, and operability are considered during design and implementation, not added as ceremonial final checks.

## 9.7 Research and experiments

When the correct engineering choice is genuinely uncertain, the Chief Engineer SHOULD create a bounded experiment rather than disguise preference as fact.

Experiment results are evidence, not automatic architectural law.

---

# 10. Work hierarchy

HumanOS work may be organized conceptually as:

```text
MISSION / PRODUCT VISION
  -> ROADMAP
  -> EPIC
  -> WORK ITEM
  -> WORK ORDER
  -> TASK / WORKER ASSIGNMENT
  -> ARTIFACT + EVIDENCE
  -> REVIEW / DECISION
  -> RELEASE / VERIFIED STATE
```

Special work products include:

- RFC / design proposal — material change requiring alternatives and tradeoffs;
- ADR / decision record — records a chosen architecture decision and reconsideration conditions;
- EXP / experiment — tests uncertainty;
- DEFECT — verified or suspected failure requiring disposition;
- POSTMORTEM — reconstructs material failure and prevention;
- RELEASE record — identifies promoted version and evidence.

Existing stable IDs SHALL NOT be renamed to fit this vocabulary. A future registry migration may standardize new IDs after duplicate/preflight checks.

---

# 11. Definition of Ready

A nontrivial engineering work item is **READY** only when enough information exists to begin without inventing the mission.

Minimum Ready fields:

- objective;
- owner;
- governing/authority references;
- baseline or baseline plan;
- scope boundaries;
- acceptance criteria;
- risk lane;
- required evidence;
- rollback/recovery expectation;
- known blockers/dependencies;
- initial resource/delegation plan where workers are used.

Not every GREEN task requires a large document. The information may be concise.

---

# 12. Definition of Done

An engineering work item is not DONE because a worker says it is done.

Applicable completion evidence includes:

- implementation/artifact exists;
- changed scope is known;
- acceptance criteria have evidence;
- required tests/readback were actually executed;
- important failure paths were considered/tested as required;
- Principal Engineer review is resolved where required;
- AEGIS review is resolved where required;
- Human Principal approval is recorded where required;
- limitations and unresolved risk are explicit;
- rollback/recovery path is known where applicable;
- promoted runtime behavior is verified where promotion occurred;
- material evidence is preserved;
- one next action or closure statement is recorded.

If an independent verifier was unavailable when required, the work cannot silently become `VERIFIED`; it remains `UNVERIFIED`, `PARTIAL`, or `BLOCKED` according to workflow policy.

---

# 13. Chief Engineer report contract

At a meaningful checkpoint or completion, the Chief Engineer SHOULD report:

```yaml
engineering_report:
  work_item: <id>
  objective: <plain language>
  current_state: <HW-0300-compatible state>
  risk_lane: green | amber | red

  organization:
    chief_engineer: <role/runtime>
    principal_engineer: <role/runtime or not_required>
    aegis_review: <status>
    workers: []

  resource_summary:
    tokens: <known | estimated | UNKNOWN>
    monetary_cost: <known | estimated | UNKNOWN>
    elapsed_time: <known | estimated | UNKNOWN>
    retries: <count | UNKNOWN>
    local_compute: <known | estimated | UNKNOWN>
    major_scarce_workers_used: []

  changes: []
  tests_and_evidence: []
  failures_and_retries: []
  principal_findings: []
  aegis_findings: []
  unresolved_disagreements: []
  limitations: []
  residual_risk: []
  rollback_or_recovery: <summary>
  recommendation: <promote | revise | defer | rollback | reject>
  one_next_action: <single next action>
```

The report is concise operational truth, not marketing.

---

# 14. Anti-bureaucracy rules

Governance exists to prevent meaningful failure, not to manufacture paperwork.

The following rules apply:

1. GREEN work does not require RED ceremony.
2. Reviews MAY be sampled for low-risk repetitive work when policy permits.
3. One record may satisfy multiple documentation needs when it preserves the required information.
4. Do not create a meeting/ceremony merely because Scrum uses one.
5. Do not use a frontier model where deterministic or qualified local work is sufficient.
6. Do not create a new role if a temporary assignment is enough.
7. Do not create a new database because a Markdown/YAML/manual record proves the workflow first.
8. The Principal Engineer SHOULD challenge process complexity itself.
9. AEGIS SHOULD distinguish real governance risk from aesthetic preference.
10. If a control repeatedly adds cost without preventing a meaningful failure class, propose simplification through the governed change process.

---

# 15. Manual bootstrap procedure

Until the organization is implemented in software, each meaningful engineering slice can use this lightweight procedure:

```text
1. Jon states/approves objective.
2. Chief Engineer creates/updates work item and risk lane.
3. Chief establishes baseline and acceptance criteria.
4. Chief chooses deterministic/local/external workers and budgets.
5. Workers execute bounded assignments.
6. Chief inspects/integrates outputs and runs tests.
7. Principal Engineer reviews AMBER/RED work; GREEN may be sampled.
8. AEGIS checks according to risk and governing requirements.
9. Jon decides consequential promotion.
10. Runtime/result is verified and evidence preserved.
11. Chief reports one next action.
```

This procedure is intentionally usable in an ordinary chat plus Git/evidence records before dedicated orchestration software exists.

---

# 16. Future implementation path

HE-0410 does not authorize a large agent platform.

A prudent implementation sequence is:

```text
Phase 0 — manual standard + template
Phase 1 — durable work-item/workflow object
Phase 2 — worker registry / Model Passport linkage
Phase 3 — deterministic authority envelope + budget checks
Phase 4 — Chief Engineer routing assistance
Phase 5 — Principal/AEGIS review gates
Phase 6 — bounded worker orchestration
Phase 7 — measured automation only where evidence shows value
```

Each phase requires its own work order, tests, evidence, and review.

---

# 17. Acceptance criteria

HE-0410 v0.1 is acceptable as a local candidate only if it:

- keeps Jon as final Human Principal;
- distinguishes Chief Engineer delivery from Principal Engineer technical challenge;
- keeps AEGIS independent from Engineering management;
- makes worker roles replaceable across providers/models;
- preserves `child_authority ⊆ parent_authority ⊆ owner_grant`;
- prohibits fake independent self-review;
- defines resource-aware routing including tokens/time/money/rework/privacy;
- places privacy/authority eligibility before price;
- prevents scarcity from weakening safeguards;
- uses GREEN/AMBER/RED proportional review;
- maps delivery flow to HW-0300 rather than inventing a competing state machine;
- defines Ready, Done, and Chief Engineer reporting;
- starts manual and anti-bureaucratic;
- does not claim runtime implementation or ratification.

---

# 18. Status

**CANDIDATE — NOT RATIFIED — DOCUMENTED/MANUAL ONLY.**

Creating this Instrument does not create live worker orchestration, a model router, AEGIS automation, or any new runtime permission.

---

# 19. One next action

Apply HE-0410 manually to one real HumanOS implementation slice—preferably the next Workflow Kernel / Life Notebook engineering work—then record friction, actual resource use, review burden, and missing fields before automating the organizational model.