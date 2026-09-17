# HumanOS Foundation Control Index

**Lifecycle:** Local Re-Bootstrap  
**Status:** CANDIDATE CONTROL INDEX  
**Owner / final authority:** Jon Alicea  
**Implementation:** Documentation control plane only; no runtime authority change

## Purpose

This directory is the local, version-controlled working control plane for HumanOS Foundation governance.

It does not erase or rewrite the earlier ChatGPT / Google Drive Foundation period. Earlier ratifications, drafts, reviews, and artifacts remain historical and bootstrap evidence. They become current local authority only through an explicit local promotion and ratification record.

## Authority order during local re-bootstrap

1. Jon's explicit current decision.
2. Locally ratified HumanOS constitutional / Foundation instruments.
3. Locally approved subordinate standards and decisions.
4. Workflow and permission enforcement.
5. Verified implementation and runtime evidence.
6. Imported historical/bootstrap artifacts and external reviews as evidence.
7. Model output, including FRIENDS, as proposals or review findings unless locally promoted.

No model, reviewer, external service, repository document, or historical artifact can grant itself authority.

## Controlled records

### Foundation Registry & Document-Control Recovery

- `MASTER_FOUNDATION_REGISTER.md` — identity/status registry for Foundation instruments.
- `LOCAL_AUTHORITY_AND_BOOTSTRAP_TRANSITION.md` — transition rule from historical ChatGPT/Drive bootstrap to local-first governance.
- `IDENTIFIER_AND_LIFECYCLE_STANDARD.md` — stable ID, chronology, lifecycle, and representation rules.
- `FDR-0004_CORRECTION_RECORD.md` — non-destructive correction for the mistaken HF-0100-unresolved claim.
- `SLICE_VERIFICATION.md` — evidence and limitations for the initial registry-recovery slice.

### HOS-DOC-001 — Document Workflow / Registry candidate

- `HOS-DOC-001_PREFLIGHT.md`
- `HD-0100_HumanOS_Document_and_Artifact_Governance_v0.1.md` — candidate; **not ratified**.
- `HD-0100_Document_Registry_Schema_v0.1.yaml` — non-authoritative projection.
- `HD-0100_Artifact_Registry_Schema_v0.1.yaml` — non-authoritative projection.
- `HOS-DOC-001_SLICE_VERIFICATION.md`

### HOS-GOV-001 — Constitutional Branches reconciliation

- `HOS-GOV-001_PREFLIGHT.md`
- `HOS-GOV-001_BRANCHES_RECONCILIATION.md` — historical-source reconciliation; **not constitutional law and not ratification**.
- `HOS-GOV-001_SLICE_VERIFICATION.md`

### HOS-CONST-001 — Local Constitutional Baseline reconciliation

- `HOS-CONST-001_PREFLIGHT.md`
- `HOS-CONST-001_RECONCILIATION_MATRIX.md`
- `HF-0200_HumanOS_Constitution_and_Human_Bill_of_Rights_v0.2-rc1.md` — preserved predecessor candidate; **never ratified**.
- `HOS-CONST-001_FRIENDS_CHALLENGE_PACKET.md` — earlier rc1 challenge packet; preserved.
- `HOS-CONST-001_SLICE_VERIFICATION.md`

### HOS-CONST-002 — Recovered FRIENDS evidence and constitutional hardening

- `HOS-CONST-002_FROZEN_FRIENDS_EVIDENCE_INDEX.md` — indexes five frozen September 14 independent Pass A constitutional reviews recovered from the HumanOS Library; model self-report is not treated as runtime-attested identity.
- `HOS-CONST-002_LEGACY_FINDINGS_REGRESSION.md` — regresses the frozen findings against rc1 and distinguishes resolved, partial, subordinate-standard, and unresolved issues.
- `HF-0200_HumanOS_Constitution_and_Human_Bill_of_Rights_v0.2-rc2.md` — current hardened constitutional **candidate; NOT RATIFIED**.
- `HOS-CONST-002_FRIENDS_DELTA_CHALLENGE_PACKET.md` — short fresh-review packet targeted only at rc2 repairs; **ready, not executed**.
- `HOS-CONST-002_SLICE_VERIFICATION.md` — evidence and limitations for this hardening slice.

### HOS-ENG-001 — AI-augmented engineering organization and delivery

- `HOS-ENG-001_PREFLIGHT.md` — confirms that HE-0410 specializes existing HE-0400/HW-0300/HAI-0600 rather than replacing them.
- `HE-0410_HumanOS_Engineering_Organization_and_Delivery_Standard_v0.1.md` — current engineering-organization **candidate; NOT RATIFIED; MANUAL ONLY**.
- `HE-0410_Manual_Engineering_Work_Item_Template_v0.1.yaml` — non-authoritative manual work-item/worker-assignment projection.
- `HOS-ENG-001_SLICE_VERIFICATION.md` — evidence and limits of the standardization slice.

HE-0410 defines the current candidate organizational pattern:

```text
Jon — Human Principal / final decision & review
  |
  +-- Chief Engineer — delivery, decomposition, delegation, resources, integration, reporting
  +-- Principal Engineer — independent technical red-team/review of Chief and worker organization
            |
          AEGIS — governance/security/privacy/evidence/authority assurance for both
```

Workers remain bounded, role-based, and replaceable. The authority invariant is:

```text
child_authority ⊆ parent_authority ⊆ owner_grant
```

The implementation worker cannot silently certify its own work as independent verification.

The resource rule is to use the **least-scarce sufficiently capable qualified worker**, considering total task cost: tokens, money, elapsed time, compute, retries, review, rework, privacy exposure, and failure risk. Privacy and authority eligibility come before price. Scarcity may reduce speed/depth/convenience; it may not reduce required rights, privacy, security, permission, evidence, or review.

Risk review remains proportional:

- GREEN — Chief/worker + tests/readback; Principal/AEGIS may sample.
- AMBER — Principal technical review plus targeted AEGIS as applicable.
- RED — Principal independent technical review + full applicable AEGIS + explicit Jon approval before consequential promotion.

## Local-first rule

HumanOS is built, tested, and canonically controlled locally. Git is the version-controlled engineering and sanitized governance record. Private evidence, Notebook content, secrets, sensitive model transcripts, and protected artifact-vault contents do not belong in the public repository.

External services may research, review, challenge, or propose. They do not directly mutate constitutional authority, permissions, or canonical runtime state.

## Current candidate state

### HD-0100

Document/Artifact governance is **CANDIDATE / NOT RATIFIED / NOT IMPLEMENTED**.

### Government / branches

The historical government architecture has been reconciled as source lineage. Human sovereignty; branches as functions rather than personalities; standards/rulemaking, executive/runtime, judicial/review, investigation, and oversight separation; external AI subordination; due process; and explicit human ratification are preserved without creating a second government Instrument.

### HF-0200 v0.2-rc2

The five recovered frozen FRIENDS reviews independently converged on several important pressure points in the historical Constitution: owner-authority authenticity/voluntariness, third-party boundaries, rights collisions, Mirror/recovery concentration, delegation/succession, consent lifecycle, and a lawful non-sovereign challenge path.

rc2 applies a deliberately small constitutional hardening delta and remains **NOT RATIFIED / NOT RUNTIME ENFORCED**. Its fresh independent delta challenge is still pending.

### HE-0410 v0.1

The Engineering Organization and Delivery Standard is **CANDIDATE / NOT RATIFIED / MANUAL ONLY**.

It intentionally starts small. It does not create autonomous worker spawning, a live model router, automated AEGIS, new runtime permissions, or a new canonical database.

Its development method combines Lean, Kanban, incremental Agile delivery, formal SDLC, DevSecOps, and research/evaluation discipline while rejecting ceremony that does not reduce meaningful failure.

The next evidence needed is a real manual pilot, not more architecture prose.

## Review truth boundary

The September 14 broad constitutional challenge was real and is preserved as historical evidence. It targeted the August Constitution, not rc2.

The current ChatGPT architect has inspected multiple frozen FRIEND outputs while performing regression/synthesis. Therefore it cannot truthfully count itself as a clean-room independent reviewer of rc2.

The fresh rc2 delta challenge remains intentionally **READY / NOT EXECUTED** until independent reviewers receive the delta packet without seeing one another's new answers first.

## Current active slice / one next action

**Pilot HE-0410 manually on the next bounded real HumanOS engineering work item, using the new work-item template and recording actual friction/resource/review evidence.**

The independent rc2 constitutional delta challenge remains queued for when independent reviewer access is available.

After the HE-0410 pilot:

1. preserve the actual work item, worker assignments, costs/usage where known, failures, reviews, and final report;
2. remove or simplify any HE-0410 field/process that creates cost without preventing a meaningful failure class;
3. add only the smallest deterministic workflow support proven useful by the pilot;
4. continue toward Workflow Kernel / Life Notebook implementation rather than building a large agent platform first.
