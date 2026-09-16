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
| HF-0200 | HumanOS Constitution and Human Bill of Rights v0.1 | Reconstruction CANDIDATE; explicitly not newly ratified | IMPORTED | Not implemented | VERIFIED_SOURCE | Must be reconciled against the historically ratified Constitution before any local promotion. |
| HW-0300 | HumanOS Workflow Governance Protocol v0.1 | UNKNOWN pending content reconciliation | DISCOVERED | UNKNOWN | PARTIAL | Package and representations exist in Drive. Do not infer current local authority from existence. |
| HE-0400 | HumanOS Engineering Contract v0.1 | CANDIDATE | DISCOVERED | UNKNOWN | PARTIAL | Package exists; local reconciliation pending. |
| HD-0100 | HumanOS Document and Artifact Governance Standard v0.1 | N/A_LOCAL_ORIGIN | CANDIDATE | DOCUMENTED / MANUAL ONLY | PARTIAL | Created on `foundation-local-bootstrap-registry-v1` after `HOS-DOC-001_PREFLIGHT.md`. Canonical candidate prose has Document Registry and Artifact Registry YAML projections. Not ratified; no runtime registry exists. |
| HM-0500 | HumanOS Human Model and Flourishing Standard v0.1 | CANDIDATE | DISCOVERED | Not fully implemented | VERIFIED_SOURCE | Source states Foundation Period Bootstrap Candidate. |
| HAI-0600 | HumanOS AI Model and Authority Standard v0.1 | CANDIDATE | DISCOVERED | Not fully implemented | VERIFIED_SOURCE | Source states Bootstrap Candidate and separates capability from authority. |
| HF-0700 | Knowledge Model | Planned target only | DISCOVERED | Not implemented | PARTIAL | Recovered bootstrap-gap records name HF-0700 as a future promotion target. No standalone governing instrument has been reconciled yet. |
| HK-0800 | HumanOS Knowledge Kernel Protocol v0.1 | UNKNOWN pending content reconciliation | DISCOVERED | UNKNOWN | PARTIAL | Package and representations exist in Drive. Historical planning also used `HF-0800`; naming evolution must be reconciled without renumbering HK-0800. |
| HIST-CONST-2026-08-02 | Founding Constitution and Human Bill of Rights v0.2 | RATIFIED | IMPORTED / PREFLIGHT | Historical governance record | VERIFIED_SOURCE | Original ratification occurred in the earlier ChatGPT/Drive period. Preserved as bootstrap/preflight evidence during local re-bootstrap. |
| HIST-CONST-RAT-2026-08-02 | Constitutional Ratification Record — Founding Constitution v0.2 | RATIFIED | IMPORTED / PREFLIGHT | Record only | VERIFIED_SOURCE | Separate historical ratification record exists in Drive. |
| HIST-GOV-BRANCHES-v0.1 | Constitutional Branches, Review Court, and Governance Runtime Charter v0.1 | Historical governance charter; not a ratified constitutional amendment | RECONCILED AS HISTORICAL SOURCE | Manual governance design; automated governance not established by this register | VERIFIED_RECONCILIATION | `HOS-GOV-001_BRANCHES_RECONCILIATION.md` preserves the durable separation-of-functions design, clarifies local-first/FRIENDS/resource boundaries, and deliberately creates no competing government Instrument. |
| REPO-FOUNDATION-RAT-2026-09-11 | `docs/FOUNDATION_RATIFICATION.md` — Foundation Contract v0.1 ratification record | RATIFIED by source text | IMPORTED / PREFLIGHT | Incremental implementation claimed; not all contracts implemented | VERIFIED_SOURCE | Existing repository record is preserved. Local re-bootstrap does not silently delete or upgrade it. |
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

For HD-0100 v0.1, the current candidate representations are:

- `HD-0100_HumanOS_Document_and_Artifact_Governance_v0.1.md` — candidate human-readable meaning anchor;
- `HD-0100_Document_Registry_Schema_v0.1.yaml` — non-authoritative structured projection;
- `HD-0100_Artifact_Registry_Schema_v0.1.yaml` — non-authoritative structured projection.

## Canonical local path field

This register is intentionally conservative during re-bootstrap.

Historical Drive paths remain provenance references. Current local canonical paths are assigned only after reconciliation/import under the Document Workflow or, for new local candidates, recorded as candidate paths until ratification.

No mass copy into Git is authorized by this register.

HD-0100 currently has a **candidate path**, not a ratified canonical-law path:

`docs/foundation/HD-0100_HumanOS_Document_and_Artifact_Governance_v0.1.md`

## Reconciliation queue

1. **HOS-CONST-001:** reconcile historical Founding Constitution v0.2, HF-0200, repository Foundation ratification records, current local authority transition, and HOS-GOV-001 into one reviewable local constitutional baseline candidate.
2. Owner review of HD-0100 candidate and its HOS-DOC-001 preflight/verification record; keep it unratified unless explicitly approved.
3. Reconcile HW-0300 content and historical state.
4. Reconcile HE-0400 content and historical state.
5. Reconcile HK-0800 content and the earlier `HF-0800` planning name.
6. Confirm whether an HF-0700 standalone artifact exists; if not, create only after document preflight.
7. Add hashes/local paths as each historical artifact is locally imported and verified.

### Completed reconciliation in this branch

- The August artifact/document governance standards were inspected and treated as source/subordinate control lineage for HD-0100 rather than duplicated as competing standards.
- The historical Constitutional Branches / Review Court charter was reconciled through HOS-GOV-001. Its durable branch/function design is preserved for HOS-CONST-001; no second government Instrument was created.

## Promotion rule

An entry moves to local `RATIFIED` only when all required conditions are satisfied:

- identity reconciled;
- source/provenance recorded;
- authority conflicts resolved;
- required independent challenge/review completed when applicable;
- structured/readback projection verified when applicable;
- explicit Jon approval recorded;
- version/status change committed locally.

No reviewer, FRIEND, model, script, or external service may perform that promotion by itself.
