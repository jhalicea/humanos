# HumanOS Master Foundation Register

**Register ID:** HOS-REG-FOUNDATION-001  
**Lifecycle:** Local Re-Bootstrap  
**Status:** CANDIDATE REGISTER  
**Date:** 2026-09-16  
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
| HF-0200-v0.2-rc1 | HumanOS Constitution and Human Bill of Rights v0.2-rc1 | N/A_LOCAL_ORIGIN; derived from historically ratified and candidate lineage | CANDIDATE | Constitutional text candidate only; no runtime enforcement | PARTIAL | Local constitutional reconciliation candidate. Requires FRIENDS/adversarial challenge and explicit owner ratification before becoming current local constitutional law. |
| HW-0300 | HumanOS Workflow Governance Protocol v0.1 | UNKNOWN pending content reconciliation | DISCOVERED | UNKNOWN | PARTIAL | Package and representations exist in Drive. Do not infer current local authority from existence. |
| HE-0400 | HumanOS Engineering Contract v0.1 | CANDIDATE | DISCOVERED | UNKNOWN | PARTIAL | Package exists; local reconciliation pending. |
| HD-0100 | HumanOS Document and Artifact Governance Standard v0.1 | N/A_LOCAL_ORIGIN | CANDIDATE | DOCUMENTED / MANUAL ONLY | PARTIAL | Created after `HOS-DOC-001_PREFLIGHT.md`. Candidate prose has Document Registry and Artifact Registry YAML projections. Not ratified; no runtime registry exists. |
| HM-0500 | HumanOS Human Model and Flourishing Standard v0.1 | CANDIDATE | DISCOVERED | Not fully implemented | VERIFIED_SOURCE | Source states Foundation Period Bootstrap Candidate. |
| HAI-0600 | HumanOS AI Model and Authority Standard v0.1 | CANDIDATE | DISCOVERED | Not fully implemented | VERIFIED_SOURCE | Source states Bootstrap Candidate and separates capability from authority. |
| HF-0700 | Knowledge Model | Planned target only | DISCOVERED | Not implemented | PARTIAL | Recovered bootstrap-gap records name HF-0700 as a future promotion target. No standalone governing instrument has been reconciled yet. |
| HK-0800 | HumanOS Knowledge Kernel Protocol v0.1 | UNKNOWN pending content reconciliation | DISCOVERED | UNKNOWN | PARTIAL | Package and representations exist in Drive. Historical planning also used `HF-0800`; naming evolution must be reconciled without renumbering HK-0800. |
| HIST-CONST-2026-08-02 | Founding Constitution and Human Bill of Rights v0.2 | RATIFIED | RECONCILED HISTORICAL / PREFLIGHT | Historical governance record | VERIFIED_RECONCILIATION | Ratification is preserved as historical fact and strongest constitutional source. Current owner direction requires local-first re-ratification for the new control plane rather than automatic local promotion. |
| HIST-CONST-RAT-2026-08-02 | Constitutional Ratification Record — Founding Constitution v0.2 | RATIFIED | RECONCILED HISTORICAL / PREFLIGHT | Record only | VERIFIED_RECONCILIATION | Separate historical ratification record confirms exact document identity and 2026-08-02T22:44:00-04:00 effective time in the prior governance context. |
| HIST-GOV-BRANCHES-v0.1 | Constitutional Branches, Review Court, and Governance Runtime Charter v0.1 | Historical governance charter; not a ratified constitutional amendment | RECONCILED AS HISTORICAL SOURCE | Manual governance design; automated governance not established by this register | VERIFIED_RECONCILIATION | `HOS-GOV-001_BRANCHES_RECONCILIATION.md` preserves separation-of-functions design, clarifies local-first/FRIENDS/resource boundaries, and deliberately creates no competing government Instrument. |
| REPO-FOUNDATION-RAT-2026-09-11 | `docs/FOUNDATION_RATIFICATION.md` — Foundation Contract v0.1 ratification record | RATIFIED by source text | RECONCILED SOURCE / PREFLIGHT | Incremental implementation claimed; not all contracts implemented | VERIFIED_RECONCILIATION | Commitments were compared during HOS-CONST-001; human ownership, local-first/provider-neutral operation, model/FRIENDS non-authority, privacy lifecycle, provenance, recovery, rollback, and human approval remain aligned. |
| HOS-CONST-001-FRIENDS-001 | FRIENDS Constitutional Challenge Packet | N/A_LOCAL_ORIGIN | CANDIDATE / READY | Review packet only; not executed | UNVERIFIED | Defines independent challenge, attack families, resilience tests, metadata, cross-review, and promotion gate for HF-0200 v0.2-rc1. No FRIENDS review or test pass is claimed. |
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

For the constitutional lineage, `HF-0200_HumanOS_Constitution_and_Human_Bill_of_Rights_v0.2-rc1.md` is the current **local candidate**, not a ratified replacement for the historical August Constitution.

## Canonical local path field

This register is intentionally conservative during re-bootstrap.

Historical Drive paths remain provenance references. Current local canonical paths are assigned only after reconciliation/import under the Document Workflow or, for new local candidates, recorded as candidate paths until ratification.

No mass copy into Git is authorized by this register.

Current candidate paths include:

- `docs/foundation/HD-0100_HumanOS_Document_and_Artifact_Governance_v0.1.md`
- `docs/foundation/HF-0200_HumanOS_Constitution_and_Human_Bill_of_Rights_v0.2-rc1.md`

## Reconciliation queue

1. **Execute HOS-CONST-001 FRIENDS/adversarial review** against the immutable constitutional candidate commit, preserving independent raw outputs before synthesis.
2. Dispose all CRITICAL/HIGH constitutional findings and version the candidate if repairs are needed.
3. Present the exact final candidate/version, change summary, unresolved risks, and challenge record for explicit owner local ratification or rejection.
4. Reconcile HD-0100 against the finally ratified constitutional baseline before any separate ratification of document governance.
5. Reconcile HW-0300 content and historical state.
6. Reconcile HE-0400 content and historical state.
7. Reconcile HK-0800 content and the earlier `HF-0800` planning name.
8. Confirm whether an HF-0700 standalone artifact exists; if not, create only after document preflight.
9. Add hashes/local paths as each historical artifact is locally imported and verified.

### Completed reconciliation in this branch

- The August artifact/document governance standards were inspected and treated as source/subordinate control lineage for HD-0100 rather than duplicated as competing standards.
- The historical Constitutional Branches / Review Court charter was reconciled through HOS-GOV-001. No second government Instrument was created.
- HOS-CONST-001 preflight and clause/topic reconciliation were completed.
- HF-0200 v0.2-rc1 was drafted as a local constitutional candidate while preserving the August ratification as historical constitutional provenance.
- A FRIENDS challenge packet and constitutional resilience-test plan were prepared but **not executed**.

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
