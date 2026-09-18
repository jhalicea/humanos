# HumanOS Engineering Hardening — Research Intake

Status: PROPOSAL / REVIEW LATER
Source class: cross-project engineering research
Canonical impact: NONE until separately implemented, tested, reviewed, and promoted

## Principle

HumanOS should become more independent, safer, and easier to verify by turning architectural intentions into enforceable boundaries. The research does not replace the HumanOS Constitution, Workflow Standard, Context Engine lineage, or local verification requirements.

## Adopt as shared design heuristics

- Keep canonical HumanOS concepts provider-independent.
- Put replaceable services behind explicit interfaces/adapters.
- Treat all model outputs and retrieved content as untrusted proposals until deterministic policy or human approval authorizes an effect.
- Design core behavior to remain usable in degraded/no-AI mode.
- Prefer small reversible slices and one clear next action.
- Make retries/replays safe by design.
- Log provenance for model/prompt/tool behavior when it can affect durable state.
- Test restart, recovery, duplication, isolation, permission failure, and adversarial input.
- Distinguish immutable evidence from correctable views; preserve amendments instead of silent history rewrites.
- Make sensitive reads and exports explicit parts of the security model.
- Keep provider outage/restore/fallback procedures proportional to actual deployed capability.

## HumanOS surfaces worth reviewing

| Surface | Research question |
| --- | --- |
| Model router / swarm | Are providers truly interchangeable at the HumanOS boundary, and can one model's output gain authority accidentally? |
| Browser bridge | Can page content or prompt injection influence tool authority beyond the user's explicit request? |
| Work executor | Are retries atomic/idempotent and are consequential effects gated? |
| Context Engine | Are context assertions provenance-bound and prevented from becoming implicit action authority? |
| Life Notebook | Are append-only evidence, amendments, replay, restore, and sensitive-read access handled consistently? |
| File intelligence | Are external/file instructions treated as data rather than authority? |
| Inbox automation | Are email bodies and links untrusted, with outbound actions permission-scoped? |
| Backup/portability | Are restore drills and degraded-mode operation verified, not merely documented? |
| CI/repository | Are sensitive paths protected with stronger review and automated checks? |

## Do not generalize from BodyFixOS

Health-data compliance, clinical retention, booking concurrency, and patient/client rules are BodyFixOS-domain concerns unless a HumanOS feature independently needs equivalent controls.

## Evidence rule

A research suggestion becomes a HumanOS standard only after:
1. a bounded work order;
2. baseline inspection;
3. implementation or documentation diff;
4. tests/evidence appropriate to the risk;
5. independent review;
6. owner promotion approval;
7. post-promotion verification.
