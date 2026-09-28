# HumanOS Engineering Hardening — Research Intake

Status: PROPOSAL / REVIEW LATER
Source class: cross-project engineering research
Canonical impact: NONE until separately implemented, tested, reviewed, and promoted

## Principle

HumanOS should become more independent, safer, and easier to verify by turning architectural intentions into enforceable boundaries. The research does not replace the HumanOS Constitution, Workflow Standard, Context Engine lineage, or local verification requirements.

The portability rule is:

> Portability is not a claim. It is a tested capability with an exit level, exit path, and recorded exit drill.

## Ports versus connectors

Do not treat every external dependency the same.

**Port:** a replaceable provider/runtime boundary whose implementation may change while HumanOS capability semantics remain stable.

Examples:
- model/inference provider;
- storage implementation;
- notification transport;
- future auth provider;
- future task/queue backend.

**Connector:** a deliberately supported external system whose purpose is interoperability, not disappearance.

Examples:
- Google Drive;
- GitHub;
- browser bridge/service;
- calendars;
- email/inbox sources;
- future third-party apps.

Ports need substitution contracts and fake/alternate implementations where risk justifies it. Connectors need scoped credentials, stable import/export/event semantics, explicit data classes, and graceful degradation when the external system is unavailable.

## Independence ladder

Assess each capability separately:

| Level | Meaning |
| --- | --- |
| L0 | Provider concepts leak into canonical HumanOS state or behavior. |
| L1 | Canonical data can be exported in documented/open formats. |
| L2 | A fake or alternate implementation passes a shared capability contract and a bounded provider switch is possible. |
| L3 | The capability can be deployed/restored elsewhere and the exit drill has passed. |
| L4 | HumanOS operates the infrastructure itself. |

Default posture: pursue L2 for high-risk provider boundaries; L3 for canonical data, backups, and critical runtime portability when useful; pursue L4 only from a real owner/security/economic requirement.

## Adopt as shared design heuristics

- Keep canonical HumanOS concepts provider-independent.
- Put high-lock-in/high-risk replaceable services behind domain-shaped interfaces/adapters.
- Do not abstract every library or implementation detail merely for symmetry.
- Prefer open standards and open export formats where they meet the requirement.
- Treat all model outputs and retrieved content as untrusted proposals until deterministic policy or human approval authorizes an effect.
- Design core behavior to remain usable in degraded/no-AI mode.
- Prefer small reversible slices and one clear next action.
- Make retries/replays safe by design.
- Log provenance for model/prompt/tool behavior when it can affect durable state.
- Test restart, recovery, duplication, isolation, permission failure, adversarial input, and provider exit where relevant.
- Distinguish immutable evidence from correctable views; preserve amendments instead of silent history rewrites.
- Make sensitive reads and exports explicit parts of the security model.
- Keep provider outage/restore/fallback procedures proportional to actual deployed capability.
- Prefer trigger-based provider replacement (security failure, owner requirement, outage, cost threshold, capability gap) over calendar-based rewrites.

## Exit-drill examples

| HumanOS surface | Candidate exit evidence |
| --- | --- |
| Model router / swarm | Disable provider A; run the same bounded capability through fake/provider B/local adapter and compare contract/eval evidence. |
| Life Notebook | Restore an encrypted export on another machine/location and verify counts, hashes, provenance, and readability. |
| Backup/portability | Restore onto a clean environment and prove the documented recovery point rather than only creating backup files. |
| Google Drive connector | Export canonical HumanOS-owned records and prove HumanOS does not lose its own identifiers/meaning if Drive is unavailable. |
| GitHub | Mirror/clone repository history elsewhere and verify branches/tags/releases required for recovery. |
| Browser bridge | Disable browser integration and verify core HumanOS functions degrade safely rather than failing globally. |
| Inbox connector | Disconnect source; preserve HumanOS-owned state and resume safely after reconnection without duplicate side effects. |

## HumanOS surfaces worth reviewing

| Surface | Research question |
| --- | --- |
| Model router / swarm | Are providers truly interchangeable at the HumanOS boundary, can one model's output gain authority accidentally, and what independence level is actually proven? |
| Browser bridge | Can page content or prompt injection influence tool authority beyond the user's explicit request, and is browser availability a connector dependency rather than core authority? |
| Work executor | Are retries atomic/idempotent and are consequential effects gated? |
| Context Engine | Are context assertions provenance-bound and prevented from becoming implicit action authority? |
| Life Notebook | Are append-only evidence, amendments, replay, restore, exit formats, and sensitive-read access handled consistently? |
| File intelligence | Are external/file instructions treated as data rather than authority? |
| Inbox automation | Are email bodies and links untrusted, with outbound actions permission-scoped and reconnect/replay safe? |
| Backup/portability | Are restore and provider-exit drills verified, not merely documented? |
| CI/repository | Are sensitive paths protected with stronger review and automated checks? |
| External connectors | Are HumanOS IDs/data semantics preserved independently of provider object IDs and payload formats? |

## Provider/connector register fields to consider

- capability;
- relationship type: PORT or CONNECTOR;
- provider/product;
- allowed data classes;
- HumanOS-owned canonical state;
- provider-held state;
- external identifiers;
- export mechanism;
- fallback provider/path;
- contract/renewal dependency;
- estimated switching time;
- last exit-drill date/result;
- observed blockers;
- current L0-L4 level.

## Do not generalize from BodyFixOS

Health-data compliance, clinical retention, booking concurrency, payment settlement, and patient/client rules are BodyFixOS-domain concerns unless a HumanOS feature independently needs equivalent controls.

## Evidence rule

A research suggestion becomes a HumanOS standard only after:
1. a bounded work order;
2. baseline inspection;
3. implementation or documentation diff;
4. tests/evidence appropriate to the risk;
5. independent review;
6. owner promotion approval;
7. post-promotion verification.
