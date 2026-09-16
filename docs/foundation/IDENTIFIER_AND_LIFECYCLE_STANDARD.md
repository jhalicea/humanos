# HumanOS Identifier and Document Lifecycle Standard

**Standard ID:** HOS-DOC-ID-001  
**Lifecycle:** Local Re-Bootstrap  
**Status:** CANDIDATE  
**Date:** 2026-09-16  
**Owner / final authority:** Jon Alicea  
**Implementation:** Manual/documentary until enforced by the local Document Workflow

## 1. Purpose

Define one stable rule for HumanOS document identity, chronology, lifecycle, representations, authority, and supersession.

This standard is intentionally narrow. It does not replace the existing Instrument Standard, artifact-preflight rules, canonical-home rules, or supersession procedure. It reconciles their common control requirements for the local-first re-bootstrap.

## 2. Stable identity is not chronology

A HumanOS document ID identifies a semantic object or document family.

An ID SHALL NOT be interpreted as the time the document was created.

Example:

```text
HF-0150 may be created before HF-0100.
```

That is valid when HF-0150 occupies a different semantic slot and the creation timestamps preserve chronology.

Existing stable IDs SHALL NOT be renumbered merely to produce chronological visual order.

## 3. Creation chronology

Chronology is carried by evidence such as:

- `created_at`;
- `modified_at`;
- source conversation date;
- source artifact date;
- Git commit;
- release or ratification date;
- predecessor/successor relationship.

When chronology is uncertain, status is `UNKNOWN` rather than inferred from numbering.

## 4. Required metadata

Every consequential governed document SHOULD support:

```yaml
id: stable identifier
title: human-readable canonical title
version: controlled version
lifecycle: lifecycle name
historical_authority_state: source/history status
local_authority_state: current local status
implementation_state: documented | planned | prototype | implemented | tested | verified | unknown
verification_state: unverified | partial | verified_source | verified_reconciliation | failed | disputed
owner: human owner / governing domain
canonical_role: role for which the object is authoritative
canonical_local_path: path or null until reconciled
source_refs: []
predecessor_refs: []
successor_refs: []
aliases: []
external_locations: []
hash_refs: []
classification: public | internal | private | restricted | unknown
created_at: timestamp/date if known
ratified_at: timestamp/date or null
```

Fields may evolve. Identity, authority state, provenance, and verification SHALL NOT be removed.

## 5. Local lifecycle

The controlled local lifecycle is:

```text
DISCOVERED
  -> IMPORTED
  -> RECONCILED
  -> CANDIDATE
  -> RATIFIED
  -> IMPLEMENTED
  -> VERIFIED
```

Side states:

```text
BLOCKED
DISPUTED
SUPERSEDED
REJECTED
ARCHIVED
```

These are not all mutually exclusive dimensions. `IMPLEMENTED` and `VERIFIED` describe implementation maturity; `RATIFIED` describes authority. HumanOS should represent independent dimensions separately in the registry rather than compressing every fact into one status string.

## 6. Bootstrap is provenance, not permanent status

`BOOTSTRAP` describes how an artifact entered HumanOS history.

It does not, by itself, determine current local authority.

Examples:

```yaml
provenance: CHATGPT_FOUNDATION_BOOTSTRAP
historical_authority_state: RATIFIED
local_authority_state: IMPORTED
```

or:

```yaml
provenance: DRIVE_FOUNDATION_BOOTSTRAP
historical_authority_state: CANDIDATE
local_authority_state: RECONCILED
```

## 7. Representation rule

A governed Instrument may appear as Markdown, DOCX, PDF, YAML, JSON, database object, signed manifest, archive package, or another controlled representation.

Representations SHALL declare their relationship to the governed object.

A renderer may change presentation. It may not change meaning or authority.

A machine projection may support enforcement only after required readback/verification. It may not silently override canonical human-readable text.

## 8. Authority dimensions

HumanOS SHALL distinguish at minimum:

1. **Source authenticity** — is this the artifact/source it claims to be?
2. **Historical authority** — what authority did it have in its original governance context?
3. **Current local authority** — what authority does it have now in local HumanOS?
4. **Implementation state** — is the behavior actually implemented?
5. **Verification state** — what evidence supports its claims or implementation?

A file can be historically ratified and locally imported without yet being locally re-ratified.

A specification can be locally ratified while its implementation remains `NOT_IMPLEMENTED`.

A runtime can pass tests without acquiring constitutional authority.

## 9. Supersession

Supersession is explicit and scope-limited.

A successor SHALL record:

- predecessor identity;
- superseded scope;
- unaffected predecessor scope, if any;
- effective date;
- authority approving the change;
- migration/compatibility effects;
- rollback path;
- downstream propagation targets.

Supersession preserves history. It does not rewrite the predecessor as though it never governed.

## 10. Correction rule

When a material factual or registry error is discovered:

1. preserve the erroneous historical artifact;
2. record the error;
3. attach the evidence that resolves it;
4. issue a correction or controlled successor;
5. update active registries/references;
6. do not delete the original merely to make history look clean.

## 11. Preflight rule

Before creating a consequential new artifact, HumanOS SHALL search for:

- exact title;
- stable ID;
- title variants and aliases;
- predecessor/successor records;
- canonical registry entries;
- related artifacts serving the same purpose.

The operation is then classified as one of:

```text
CREATE NEW
UPDATE EXISTING
CREATE NEW VERSION
CREATE DERIVATIVE
CREATE CANDIDATE / EXPERIMENT
RECOVER / RESTORE
COPY FOR REFERENCE / TESTING
DO NOT CREATE
```

## 12. Model and external-service rule

A model or service may draft metadata, discover duplicates, propose relationships, generate diffs, or flag conflicts.

It cannot assign final authority or ratify its own result.

Deterministic checks and owner-approved workflows control canonical state transitions.

## 13. Acceptance criteria

This candidate standard is ready for local ratification only if:

- it does not renumber existing stable IDs;
- creation order is represented separately from ID;
- historical and local authority are distinct;
- bootstrap is treated as provenance;
- representations cannot silently compete for authority;
- corrections preserve history;
- preflight prevents unnecessary duplicates;
- no model can self-promote an artifact;
- the rules are implementable later in a local Document Registry / Workflow.
