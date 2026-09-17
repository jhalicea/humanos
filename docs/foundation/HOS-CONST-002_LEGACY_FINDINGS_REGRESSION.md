# HOS-CONST-002 — Legacy FRIENDS Findings Regression Against HF-0200 v0.2-rc1

**Record type:** Constitutional regression analysis  
**Lifecycle:** Local Re-Bootstrap  
**Status:** CANDIDATE ANALYSIS — NOT LAW / NOT RATIFICATION  
**Date:** 2026-09-16  
**Owner / final authority:** Jon Alicea  
**Baseline under test:** `HF-0200_HumanOS_Constitution_and_Human_Bill_of_Rights_v0.2-rc1.md`

## 1. Purpose

Use the five frozen September 14 FRIENDS Pass A constitutional reviews as regression evidence against the newer local reconciliation candidate.

This is not a substitute for a fresh clean-room review of the exact current candidate. It answers a narrower question:

> Did the newer candidate actually close the important defects already found independently, or merely rewrite them in different language?

## 2. Regression dispositions

| ID | Frozen challenge theme | rc1 evidence | Disposition | Severity after rc1 | Required action |
|---|---|---|---|---|---|
| REG-001 | Authentic / attributable / voluntary owner authority | Article I still says owner/current consent governs, but does not expressly require reasonable attribution/authentication or distinguish compromised credentials/coercion from valid authority. Article V mentions credential compromise only as emergency-stay trigger. | **UNRESOLVED** | **CRITICAL** | Constitutional repair required. |
| REG-002 | Human-capacity / anti-paternalism boundary | rc1 does not define a safe boundary between voluntary owner choice and a system/model declaring the owner unfit. | **UNRESOLVED** | **HIGH** | Add presumption of capacity plus narrow non-diagnostic hold for credible authorization failure; details subordinate. |
| REG-003 | Third-party data dignity | Eleventh Guarantee now establishes purpose limitation, minimum necessary access, classification, consent boundaries, and stronger handling for sensitive/professional contexts. | **RESOLVED AT CONSTITUTIONAL PRINCIPLE LEVEL** | LOW / subordinate testing | Keep implementation standards below Constitution. |
| REG-004 | Third-party rights beyond data | Eleventh Guarantee focuses primarily on information handling. Owner sovereignty is still not expressly bounded from creating authority over another person's property, systems, autonomy, safety, or consent. | **PARTIALLY RESOLVED** | **HIGH** | Add explicit scope boundary for owner sovereignty. |
| REG-005 | Mirror as sole interface / recovery monopoly | rc1 changed Mirror from `sole` to `primary` and explicitly permits governed recovery/admin/CLI/emergency interfaces without alternate sovereignty. | **RESOLVED** | LOW | Test recovery paths later. |
| REG-006 | Emergency stay can become indefinite veto | rc1 requires stay to be narrow, owner-visible, recorded, scoped, and to include a review or expiry rule. | **RESOLVED AT PRINCIPLE LEVEL** | MEDIUM implementation risk | Test TTL/renewal/owner visibility. |
| REG-007 | FRIEND/model consensus becomes law | rc1 expressly says reviewer consensus is not ratification and reviewers gain no office by participation. | **RESOLVED** | LOW | Preserve in deterministic workflow. |
| REG-008 | Non-sovereign machine/reviewer dissent when HumanOS is wrong | rc1 permits FRIENDS/reviewers to challenge and propose, but does not clearly guarantee any participant a bounded channel to submit concrete evidence of constitutional compromise for review. | **PARTIALLY RESOLVED** | **HIGH** | Add challenge/escalation right without granting execution authority. |
| REG-009 | Rights-collision method | rc1 still lists multiple protected values and uses `narrowest effective remedy`, but does not clearly state how to resolve owner personal rights vs structural safeguards vs third-party/external rights. | **PARTIALLY RESOLVED** | **HIGH** | Add concise rights-collision rule; avoid rigid universal hierarchy. |
| REG-010 | Deletion vs provenance / continuity | Fifth Guarantee now makes provenance preservation subject to valid privacy/erasure rules; Article VII preservation applies only where allowed/materially necessary; Seventh Guarantee bars silent resurrection. | **RESOLVED AT PRINCIPLE LEVEL** | MEDIUM implementation risk | Define tombstone/receipt/cache invalidation standard later. |
| REG-011 | Recurring / stale / broad consent lifecycle | rc1 strengthens `current consent` and rejects prior consent/repeated behavior as manufactured consent, but exact TTL, renewal, delegation, in-flight revocation, and cross-device conflicts remain undefined. | **MOVED TO SUBORDINATE STANDARD** | HIGH implementation risk, not necessarily constitutional defect | Create consent-lifecycle/authorization standard and tests. |
| REG-012 | Delegation / recovery / succession | rc1 Future Expansion addresses additional humans but not bounded delegation, emergency recovery, incapacity, death, or succession of owner authority. | **UNRESOLVED** | **MEDIUM-HIGH** | Add narrow constitutional permission/boundary; mechanics subordinate. |
| REG-013 | Anti-manipulation verification / personalization disclosure | Eighth Guarantee forbids covert persuasion/exploitation but does not specify operational disclosure tests. | **MOVED TO SUBORDINATE STANDARD** | MEDIUM | Build manipulation/transparency test standard. |
| REG-014 | Provider/model retirement | rc1 defines roles by function and requires provider/model replaceability. | **RESOLVED** | LOW | Qualification/migration tests later. |
| REG-015 | Token/resource scarcity weakens safeguards | rc1 explicitly prohibits scarcity from reducing privacy, authority, permissions, evidence, review, rollback, or constitutional protections. | **RESOLVED** | LOW | Enforce in resource router later. |
| REG-016 | Architecture/technology lock-in | rc1 intentionally keeps storage engines, model-routing algorithms, registry schemas, and provider names below constitutional layer. | **RESOLVED** | LOW | Maintain discipline. |
| REG-017 | Correct challenge can be suppressed by compromised Executive | Review/Investigation can challenge, but a compromised Mirror/runtime could theoretically suppress the route if no independent challenge ingress is guaranteed. | **PARTIALLY RESOLVED** | **HIGH** | Establish bounded independent challenge path and recovery visibility. |
| REG-018 | Historical readiness imported as current readiness | rc1 explicitly says historical governance-readiness claims remain historical evidence and current local system must re-verify controls. | **RESOLVED** | LOW | Keep implementation verification separate. |

## 3. Constitutional repairs justified now

The regression supports a **small** constitutional delta rather than another rewrite.

### Repair A — Valid owner authority

Constitutional property required:

- consequential owner authority must be reasonably attributable to the owner and voluntary;
- credential possession alone is not constitutional proof of authority;
- credible evidence of impersonation, coercion, or authorization compromise may trigger only a narrow temporary hold sufficient to verify authority;
- HumanOS presumes the owner's capacity and may not use disagreement, unconventional choices, emotion, diagnosis, or model confidence as a shortcut to declare the owner incapable;
- detailed authentication/verification technology remains subordinate.

### Repair B — Scope of owner sovereignty

Owner sovereignty governs HumanOS and the owner's own HumanOS authority. It does not manufacture authority over another person's independent rights, systems, property, information, body, identity, or consent.

This is not a limitation imposed by a model over the owner. It defines the boundary of what HumanOS sovereignty means.

### Repair C — Delegation, recovery, and succession boundary

The owner may define bounded, revocable delegation, emergency recovery, and succession procedures through governed instruments.

No credential holder, relative, executor, provider, model, employee, or delegate automatically acquires constitutional sovereignty through possession, proximity, or service role.

### Repair D — Rights-collision rule

When constitutional protections collide:

1. first separate the owner's own waivable interests from third-party/external constraints and structural anti-capture rules;
2. use the narrowest effective action and least necessary disclosure/restriction;
3. give strong effect to authenticated, voluntary, current owner choice for the owner's own interests;
4. do not let ordinary instruction silently waive structural rules such as no silent amendment, truthful status, or independent third-party boundaries;
5. unresolved consequential conflicts route to Review and remain visible.

A fixed universal value ranking is deliberately rejected because privacy, safety, truth, autonomy, and continuity can change weight by context.

### Repair E — Protected dissent without sovereign dissenters

Any authorized participant may submit concrete evidence that HumanOS, its authority state, or an implementation may be constitutionally wrong or compromised.

Submission creates a review claim, not command authority. Credible evidence is preserved and evaluated through the review workflow; the challenger may not self-execute, self-stay indefinitely, or self-ratify.

## 4. Matters deliberately kept subordinate

The following SHOULD NOT be added to constitutional text at this stage:

- biometric/KYC/device-attestation method;
- exact definition of cognitive or clinical incapacity;
- exact consent TTL;
- cryptographic signature schemes;
- succession/estate implementation mechanics;
- model-routing scores;
- database/storage technology;
- FRIEND count or voting rule;
- exact manipulation classifier;
- exact emergency-stay duration;
- exact artifact-ID format.

These need standards and tests, not constitutional permanence.

## 5. Result

**HF-0200 v0.2-rc1 should not be presented for local ratification unchanged.**

The frozen FRIENDS evidence identifies several important defects that rc1 did not fully close. The smallest repair is a successor candidate, `HF-0200 v0.2-rc2`, carrying Repairs A-E while preserving the rest of rc1.

After rc2 is created, a short **fresh independent delta challenge** should target only the new/changed constitutional surfaces plus any remaining HIGH/CRITICAL regression items. The old frozen reviews remain the broad blind baseline; the delta pass verifies that the repairs did not create new capture or paternalism loopholes.