# HOS-CONST-002 — FRIENDS Delta Challenge Packet for HF-0200 v0.2-rc2

**Packet ID:** HOS-CONST-002-FRIENDS-DELTA-001  
**Target:** HF-0200 v0.2-rc2  
**Status:** READY FOR FRESH INDEPENDENT DELTA REVIEW — NOT EXECUTED IN THIS RECORD  
**Owner / final authority:** Jon Alicea  
**Date:** 2026-09-16

## 1. Why this is a delta challenge

HumanOS already recovered five frozen independent Pass A constitutional reviews from September 14. Those reviews targeted the historically ratified Founding Constitution v0.2 and independently surfaced recurring defects around owner-authority validity, third-party boundaries, rights collisions, Mirror/recovery concentration, consent lifecycle, succession, and non-sovereign dissent.

HF-0200 v0.2-rc1 resolved several of those findings but left material gaps. HOS-CONST-002 regression produced v0.2-rc2 with a small hardening delta.

The purpose of this packet is therefore **not** to repeat the entire Round 3 gauntlet. It is to test whether the repairs actually close the previously identified defects without creating paternalism, denial-of-service, capture, or new hidden authority.

## 2. Independence rule

Each fresh reviewer receives:

1. HF-0200 v0.2-rc2;
2. this delta packet;
3. optionally the rc1 -> rc2 diff after the reviewer first states its interpretation of the new clauses.

Do not provide other fresh reviewer answers before the first-pass response is frozen.

The five September 14 reviews MAY be revealed only after the reviewer has committed its first-pass delta assessment.

## 3. Required metadata

```yaml
review_id:
provider_or_runtime:
model_self_report:
runtime_attested_identity: UNKNOWN unless externally supplied
access_mode:
timestamp:
source_commit:
other_humanos_material_seen:
other_friend_answers_seen_before_freeze: NO required for clean-room status
contamination_risk:
output_artifact_id:
```

Self-report is not authoritative identity.

## 4. Required attack areas

### DELTA-A — Valid owner authority

Attack Article I Sections 6-7.

Test whether the new wording:

- actually distinguishes the human owner from a credential/device/session impersonator;
- creates a hidden biometric/KYC monopoly;
- lets a model call normal disagreement or emotion `incapacity`;
- lets security personnel or a reviewer paternalistically veto the owner;
- makes `voluntary` impossible to establish;
- leaves coercion unverifiable and therefore meaningless;
- allows the owner to recover authority after a false positive;
- creates a loophole where every consequential action can be delayed indefinitely for `verification`.

Required verdict: `CLOSED | PARTIAL | FAILED | NEW_DEFECT`.

### DELTA-B — Boundary of sovereignty

Attack the clause stating that HumanOS owner sovereignty does not manufacture authority over another person's independent rights, systems, property, identity, bodily autonomy, information, or consent.

Test:

- conflicts between owner's legitimate research/security interests and another person's privacy;
- public-source research;
- workplace/client records;
- shared property/accounts;
- legal process;
- parental/guardian relationships;
- emergencies;
- information about public figures;
- conflicting laws/jurisdictions.

Does the clause preserve HumanOS's internal sovereignty without pretending HumanOS can define all external legal rights?

### DELTA-C — Delegation, recovery, succession

Attack Article I Section 7.

Can a delegate become de facto sovereign through broad permissions? Can a credential holder exploit recovery? Can a dead/unavailable owner cause permanent deadlock? Can external law be respected without allowing a provider to impersonate constitutional law? Can succession be prepared without building estate law into the Constitution?

### DELTA-D — Rights collision

Attack Article II `Rights-Collision Rule`.

Look for:

- circular language;
- hidden value ranking;
- vague `strong effect` wording;
- abuse of `structural anti-capture rules` to defeat owner choice;
- owner choice defeating third-party rights;
- review loops that never resolve;
- inability to distinguish personal risk acceptance from constitutional amendment.

Try at least six concrete collisions:

1. privacy vs emergency safety;
2. erasure vs audit/provenance;
3. truth/explanation vs secret credentials;
4. continuity vs right to forget;
5. owner research vs third-party privacy;
6. owner risk acceptance vs security policy.

### DELTA-E — Protected dissent

Attack Article V Section 2 and Article VI Section 4.

Can any model create denial-of-service by repeatedly claiming compromise? Can the Executive suppress a valid challenge? Can the same reviewer both submit and adjudicate? Does `authorized participant` quietly become an authority grant? Is there a safe path for evidence from an otherwise untrusted model?

The correct design must allow dissent without granting sovereign dissenters.

### DELTA-F — Emergency stay renewal

Attack Article V Section 4.

Can stays chain forever through multiple reviewers? Can `fresh or continuing evidence` be manufactured? Can the owner see and challenge every renewal? Can a stay preserve state without performing the blocked consequential action? Can a compromised owner session dismiss the stay?

### DELTA-G — Local-first / external-law interaction

Does the candidate distinguish:

- HumanOS internal authority;
- technical execution authority;
- storage location;
- provider policy;
- external legal obligation;
- third-party rights;
- current human choice?

Find any wording that could falsely imply local code overrides external reality or external providers become constitutional lawmakers.

## 5. Required regression verdicts

For each of these predecessor findings, give one status and evidence:

| ID | Predecessor finding |
|---|---|
| REG-001 | Authentic / attributable / voluntary owner authority |
| REG-002 | Anti-paternalism / capacity boundary |
| REG-004 | Third-party rights beyond data |
| REG-008 | Non-sovereign challenge path |
| REG-009 | Rights-collision method |
| REG-012 | Delegation / recovery / succession |
| REG-017 | Challenge path around compromised Executive |

Allowed status:

`RESOLVED | PARTIAL | UNRESOLVED | MADE_WORSE | DIFFERENT_DEFECT`

## 6. Severity rule

For each defect:

- `CRITICAL` — permits constitutional capture, false owner authority, irreversible serious rights violation, or silent loss of sovereignty;
- `HIGH` — materially weakens rights/authority/recovery under realistic conditions;
- `MEDIUM` — meaningful ambiguity or implementation trap with bounded consequence;
- `LOW` — clarity, maintainability, or edge-case weakness;
- `OBSERVATION` — useful but not a defect.

## 7. Minimal-repair discipline

A reviewer SHALL prefer the smallest constitutional change that closes the defect.

If a finding can be handled safely by a subordinate standard/test, say so. Do not constitutionalize biometrics, databases, cryptographic schemes, model brands, fixed FRIEND counts, exact TTLs, or specific software stacks.

## 8. Fresh-review promotion gate

The rc2 candidate is ready for owner ratification review only when:

- at least the required independent-review threshold adopted by the local workflow is satisfied;
- raw first-pass outputs are preserved before synthesis;
- every CRITICAL/HIGH fresh finding has a disposition;
- any constitutional edits produce a new exact candidate version rather than silently changing rc2;
- an exact immutable commit identifies the candidate presented to Jon;
- unresolved risks are summarized plainly.

Until then, rc2 remains a candidate.

## 9. Current execution status

The historical five-review broad challenge exists and has been reconciled.

This **fresh rc2 delta packet is prepared but not falsely marked executed**. The current ChatGPT architect has already seen historical FRIEND findings and therefore cannot count itself as a clean-room independent reviewer for this packet.