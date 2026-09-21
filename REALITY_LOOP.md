# HumanOS Reality Loop R1

Status: **IMPLEMENTED CANDIDATE — NOT YET MERGED OR HOST-VERIFIED**

## Purpose

Convert recent agent-reliability and alignment research into executable HumanOS development behavior.

Core cycle:

`GOAL -> PLAN -> BOUNDED EXECUTION BLOCK -> OBSERVE REALITY -> VERIFY -> CHECKPOINT -> RECONSIDER -> NEXT BLOCK`

Hard stop:

`STOP -> evidence no longer matches assumptions`

The design deliberately treats model reasoning as advisory and observable evidence plus trusted host policy as authoritative.

## Verified research inputs

1. Anthropic, **An alignment assessment of recent cybersecurity incidents** (2026-09-09):
   https://www.anthropic.com/research/alignment-assessment-cybersecurity-incidents

   Research implications adopted here:
   - models can persist recklessly toward an assigned goal;
   - models can interpret contradictory evidence in a biased way;
   - impossible tasks and mixed simulation/real-world signals deserve explicit testing;
   - long trajectories need stronger runtime monitoring;
   - authorization and environment boundaries must not depend on the acting model's beliefs.

2. Mittal, **How Fast Do Agents Rot? An Empirical Study of Long-Horizon Degradation in LLM Agents for Production Decision-Making** (arXiv:2609.01660):
   https://arxiv.org/abs/2609.01660

   Research implication adopted here:
   - evaluate reliability as a function of dependent step count and impose explicit horizon limits/checkpoints rather than relying on aggregate pass rates.

3. NIST, **TEVV-Athlon Framework for Evaluating AI Systems**, initial public draft announced 2026-08-07:
   https://www.nist.gov/artificial-intelligence/ai-research/tevv-athlon-framework-evaluating-ai-systems

   Research implication adopted here:
   - structure evidence around explicit events, tools, measurements, verification, and acceptance criteria.

## R1 runtime primitive

`reality_loop.py` adds a provider-neutral execution controller with these properties:

- `max_blocks` is explicit and cannot silently expand.
- Authority is refreshed immediately before every consequential execution block.
- A revoked/absent authority snapshot stops before the effect occurs.
- The verifier receives observable evidence and current authority, not the worker's hidden/private rationale.
- Evidence mismatch is a hard stop before checkpoint or further work.
- Checkpoint occurs only after successful verification.
- Reconsideration occurs only after verified evidence.
- An impossible task may return `no_legitimate_path` instead of encouraging workaround behavior.
- Result telemetry records attempted/completed blocks, verifications, checkpoints, history, and stop reason.

## Initial regression family

`tests/test_reality_loop.py` covers:

- normal verified completion;
- momentum/persistence stop when reality contradicts an assumption;
- authority refresh and mid-run revocation;
- impossible task with no legitimate path;
- explicit 32-block horizon accounting;
- behavior-only verifier interface that excludes worker rationale.

## Existing HumanOS preparation already present before R1

HumanOS already had several strong controls that align with the new research:

- immutable authorization envelope and target allowlist;
- model-neutral trusted `ControlPlane` outside the LLM;
- capability manifests and declared peer routes;
- fail-closed escalation for unknown tools, scope escape, unexpected privilege, and high-impact requests;
- append-only broker action/result ledger;
- heterogeneous coordinator/worker/verifier model roles without authority expansion;
- adversarial tests proving heterogeneous models do not widen targets, tools, peers, or authorization.

These are important strengths, but they do **not** by themselves prove long-horizon reliability or independence of verifier beliefs.

## Gaps after R1

R1 intentionally does not yet claim all of the following are production-integrated:

- wiring `RealityLoop` into every HumanOS agent/swarm workflow;
- automated 1/2/4/8/16/32/64+ horizon benchmark runs across real local/commercial models;
- a formal assumption ledger with provenance and confidence changes;
- cross-agent belief-contamination experiments;
- a second behavioral monitor isolated from actor narrative;
- impossible-task suites across non-cyber HumanOS workflows;
- explicit metrics for agent-hours per human-hour, recovery attempts, interventions, duplicate actions, and accepted/rejected autonomous improvements;
- full TEVV-Athlon mapping of every HumanOS evaluation.

Those should be implemented incrementally and must not be labeled VERIFIED until the corresponding executable tests and host evidence exist.
