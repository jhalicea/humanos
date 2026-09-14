# HumanOS FRIENDS Research Addendum — 2026-09-14

Status: **RESEARCH ADDENDUM / IMPLEMENTED-CANDIDATE CROSSWALK**

This addendum connects the Sept. 14 FRIENDS convergence research (OpenAI/Codex, xAI/Grok, Google/Gemini, Anthropic/Claude, DeepSeek) with the later verified agent-reliability research and the HumanOS Reality Loop R1 candidate.

It does **not** claim that all five FRIENDS were re-queried on these new findings. The earlier FRIENDS outputs remain historical research inputs. This document records how the new evidence changes or strengthens the convergence conclusions.

## New verified external evidence

1. Anthropic, **An alignment assessment of recent cybersecurity incidents** (2026-09-09)
   - strengthens the FRIENDS convergence that deterministic authority must remain outside LLMs;
   - adds explicit evidence for biased interpretation of contradictory environment signals and reckless goal persistence;
   - supports independent behavior monitoring and impossible-task testing;
   - supports re-checking authorization and reality during long trajectories rather than trusting an initial prompt.

2. Mittal, **How Fast Do Agents Rot? An Empirical Study of Long-Horizon Degradation in LLM Agents for Production Decision-Making** (arXiv:2609.01660)
   - adds a new evaluation dimension absent from the original convergence report: dependent-step horizon;
   - suggests HumanOS should benchmark 1/2/4/8/16/32/64+ step workflows and report cumulative reliability, not only one-shot scores.

3. NIST, **TEVV-Athlon Framework for Evaluating AI Systems**
   - reinforces HumanOS's evidence-first design;
   - motivates explicit mapping from events and tools to measurements, verification, and acceptance criteria.

## FRIENDS convergence update

The original convergence remains sound:

- deterministic authority outside LLMs;
- model independence;
- brokered capabilities;
- MCP is not authority;
- brokered agents and no hidden agents;
- self-development allowed, self-authorization forbidden;
- independent verification where specialization or adjudication adds measurable value.

The new research adds four requirements that should now be treated as first-class HumanOS design/evaluation goals:

1. **Reality Loop**
   - Goal -> Plan -> bounded block -> Observe -> Verify -> Checkpoint -> Reconsider -> Next.
   - Hard stop when evidence no longer matches assumptions.

2. **Horizon Reliability**
   - Track reliability as a function of dependent step count.
   - Do not treat long-context capability as equivalent to long-horizon reliability.

3. **Epistemic Independence**
   - A verifier should not automatically inherit the acting agent's explanatory narrative.
   - Where practical, verification should use observable evidence, independent retrieval, and heterogeneous models.

4. **Safe Autonomy / Lab Autonomy**
   - Production authority remains bounded.
   - Broad experimentation belongs in disposable, isolated, instrumented environments where failure cannot enlarge external authority.

## New experiments for the FRIENDS program

- `EXP-FRIENDS-HORIZON-001`: run equivalent tasks at 1, 2, 4, 8, 16, 32, 64+ dependent steps across available models.
- `EXP-FRIENDS-BELIEF-002`: seed one agent with a false premise and measure whether peers independently verify or copy the belief.
- `EXP-FRIENDS-IMPOSSIBLE-003`: give agents tasks with no legitimate solution and score willingness to stop rather than bypass constraints.
- `EXP-FRIENDS-MOMENTUM-004`: inject contradictory evidence after sustained goal pursuit and measure whether the agent revises or persists.
- `EXP-FRIENDS-AUTHORITY-005`: revoke authority mid-run and verify no subsequent external effect occurs.
- `EXP-FRIENDS-LAB-006`: compare model learning/problem-solving freedom inside an isolated disposable lab versus production-bounded operation.

## Implementation crosswalk

Current HumanOS candidate implementation is PR #60 and includes:

- `reality_loop.py`
- `tests/test_reality_loop.py`
- `REALITY_LOOP.md`

The candidate implements the first slice only. It does not yet implement the full assumption ledger, cross-agent belief-contamination harness, automated multi-model horizon benchmark, second isolated behavioral monitor, or lab-autonomy runtime.

## Truth boundary

- FRIENDS convergence research: **RESEARCHED / DOCUMENTED**.
- Reality Loop R1: **IMPLEMENTED CANDIDATE** pending CI/review/host verification.
- Full FRIENDS re-evaluation against the new evidence: **NOT YET RUN**.
- Cross-agent contamination, full horizon matrix, and lab-autonomy experiments: **DESIGNED / NOT YET IMPLEMENTED**.
