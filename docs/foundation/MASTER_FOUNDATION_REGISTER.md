# HumanOS Master Foundation Register

**Register ID:** HOS-REG-FOUNDATION-001  
**Lifecycle:** Local Re-Bootstrap  
**Status:** CANDIDATE REGISTER  
**Date:** 2026-09-17  
**Owner / final authority:** Jon Alicea  
**Scope:** Foundation, constitutional, workflow-governance, engineering, document-governance, human-model, AI-authority, and knowledge-kernel instruments

## Register law

This register answers **what artifact exists, what role it claims, and what HumanOS currently knows about its authority**.

Registration is not ratification. Recency is not authority. File location is not authority. Model agreement is not authority.

A historical status and a local status are separate facts.

## Status vocabulary

### Historical / source authority state

- `RATIFIED` — historical source records explicitly record owner ratification.
- `CANDIDATE` — source artifact explicitly identifies itself as candidate.
- `DRAFT` — source artifact explicitly identifies itself as draft.
- `SUPERSEDED` — source evidence explicitly identifies a successor.
- `UNKNOWN` — current evidence is insufficient; do not guess.
- `N/A_LOCAL_ORIGIN` — object originated in the local re-bootstrap and has no earlier historical authority state.

### Local re-bootstrap state

- `DISCOVERED` — identity is known but source has not been reconciled.
- `IMPORTED` — source is available to local governance as evidence/reference.
- `RECONCILED` — identity, lineage, representations, and authority have been compared.
- `CANDIDATE` — proposed for current local governance.
- `RATIFIED` — explicitly approved by Jon under the local workflow.
- `SUPERSEDED` — replaced for a defined scope while preserved historically.
- `REJECTED` — explicitly rejected.
- `ARCHIVED` — retained for history/reference; not active governance.

### Verification state

- `UNVERIFIED`
- `PARTIAL`
- `VERIFIED_SOURCE`
- `VERIFIED_RECONCILIATION`
- `FAILED`
- `DISPUTED`

## Identifier rule

Stable IDs express semantic identity and document family. They do **not** encode creation chronology.

Creation chronology is recorded separately through dates, commits, source timestamps, and provenance.

Existing stable IDs SHALL NOT be renumbered merely to make chronological ordering visually tidy.

Work-item identifiers and Instrument identifiers remain separate. For example, `HOS-DOC-001` identifies the historical work package while `HD-0100` identifies the resulting candidate Instrument.

## Current register

| Stable ID / key | Instrument / record | Historical/source state | Local state | Implementation state | Verification | Notes |
|---|---|---:|---:|---|---|---|
| HF-0000 | HumanOS Foundation v0.3 | CANDIDATE | IMPORTED | Not runtime implementation | VERIFIED_SOURCE | Drive package exists in Markdown/DOCX/PDF/YAML/manifest form. |
| HF-0100 | HumanOS Foundational Principles v0.1 | CANDIDATE | IMPORTED | Not implemented | VERIFIED_SOURCE | Located in Drive Foundation instruments. Earlier claim that this artifact was unresolved is corrected by `FDR-0004_CORRECTION_RECORD.md`. |
| HF-0150 | HumanOS Instrument Standard v0.1 | DRAFT / CANDIDATE bootstrap | IMPORTED | Not runtime implementation | VERIFIED_SOURCE | Created earlier chronologically than HF-0100 under disclosed bootstrap exception. ID order is semantic, not chronological. |
| HF-0160 | HumanOS Visual Instrument Standard v0.1 | DRAFT | IMPORTED | Not runtime implementation | VERIFIED_SOURCE | Visual projection/renderer rules; does not establish authority by appearance. |
| HF-0200-v0.1 | HumanOS Constitution and Human Bill of Rights v0.1 | Reconstruction CANDIDATE; explicitly not newly ratified | RECONCILED SOURCE | Not implemented | VERIFIED_RECONCILIATION | Reconciled with the historical August Constitution, Foundation ratification, local transition, HOS-GOV-001, and current owner direction in HOS-CONST-001. Preserved as predecessor/source; not silently promoted. |
| HF-0200-v0.2-rc1 | HumanOS Constitution and Human Bill of Rights v0.2-rc1 | N/A_LOCAL_ORIGIN; derived from historically ratified and candidate lineage | SUPERSEDED CANDIDATE | Constitutional text candidate only; no runtime enforcement | VERIFIED_RECONCILIATION | Regressed against five frozen September 14 FRIENDS reviews. Several material findings remained; preserved as predecessor to rc2. Never ratified. |
| HF-0200-v0.2-rc2 | HumanOS Constitution and Human Bill of Rights v0.2-rc2 | N/A_LOCAL_ORIGIN; hardened from rc1 using frozen FRIENDS evidence | CANDIDATE | Constitutional text candidate only; no runtime enforcement | PARTIAL | Current local constitutional candidate. Adds valid-owner-authority boundary, anti-paternalism guard, sovereignty scope, delegation/recovery/succession boundary, rights-collision rule, protected dissent, and bounded stay renewal. Requires fresh independent delta challenge before owner ratification review. |
| HW-0300 | HumanOS Workflow Governance Protocol v0.1 | CANDIDATE | RECONCILED SOURCE | Historical specification; deterministic Workflow Kernel not established by this register | VERIFIED_SOURCE | Recovered source defines external workflow state, evidence-gated transitions, no self-certification, human authority, workflow states, transition gates, and Engineering Workflow. HE-0410 profiles rather than replaces it. |
| HE-0400 | HumanOS Engineering Contract v0.1 | CANDIDATE | RECONCILED SOURCE | Historical specification; manual/current implementation varies by work item | VERIFIED_SOURCE | Recovered source defines work orders, baseline/evidence, smallest reversible change, risk lanes, independent review, truthful status, rollback, and human approval for consequential change. |
| HE-0410 | HumanOS Engineering Organization and Delivery Standard v0.1 | N/A_LOCAL_ORIGIN | CANDIDATE | DOCUMENTED / MANUAL ONLY | PARTIAL | Subordinate specialization of HE-0400/HW-0300/HAI-0600. Defines Human Principal, Chief Engineer, Principal Engineer technical assurance, AEGIS assurance, bounded workers, resource-aware routing, GREEN/AMBER/RED review, Ready/Done, and Chief Engineer reporting. Not ratified; no orchestration runtime exists. |
| HD-0100 | HumanOS Document and Artifact Governance Standard v0.1 | N/A_LOCAL_ORIGIN | CANDIDATE | DOCUMENTED / MANUAL ONLY | PARTIAL | Created after `HOS-DOC-001_PREFLIGHT.md`. Candidate prose has Document Registry and Artifact Registry YAML projections. Not ratified; no runtime registry exists. |
| HM-0500 | HumanOS Human Model and Flourishing Standard v0.1 | CANDIDATE | DISCOVERED | Not fully implemented | VERIFIED_SOURCE | Source states Foundation Period Bootstrap Candidate. |
| HAI-0600 | HumanOS AI Model and Authority Standard v0.1 | CANDIDATE | RECONCILED SOURCE | Not fully implemented | VERIFIED_SOURCE | Source defines bounded workers/reviewers, Model Passports/Ledgers, provider neutrality, replaceable runtimes, minimal context, review independence, and no self-certification. |
| HF-0700 | Knowledge Model | Planned target only | DISCOVERED | Not implemented | PARTIAL | Recovered bootstrap-gap records name HF-0700 as a future promotion target. No standalone governing instrument has been reconciled yet. |
| HK-0800 | HumanOS Knowledge Kernel Protocol v0.1 | UNKNOWN pending content reconciliation | DISCOVERED | UNKNOWN | PARTIAL | Package and representations exist in Drive. Historical planning also used `HF-0800`; naming evolution must be reconciled without renumbering HK-0800. |
| HIST-CONST-2026-08-02 | Founding Constitution and Human Bill of Rights v0.2 | RATIFIED | RECONCILED HISTORICAL / PREFLIGHT | Historical governance record | VERIFIED_RECONCILIATION | Ratification is preserved as historical fact and strongest constitutional source. Current owner direction requires local-first re-ratification for the new control plane rather than automatic local promotion. |
| HIST-CONST-RAT-2026-08-02 | Constitutional Ratification Record — Founding Constitution v0.2 | RATIFIED | RECONCILED HISTORICAL / PREFLIGHT | Record only | VERIFIED_RECONCILIATION | Separate historical ratification record confirms exact document identity and 2026-08-02T22:44:00-04:00 effective time in the prior governance context. |
| HIST-GOV-BRANCHES-v0.1 | Constitutional Branches, Review Court, and Governance Runtime Charter v0.1 | Historical governance charter; not a ratified constitutional amendment | RECONCILED AS HISTORICAL SOURCE | Manual governance design; automated governance not established by this register | VERIFIED_RECONCILIATION | `HOS-GOV-001_BRANCHES_RECONCILIATION.md` preserves separation-of-functions design, clarifies local-first/FRIENDS/resource boundaries, and deliberately creates no competing government Instrument. |
| REPO-FOUNDATION-RAT-2026-09-11 | `docs/FOUNDATION_RATIFICATION.md` — Foundation Contract v0.1 ratification record | RATIFIED by source text | RECONCILED SOURCE / PREFLIGHT | Incremental implementation claimed; not all contracts implemented | VERIFIED_RECONCILIATION | Commitments were compared during HOS-CONST-001; human ownership, local-first/provider-neutral operation, model/FRIENDS non-authority, privacy lifecycle, provenance, recovery, rollback, and human approval remain aligned. |
| HOS-CONST-001-FRIENDS-001 | FRIENDS Constitutional Challenge Packet | N/A_LOCAL_ORIGIN | SUPERSEDED PACKET / HISTORICAL | Review packet only | PARTIAL | Prepared for rc1. Broad historical FRIENDS evidence was subsequently recovered and rc1 was superseded by rc2; packet remains preserved. |
| HOS-CONST-002-FROZEN-EVIDENCE | Frozen FRIENDS Evidence Index | N/A_LOCAL_ORIGIN / indexes historical September 14 evidence | RECONCILED EVIDENCE | Evidence index only | VERIFIED_RECONCILIATION | Indexes five frozen Pass A constitutional reviews; self-reported identities are evidence only, runtime-attested identities remain unknown. |
| HOS-CONST-002-REGRESSION | Legacy FRIENDS Findings Regression | N/A_LOCAL_ORIGIN | RECONCILED ANALYSIS | Analysis only | VERIFIED_RECONCILIATION | Regresses the five frozen review themes against rc1; justifies the minimal rc2 hardening delta. |
| HOS-CONST-002-FRIENDS-DELTA-001 | FRIENDS Delta Challenge Packet for rc2 | N/A_LOCAL_ORIGIN | READY / NOT EXECUTED | Review packet only | UNVERIFIED | Fresh clean-room review of rc2 repairs is still required. Current ChatGPT architect is not independent because historical FRIEND outputs were inspected during synthesis. |
| HOS-ENG-001 | Engineering Organization & Delivery standardization work item | N/A_LOCAL_ORIGIN | CANDIDATE SLICE | Documentary/manual only | PARTIAL | Preflight confirms HE-0410 is a subordinate specialization, not a replacement for HE-0400/HW-0300/HAI-0600. Manual pilot required before automation. |
| FDR-0004-v0.1 | Foundation Continuation & Artifact Governance Plan v0.1 | DRAFT / PROPOSAL | IMPORTED | Not implemented | PARTIAL | Contains a now-known retrieval error about HF-0100. Preserve; do not silently overwrite. |

## Representation rule

A governed Instrument may have multiple representations:

```text
canonical human-readable source
  -> PDF rendering
  -> DOCX rendering
  -> structured object index / registry projection
  -> hash / manifest
  -> export / package
```

No representation alone changes the Instrument's authority. A PDF is not more authoritative because it looks finished. A YAML object does not outrank canonical prose merely because software can parse it.

For HD-0100 v0.1, current candidate representations are:

- `HD-0100_HumanOS_Document_and_Artifact_Governance_v0.1.md` — candidate human-readable meaning anchor;
- `HD-0100_Document_Registry_Schema_v0.1.yaml` — non-authoritative structured projection;
- `HD-0100_Artifact_Registry_Schema_v0.1.yaml` — non-authoritative structured projection.

For HE-0410 v0.1:

- `HE-0410_HumanOS_Engineering_Organization_and_Delivery_Standard_v0.1.md` — candidate human-readable meaning anchor;
- `HE-0410_Manual_Engineering_Work_Item_Template_v0.1.yaml` — non-authoritative manual bootstrap projection/template.

For the constitutional lineage:

- `HF-0200_HumanOS_Constitution_and_Human_Bill_of_Rights_v0.2-rc1.md` — preserved superseded candidate;
- `HF-0200_HumanOS_Constitution_and_Human_Bill_of_Rights_v0.2-rc2.md` — current local candidate; **not ratified**.

## Canonical local path field

This register is intentionally conservative during re-bootstrap.

Historical Drive paths remain provenance references. Current local canonical paths are assigned only after reconciliation/import under the Document Workflow or, for new local candidates, recorded as candidate paths until ratification.

No mass copy into Git is authorized by this register.

Current candidate paths include:

- `docs/foundation/HD-0100_HumanOS_Document_and_Artifact_Governance_v0.1.md`
- `docs/foundation/HE-0410_HumanOS_Engineering_Organization_and_Delivery_Standard_v0.1.md`
- `docs/foundation/HE-0410_Manual_Engineering_Work_Item_Template_v0.1.yaml`
- `docs/foundation/HF-0200_HumanOS_Constitution_and_Human_Bill_of_Rights_v0.2-rc2.md`

## Reconciliation queue

1. **Execute `HOS-CONST-002_FRIENDS_DELTA_CHALLENGE_PACKET.md`** against an immutable rc2 commit using fresh independent reviewers and preserve raw outputs before synthesis when independent reviewer access is available.
2. **Pilot HE-0410 manually on one bounded real engineering work item** and record friction, resource usage, review burden, and missing fields before implementing worker orchestration.
3. Dispose every fresh CRITICAL/HIGH constitutional finding. If constitutional repairs are needed, create rc3 rather than silently editing rc2.
4. Present the exact final constitutional candidate/version, immutable commit, change summary, unresolved risks, and challenge record for explicit owner local ratification or rejection.
5. Reconcile HD-0100 against the finally ratified constitutional baseline before any separate ratification of document governance.
6. Reconcile HK-0800 content and the earlier `HF-0800` planning name.
7. Confirm whether an HF-0700 standalone artifact exists; if not, create only after document preflight.
8. Add hashes/local paths as each historical artifact is locally imported and verified.

### Completed reconciliation in this branch

- The August artifact/document governance standards were inspected and treated as source/subordinate control lineage for HD-0100 rather than duplicated as competing standards.
- The historical Constitutional Branches / Review Court charter was reconciled through HOS-GOV-001. No second government Instrument was created.
- HOS-CONST-001 preflight and clause/topic reconciliation were completed.
- HF-0200 v0.2-rc1 was drafted as a local constitutional candidate while preserving the August ratification as historical constitutional provenance.
- Five frozen September 14 FRIENDS Pass A reviews were recovered from the HumanOS Library and indexed without treating self-reported model names as attested identity.
- Those frozen findings were regressed against rc1. Several important findings were already closed; unresolved authority, third-party scope, rights-collision, succession/delegation, and dissent-path issues justified a minimal successor candidate.
- HF-0200 v0.2-rc2 was created as the current candidate. It is not ratified and has not yet received the fresh independent delta review required by its challenge packet.
- HE-0400, HW-0300, and HAI-0600 were re-read as source lineage for HOS-ENG-001. HE-0410 was created as a subordinate organizational/delivery specialization rather than a competing workflow or engineering contract.
- HE-0410 now defines the Human Principal / Chief Engineer / Principal Engineer / AEGIS separation, worker authority inheritance, resource-aware routing, proportional review lanes, Ready/Done, and a manual work-item template. No orchestration runtime is claimed.

## Promotion rule

An entry moves to local `RATIFIED` only when all required conditions are satisfied:

- identity reconciled;
- source/provenance recorded;
- authority conflicts resolved;
- required independent challenge/review completed when applicable;
- structured/readback projection verified when applicable;
- explicit Jon approval recorded;
- version/status change committed locally.

No reviewer, FRIEND, model, script, repository, registry, or external service may perform that promotion by itself.
