# HOS-ENG-001 — Engineering Organization & Delivery Preflight

**Work item:** HOS-ENG-001  
**Lifecycle:** Local Re-Bootstrap  
**Status:** PREFLIGHT COMPLETE — CANDIDATE WORK ONLY  
**Owner / final authority:** Jon Alicea  
**Date:** 2026-09-17  
**Implementation status:** DOCUMENTARY / MANUAL ONLY

## 1. Objective

Standardize how HumanOS engineering work is organized, delegated, reviewed, resource-managed, verified, and reported without creating a competing workflow system or a premature autonomous-agent runtime.

The immediate design target is a small human-led, AI-augmented engineering organization:

- Jon as Human Principal, final decision-maker, and final reviewer;
- a Chief Engineer accountable for delivery, decomposition, delegation, resource management, integration, and reporting;
- a Principal Engineer / Independent Technical Reviewer that red-teams the Chief Engineer and worker organization without becoming a second delivery boss;
- AEGIS as independent governance, security, privacy, evidence, and authority assurance for both engineering roles and their workers;
- replaceable workers with bounded roles, context, budgets, and permissions.

## 2. Duplicate / lineage check

Existing HumanOS sources already cover much of the required ground and SHALL be reused rather than replaced.

### HE-0400 — HumanOS Engineering Contract v0.1

Recovered source already establishes:

- Foundation before implementation;
- work orders for consequential change;
- preservation of the existing system;
- smallest useful reversible change;
- baseline before change;
- evidence before completion;
- normal and failure-path testing;
- proposal/certification separation;
- provider independence;
- protected roots;
- privacy by construction;
- split-brain prevention;
- rollback/supersession;
- human approval for consequential change;
- truthful implementation status;
- durable engineering memory.

Disposition: **DO NOT REPLACE.** Create a subordinate specialization that explains organizational roles, resource-aware delegation, and delivery flow.

### HW-0300 — HumanOS Workflow Governance Protocol v0.1

Recovered source already establishes:

- governed work belongs to workflow instances;
- workflow state is external to models;
- evidence is required for transitions;
- no self-certification where independent verification is required;
- proposal and certification are distinct;
- missing evidence is not completion;
- explicit scoped overrides;
- provider independence;
- human approval for ratification/high-risk action;
- history preservation;
- Engineering Workflow states and transition gates.

Disposition: **DO NOT CREATE A PARALLEL STATE MACHINE.** HE-0410 will profile the existing HW-0300 workflow for engineering organization and delivery.

### HAI-0600 — HumanOS AI Model and Authority Standard v0.1

Recovered source already defines workers, reviewers, challengers, Model Passports, Model Ledgers, least context, provider neutrality, replaceable runtimes, bounded agent participation, and review independence.

Disposition: **REUSE.** HE-0410 will define how the Chief Engineer assigns these roles during engineering work.

### HOS-GOV-001 — Branches / Review Court reconciliation

Current local reconciliation already preserves separation of functions, human sovereignty, independent review, FRIENDS as challengers rather than sovereigns, and the rule that resource scarcity changes routing rather than rights.

Disposition: **REUSE.** AEGIS remains governance/assurance, not Engineering management.

### Repository development guidance

Current repository documentation already states that:

- reproducible runtime behavior and tests outrank documentation/model agreement;
- changes should be narrowly scoped and reversible;
- private Notebook data, credentials, and client information do not belong in public contributions;
- model output is proposal until checked against evidence, permissions, and acceptance criteria.

Disposition: **REUSE AS CURRENT ENGINEERING EVIDENCE PRACTICE.**

## 3. Intended operation

**CREATE NEW SUBORDINATE ENGINEERING STANDARD**, not a new Constitution, not a replacement for HE-0400/HW-0300/HAI-0600, and not a runtime implementation.

Proposed Instrument identity:

- `HE-0410`
- `HumanOS Engineering Organization and Delivery Standard`
- initial version `v0.1`
- local state `CANDIDATE`

The 0410 number is semantic adjacency to HE-0400. It does not claim chronological priority and does not renumber any existing Instrument.

## 4. Required design constraints

HE-0410 SHALL preserve these invariants:

1. Jon remains Human Principal and final authority.
2. Chief Engineer owns delivery; Principal Engineer owns independent technical challenge.
3. Principal Engineer is parallel to, not command-superior to, the Chief Engineer.
4. AEGIS independently reviews governance/security/privacy/evidence/authority for both engineering roles.
5. Workers receive bounded task, context, budget, tools, and authority.
6. `child_authority ⊆ parent_authority ⊆ owner_grant`.
7. The implementer cannot be the sole independent verifier where independence is required.
8. Use the least-scarce sufficiently capable qualified worker.
9. Total task cost includes tokens, money, elapsed time, compute, retries, review, correction, privacy exposure, and failure risk.
10. Scarcity may reduce speed/depth/convenience; it may not reduce rights, privacy, required authorization, security, evidence, or required review.
11. Risk-tiered review SHALL prevent routine work from becoming bureaucratic.
12. Deterministic software is preferred when it can reliably perform the task.
13. Unknown usage/cost/model metadata remains `UNKNOWN`; it is not fabricated.
14. The design begins manual/documentary and grows into deterministic enforcement only after the workflow is proven useful.

## 5. Process-method disposition

HumanOS will not adopt one development religion.

The candidate operating model combines:

- **Lean:** remove waste and prefer the smallest useful change;
- **Kanban:** visualize flow and limit work in progress;
- **Agile:** deliver in small inspectable increments and adapt from evidence;
- **formal SDLC:** define, baseline, implement, test, review, approve, promote, verify, recover;
- **DevSecOps:** security/privacy/operability participate throughout rather than only at the end;
- **research/evaluation discipline:** uncertainty becomes experiments, benchmarks, red-team findings, and preserved evidence.

Scrum ceremonies and fixed sprints are optional, not constitutional requirements.

## 6. Initial implementation boundary

This slice MAY create:

- HE-0410 human-readable candidate;
- one structured manual work-item / worker-assignment template;
- a verification record;
- Foundation registry/index updates.

This slice SHALL NOT create:

- autonomous worker spawning;
- new runtime permissions;
- a live model router;
- automated AEGIS adjudication;
- an agent framework dependency;
- a new canonical database;
- ratification;
- merge to `runtime-0.1`.

## 7. Acceptance criteria

HOS-ENG-001 is complete as a documentary slice only if:

- existing HE-0400/HW-0300/HAI-0600 lineage is preserved rather than duplicated;
- organizational roles and boundaries are explicit;
- token/cost/time/resource routing is explicit;
- GREEN/AMBER/RED review is proportional and anti-bureaucratic;
- the workflow maps to existing HW-0300 states instead of inventing a competing lifecycle;
- the standard includes Definition of Ready and Definition of Done;
- the standard includes a Chief Engineer report contract;
- the manual template is usable before any agent runtime exists;
- status remains `CANDIDATE / NOT RATIFIED / NOT RUNTIME ENFORCED`.

## 8. One next action after this slice

Use HE-0410 manually on **one real HumanOS implementation work item** and collect friction/cost/evidence before automating the organization.