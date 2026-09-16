# HD-0100 — HumanOS Document and Artifact Governance Standard v0.1

**Instrument ID:** HD-0100  
**Historical work item:** HOS-DOC-001  
**Lifecycle:** Local Re-Bootstrap  
**Status:** CANDIDATE — NOT RATIFIED  
**Owner / final authority:** Jon Alicea  
**Date:** 2026-09-16  
**Implementation status:** DOCUMENTED / MANUAL ONLY  
**Provider dependency:** None  
**Public-repository classification:** PUBLIC / SANITIZED GOVERNANCE TEXT

> HumanOS preserves important knowledge by governing identity, authority, provenance, lifecycle, and evidence — not by trusting filenames, folders, models, or storage providers.

## 0. Candidate boundary

HD-0100 is a candidate Instrument. Its existence does not make it current law and does not prove the Document Registry or Artifact Registry is implemented.

This document consolidates and orchestrates recovered HumanOS document-control lineage. It does not silently supersede the earlier Artifact Creation Preflight, Canonical Home, Naming/Provenance, Object Identity, Diff/Supersession, Dependency Registry, or constitutional-governance records.

Until explicit local ratification, this Instrument is evidence and a proposed operating contract.

## 1. Purpose

HD-0100 defines the human-readable contract for:

- the **Document Workflow**;
- the **Document Registry**;
- the **Artifact Registry**;
- canonical document identity and version control;
- representation relationships;
- amendments, corrections, ratification, supersession, and archive;
- local-first authority during HumanOS re-bootstrap;
- future deterministic enforcement by the Workflow Kernel.

Its purpose is to eliminate document split-brain while preserving history.

## 2. Governing principles

### HD-REQ-001 — Human authority

The human owner SHALL remain the final authority for constitutional and Foundation ratification and for any promotion that requires human approval.

Models, FRIENDS, tools, scripts, registries, workflows, and external services may propose, compare, challenge, verify, or record. They may not self-ratify.

### HD-REQ-002 — Local-first governance

Current HumanOS governance state SHALL be controlled through the human-owned local HumanOS system and its version-controlled governance records.

Historical ChatGPT/Drive records remain preserved bootstrap/preflight evidence. Their historical status is not erased, but storage on an external service does not by itself create current local authority.

### HD-REQ-003 — Identity is not location

An Instrument or artifact SHALL retain stable identity across rename, relocation, rendering, export, backup, and provider migration.

A filename, folder path, URL, provider ID, or Git branch is a locator or representation detail, not the identity itself.

### HD-REQ-004 — Authority is not recency

The newest file, newest model output, newest commit, or largest document SHALL NOT automatically become canonical.

Authority is established through recorded role, status, provenance, governing scope, and valid promotion.

### HD-REQ-005 — No silent split-brain

Two objects SHALL NOT silently claim canonical authority for the same role and scope.

When competing claims exist, destructive promotion pauses until the conflict is reconciled or explicitly marked disputed.

### HD-REQ-006 — History survives correction

Correction, amendment, supersession, or migration SHALL preserve enough predecessor history and provenance to reconstruct how current authority emerged, subject to properly authorized privacy/deletion rules.

### HD-REQ-007 — Privacy outranks convenience

Registry convenience SHALL NOT justify copying private content, credentials, sensitive metadata, or protected evidence into a lower-trust store.

A safe reference is preferred when duplication would create unnecessary exposure.

### HD-REQ-008 — Anti-bureaucracy

Document governance SHALL exist to improve understanding, authority control, implementation, verification, recovery, or learning.

Artifacts that no longer serve a justified purpose SHOULD be merged, simplified, superseded, archived, or removed from active navigation through a governed process.

## 3. Core distinctions

HumanOS distinguishes four related objects.

### 3.1 Instrument

A governed human-readable object carrying durable meaning and authority state across time.

Examples: Constitution, Foundation Instrument, Workflow Governance Protocol, Engineering Contract, policy standard.

### 3.2 Document representation

A representation of an Instrument, such as Markdown, PDF, DOCX, YAML, JSON, database projection, or rendered website.

A representation does not independently gain authority merely because it is easier to read or parse.

### 3.3 Artifact

Any received or produced object worth preserving, tracing, reviewing, testing, comparing, or recovering.

Examples include source documents, screenshots, PDFs, raw model outputs, test logs, benchmark data, terminal captures, reports, review packets, evidence bundles, datasets, releases, and exports.

### 3.4 Registry record

Structured metadata describing an Instrument or artifact: identity, role, authority/status, location, provenance, relationships, security, verification, and lifecycle.

A registry record is not a substitute for the source object.

## 4. Registry architecture

```text
                   HUMAN OWNER
                       |
                       v
              DOCUMENT WORKFLOW
                       |
          +------------+------------+
          |                         |
          v                         v
  DOCUMENT REGISTRY          ARTIFACT REGISTRY
  governed meaning           evidence / objects
          |                         |
          +------------+------------+
                       |
                       v
              WORKFLOW / EVIDENCE
                       |
                       v
                  LOCAL RUNTIME
```

The Document Registry answers:

> What governing document exists, which version/status controls which scope, and what is its lineage?

The Artifact Registry answers:

> What object exists, where is it, where did it come from, what role does it serve, and what evidence/relationships belong to it?

## 5. Document Registry contract

### HD-REQ-009 — One registry identity per Instrument

Each consequential governed Instrument SHALL have one stable Instrument identity in the Document Registry.

Multiple representations SHALL attach to that identity rather than silently becoming competing Instruments.

### HD-REQ-010 — Required Document Registry fields

At minimum, a governed Document Registry record SHALL support:

```yaml
instrument_id: stable semantic ID
title: canonical human-readable title
version: controlled content revision
instrument_family: foundation | constitution | workflow | engineering | documents | standards | kernel | other
canonical_role: role/scope for which it governs
historical_authority_state: source-context authority
local_authority_state: discovered | imported | reconciled | candidate | ratified | superseded | rejected | archived
implementation_state: documented | planned | prototype | implemented | tested | verified | unknown
verification_state: unverified | partial | verified_source | verified_reconciliation | failed | disputed
owner: human/governing domain
canonical_human_source: locator or null
representations: []
source_refs: []
predecessor_refs: []
successor_refs: []
supersession_scope: null or explicit scope
aliases: []
external_locations: []
hash_refs: []
classification: public | internal | private | restricted | unknown
created_at: date/timestamp if known
effective_at: date/timestamp or null
ratified_at: date/timestamp or null
last_verified_at: date/timestamp or null
```

Exact implementation storage may evolve. These concepts SHALL remain independently representable.

### HD-REQ-011 — Authority dimensions remain separate

The registry SHALL NOT collapse source authenticity, historical authority, current local authority, implementation state, and verification state into one ambiguous status field.

A historically ratified artifact may be locally `IMPORTED` while local reconciliation is pending.

A locally ratified specification may remain `NOT_IMPLEMENTED`.

Passing tests does not create constitutional authority.

## 6. Artifact Registry contract

### HD-REQ-012 — Artifact identity

Important artifacts SHOULD receive a stable, non-secret, locally generated artifact identity independent of filename and location.

The `ART-*` namespace is reserved for this purpose. The exact suffix strategy is an implementation decision and SHALL NOT be treated as ratified merely because examples exist.

### HD-REQ-013 — Required Artifact Registry fields

For important artifacts, the registry SHOULD support:

```yaml
artifact_id: stable local identity
label: human-readable title when safe
safe_label: lower-disclosure title when needed
artifact_type: document | pdf | image | model_output | test_log | dataset | report | code_snapshot | other
artifact_role: source_evidence | canonical_source | representation | derivative | working_copy | review | test_evidence | backup | publication | archive | other
owner_domain: lifecycle owner
classification: public | internal | private | restricted | unknown
canonical_status: canonical_for_role | noncanonical_reference | derivative | replica | backup | external_authority | unknown
canonical_home: logical local role/location or external authority
locators: []
source_artifact_ids: []
derived_artifact_ids: []
related_instrument_ids: []
creator: human | model/runtime | script | external_service | organization | unknown
provider_model_metadata: optional evidence metadata
created_at: timestamp/date if known
captured_at: timestamp/date if known
last_verified_at: timestamp/date or null
hashes: []
size_bytes: integer or null
verification_state: unverified | partial | verified_source | verified_integrity | failed | disputed
retention_state: active | archived | deletion_pending | deleted_with_tombstone | external_only
notes: safe operational notes
```

### HD-REQ-014 — Raw and synthesized outputs remain distinct

A raw FRIEND/model output, reviewer synthesis, final decision, and ratified amendment SHALL be separate artifacts with explicit relationships.

A synthesized report SHALL NOT overwrite the raw responses that support it.

### HD-REQ-015 — External model metadata

When a model output materially influences consequential work, the Artifact Registry SHOULD preserve available provider/product/model/version or runtime identity, timestamp, task/work item, role, input/output evidence references, and verification/disposition state.

Unavailable metadata remains `UNKNOWN`; it is not invented.

## 7. Document Workflow

The manual local workflow is the precursor to a future deterministic workflow service.

```text
PREFLIGHT
  -> INTAKE / PRESERVE
  -> DRAFT
  -> REVIEW
  -> COMPARE
  -> DISPOSITION
  -> RATIFICATION (when required)
  -> PROMOTION / EFFECTIVE VERSION
  -> VERIFY / PROPAGATE
  -> SUPERSEDE / ARCHIVE
```

### HD-REQ-016 — Preflight before consequential creation

Before creating or materially restructuring a consequential governed artifact, HumanOS SHALL:

1. define the proposed object and purpose;
2. search exact title and identity;
3. search variants, aliases, and likely predecessors;
4. inspect current registries and relevant repositories/stores;
5. compare plausible matches;
6. classify identity relationship;
7. choose create/update/version/derivative/recover/reference/do-not-create;
8. review authority and privacy;
9. record the preflight result.

### HD-REQ-017 — Preserve before transform

When source evidence matters, the source SHALL be preserved before summarization, conversion, redaction, synthesis, or migration.

Derived objects SHALL point back to their sources.

### HD-REQ-018 — Review independence

When independent review is required, the reviewer SHALL receive the governing criteria and evidence rather than merely being asked to agree with the implementer's conclusion.

FRIENDS/model consensus is not ratification and is not a substitute for reproducible evidence.

### HD-REQ-019 — Comparison before supersession

A candidate that could replace or amend an existing governed object SHALL be compared against the baseline for identity, authority, content, dependencies, security/privacy, implementation state, and verification state.

Recency alone SHALL NOT justify supersession.

### HD-REQ-020 — Explicit disposition

A comparison SHALL end in an explicit disposition such as:

```text
NO_CHANGE
UPDATE_EXISTING
CREATE_SUCCESSOR
PARTIAL_MERGE
COEXIST
CANONICAL_SWITCH
DUPLICATE_CONTAINMENT
DISPUTED_OR_BLOCKED
```

### HD-REQ-021 — Ratification is an owner act

Where ratification is required, promotion to `RATIFIED` SHALL require explicit owner approval recorded with Instrument identity, version, date/time, scope, and evidence reference.

A file edit, merge, model vote, passing test, or publication SHALL NOT substitute for ratification.

### HD-REQ-022 — Promotion and propagation

When a new effective version is promoted, HumanOS SHALL update applicable registry records, predecessor/successor links, current pointers, dependencies, tests, implementation references, and safe public projections.

Propagation failures remain visible as incomplete work.

### HD-REQ-023 — Supersession is scope-limited

Supersession SHALL identify what scope is replaced and what historical scope remains valid.

Predecessors remain preserved unless a properly authorized privacy/deletion rule requires otherwise.

### HD-REQ-024 — Archive is not authority erasure

Archiving removes an object from active navigation/use but does not rewrite whether it existed or once governed.

A historical artifact may be archived while retaining its provenance and former authority state.

## 8. Canonical-source and representation rules

### HD-REQ-025 — Human-readable canon

For governing Instruments, the approved human-readable source SHALL be the meaning anchor unless a later ratified Instrument explicitly defines a different canonical representation model.

Structured projections support software and AI interpretation but SHALL pass readback/verification before executable governance.

### HD-REQ-026 — Rendered files are projections

PDF, DOCX, website, and presentation renderings SHALL identify the Instrument/version they represent.

A rendering may change layout. It may not silently change normative meaning.

### HD-REQ-027 — Hashes prove bytes, not truth

Cryptographic hashes may prove integrity/identity of a byte sequence. They do not prove that content is correct, ratified, current, or constitutionally valid.

## 9. Canonical homes and storage roles

### HD-REQ-028 — Role-based canonicality

Canonicality is assigned by role. One object may be canonical evidence while a separate object is canonical for current action.

The role SHALL be explicit so these objects do not silently compete.

### HD-REQ-029 — Local governance vs external evidence

HumanOS may use external systems as authoritative sources for their own records. HumanOS governance records and runtime authority remain locally controlled unless the owner explicitly adopts another architecture through governed change.

Google Drive, ChatGPT, GitHub, another model provider, or a backup location SHALL NOT become constitutional authority merely because data is stored there.

### HD-REQ-030 — Git/public boundary

The public repository SHALL contain only content appropriate for public disclosure.

Private Notebook data, secrets, protected source material, raw private model transcripts, private artifact-vault paths, and sensitive operational evidence SHALL remain outside Git.

## 10. Government / branch interaction

HD-0100 does not create a new government model. It interoperates with the recovered Constitutional Branches charter.

Document governance functions map as follows:

- **Legislative / standards function:** drafts and amends governing Instruments.
- **Executive / runtime function:** carries out valid effective rules.
- **Judicial / review function:** interprets conflicts and challenges major changes.
- **Investigation / audit function:** establishes facts and provenance.
- **Human owner:** retains ratification and final sovereign authority.

The branches are functions, not autonomous personalities or competing databases.

A model can participate in a function without becoming that constitutional office.

## 11. FRIENDS interaction

FRIENDS are bounded independent reviewers/challengers.

They MAY:

- identify loopholes and contradictions;
- challenge assumptions;
- compare proposals against governing rules;
- propose amendments;
- produce dissent;
- design adversarial tests.

They SHALL NOT:

- ratify an Instrument;
- convert consensus into authority;
- edit current local authority without the governed workflow;
- bypass privacy or permission controls;
- certify their own authority.

Raw FRIEND outputs are artifacts and should be preserved before synthesis when the review is consequential.

## 12. Resource-scarcity interaction

Document governance requirements are not relaxed because a preferred model, Codex/Work session, cloud provider, token budget, or quota is unavailable.

Scarcity may change which qualified worker performs drafting or review. It may change speed or convenience. It SHALL NOT silently reduce privacy, authority, provenance, verification, or human-approval requirements.

Detailed Token Conservative / compute routing belongs in a separate resource-governance Instrument.

## 13. Future deterministic implementation target

HD-0100 defines behavior before runtime implementation.

A future local service SHOULD provide:

- transactional Document Registry storage;
- transactional Artifact Registry storage;
- preflight / duplicate checks;
- transition validation;
- canonical-role conflict detection;
- predecessor/successor resolution;
- hash/integrity helpers;
- safe locator handling;
- review/ratification evidence linkage;
- propagation tracking;
- tombstones;
- export/backup support;
- query/readback interfaces;
- audit events;
- local-first operation with no silent cloud fallback.

SQLite is a candidate implementation technology, not constitutional law. The storage engine may change if it preserves this contract.

## 14. Failure behavior

When authority or identity is ambiguous, HumanOS SHALL fail conservative for canonical promotion.

Examples:

- duplicate candidate discovered -> preserve both, block promotion, reconcile;
- conflicting current versions -> freeze destructive edits, compare, record disposition;
- missing source -> mark `PARTIAL` / `UNKNOWN`, do not invent;
- model claims ratification -> reject the authority claim, preserve output as evidence;
- broken locator -> use stable identity/provenance to recover, do not create an arbitrary replacement;
- registry/runtime disagreement -> surface split-brain and reconcile before consequential action;
- private artifact requested by public workflow -> deny or use safe reference/redaction according to policy.

## 15. Minimum acceptance tests for later implementation

The future implementation is not `VERIFIED` until reproducible tests demonstrate at least:

1. duplicate Instrument identity cannot silently produce two canonical versions for the same scope;
2. multiple representations map to one Instrument identity;
3. historical ratification and local authority remain separate fields;
4. a model cannot self-promote `CANDIDATE -> RATIFIED`;
5. supersession preserves predecessor lineage;
6. registry entries survive rename/move without identity loss;
7. missing metadata remains unknown rather than fabricated;
8. private artifact metadata does not leak into public projections;
9. rollback restores the prior effective registry state;
10. concurrent/stale promotion attempts are rejected or reconciled transactionally;
11. deleted/hidden material follows governing privacy rules and does not silently reappear through derived indexes;
12. provider loss does not destroy HumanOS identity or governance history.

These are proposed acceptance requirements, not claimed passing tests.

## 16. Candidate acceptance criteria

HD-0100 v0.1 is ready for owner review when:

- its preflight record exists;
- it preserves existing stable IDs;
- it clearly separates Instrument, representation, artifact, and registry record;
- it defines Document Registry and Artifact Registry contracts without pretending runtime exists;
- it reuses rather than silently replaces historical control standards;
- it preserves the historical ChatGPT/Drive bootstrap as evidence;
- it keeps current local ratification explicit and human-controlled;
- it fits the recovered constitutional branch model without creating competing authority;
- its requirements can be mapped to future deterministic tests;
- rollback is simply non-promotion / branch reversion until implementation begins.

## 17. Source / lineage register

Primary lineage reviewed for this candidate:

- HF-0000 HumanOS Foundation Master Bootstrap v0.2;
- HF-0000 HumanOS Foundation v0.3;
- HF-0100 HumanOS Foundational Principles v0.1;
- HF-0150 HumanOS Instrument Standard v0.1;
- HW-0300 HumanOS Workflow Governance Protocol lineage;
- Artifact Creation Preflight and Duplicate Prevention Standard v0.1;
- Artifact Diff and Supersession Procedure v0.1;
- Canonical Home and Reference Rules v0.1;
- Naming, Metadata, Versioning, and Provenance Standard v0.1;
- Object Identity and Reference Schema v0.1;
- Dependency and Propagation Registry v0.1;
- Constitutional Branches, Review Court, and Governance Runtime Charter v0.1;
- local Master Foundation Register;
- local Identifier and Document Lifecycle Standard;
- FDR-0004 continuation/correction lineage.

## 18. Ratification

```text
Local ratification status: PENDING
Ratified by: ______________________________
Date/time: __________________________________
Instrument: HD-0100 v0.1
Evidence / review record: ____________________
```

Until that field is completed through a governed local decision, **HD-0100 remains a CANDIDATE**.