# HumanOS Adaptive Learning Academy - Gradebook Snapshot v4.2

Date: 2026-09-20
Status: Current portable gradebook snapshot
Authority: Evidence-backed learning record; HumanOS runtime/tests/Git remain implementation truth.

## Verified engine metrics

| Metric | Current value | Evidence boundary |
|---|---:|---|
| Cybersecurity, DFIR & Incident Response completion | 23.1% | 3 of 13 seeded skills have non-UNSEEN continuation stages: dfir.evidence DEMONSTRATED, windows.telemetry PRACTICED, ir PRACTICED. |
| Cybersecurity, DFIR & Incident Response career readiness | 47.0% | Preserved historical checkpoint; not automatically recalculated by curriculum edits. |
| Cybersecurity, DFIR & Incident Response mastery | 0.0% in fresh engine | Historical evidence is not fully migrated into the evidence ledger. This is not a claim of zero real-world ability. |
| AI Systems Engineering & HumanOS completion | 4.8% | 1 of 21 seeded skills has a non-UNSEEN stage: ai.transformers INTRODUCED. The denominator expanded from 13 to 21 after enterprise-AI competencies were promoted. |
| AI Systems Engineering & HumanOS mastery | 0.0% in fresh engine | Prior HumanOS work exists but is not fully migrated as scored K/P/D/C evidence. |
| AI Systems Engineering & HumanOS career readiness | Not assigned | Do not invent a historical percentage. |
| AI Automation & Integration | INTRODUCED / ungraded | Requires completed build and recorded evidence before mastery is claimed. |

## Diagnostic planning estimates

These are planning baselines, not formal exam grades. They are retained until stronger scored evidence replaces them.

- HumanOS and AI Systems: 55%
- AI Evaluation and Red Team: 40%
- DFIR and Incident Response: 42%
- OSINT and Corporate Intelligence: 48%
- Linux and Systems: 38%
- Git and GitHub: 36%
- Python: 28%
- APIs and JSON: 25%
- SQL and Data: 18%
- Blockchain and Crypto Intelligence: 18%
- Markets and Quant: 20%
- Technical Communication and Client Work: 72%

## Tabletop and practical evidence credited

### First-response / ransomware decision lab
Historical assessed activity: **8/10 (80%)**.

Observed strengths:
- identified memory/running-process/log evidence as valuable;
- showed correct incident-response instincts;
- accepted and incorporated correction about containment ordering when active encryption/network exposure exists.

This activity is preserved as assessed practical evidence, but it is not converted into invented K/P/D/C subscores.

### TTX-001 - Compromised Account / Suspected Lateral Movement
Status: **IN PROGRESS - final tabletop grade still pending**.

Scenario chain:
compromised credentials -> second workstation -> file server -> customer-record access -> 2.3 GB outbound transfer; ZIP archive created roughly ten minutes earlier.

Credited decisions to date:
- did **not** prematurely declare confirmed customer-data exfiltration;
- chose containment/isolation while preserving the powered-on system for evidence;
- preserved volatile and persistent evidence;
- logged/blocked the external destination;
- prioritized verifying the actual data type/content before overstating scope;
- escalated internally to the security director;
- kept communications need-to-know through a controlled channel.

Learning consequence:
The repeated incident-response/tabletop work is enough to preserve **ir = PRACTICED** as a continuation point. This raises DFIR course completion to 23.1%. It does **not** close TTX-001 or create a final K/P/D/C grade.

TTX-001 still needs:
- final incident scope;
- evidence-vs-inference table;
- final containment rationale;
- stakeholder communication update;
- after-action reflection.

## Enterprise-AI curriculum promotion

The AI Systems Engineering & HumanOS course now includes 21 seeded skills. Newly promoted durable capabilities:

- RAG / vector knowledge systems
- AI observability
- AI platform/reference architecture
- enterprise AI governance and risk
- AI cost/performance engineering
- architecture documentation
- portable production deployment
- Azure / Azure AI Foundry as an implementation environment, not a HumanOS dependency

The HumanOS learning loop is:

**job requirement -> recurring-market check -> curriculum competency -> HumanOS implementation/lab -> tests/evidence -> portfolio artifact -> mastery update -> next market check**

## Portable production deployment rule

HumanOS must remain portable across:
- local workstation
- private/self-hosted server
- rented VPS/dedicated server
- private cloud
- public cloud
- hybrid deployment

Provider-specific platforms are replaceable implementation environments. Market demand may inform capability priorities but does not become architectural authority.

## Grading model

K/P/D/C weights remain:
- Knowledge 25%
- Practical 30%
- Diagnostic 25%
- Communication 20%

Completion, mastery, career readiness, diagnostic planning estimates, and individual activity grades are separate metrics and must not be collapsed into one percentage.

## Change log from v4.1

- PR #58 merged into runtime-0.1.
- Enterprise-AI competency cluster promoted into the code-backed AI course.
- AI course denominator expanded from 13 to 21 seeded skills.
- AI course completion recalculated from 7.7% to 4.8%; this is denominator growth, not lost learning.
- Historical first-response tabletop grade (8/10) explicitly preserved.
- TTX-001 partial evidence credited without falsely closing the exercise.
- Incident Response continuation stage promoted to PRACTICED.
- DFIR completion recalculated from 15.4% to 23.1%.
