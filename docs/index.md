# HumanOS documentation

HumanOS is a local-first AI runtime and engineering project focused on continuity, evidence, privacy, and human authority. This map links current architecture and operating guidance with clearly labeled research and historical work.

## Start here

| If you want to… | Read |
|---|---|
| Run the current local runtime | [Getting started](getting-started.md) |
| Understand the system boundaries | [Architecture](architecture.md), [Mirror runtime](mirror-runtime.md) |
| Review privacy and security assumptions | [Security and privacy](security-and-privacy.md), [Limitations](limitations.md) |
| Understand durable conversation and recovery records | [Life Notebook](life-notebook.md) |
| See how models and tools are governed | [Model governance](model-governance.md) |
| Run tests and interpret evidence | [Testing and evidence](testing-and-evidence.md) |
| Find the next planned areas | [Roadmap](roadmap.md) |
| Contribute a bounded change | [Contributing](contributing.md) |

## Public architecture and implementation

### Foundation and governance

- [Constitution copy and provenance](../core/constitution.md)
- [Foundation ratification record](FOUNDATION_RATIFICATION.md)
- [Workflow standard](foundation/WORKFLOW_STANDARD.md)
- [Context registry](foundation/CONTEXT_REGISTRY.md)
- [Public artifact register](foundation/ARTIFACT_REGISTER.md)

### Runtime and data lifecycle

- [Architecture](architecture.md)
- [Mirror responsibilities](mirror-runtime.md)
- [Life Notebook](life-notebook.md)
- [Security and privacy](security-and-privacy.md)
- [Testing and evidence](testing-and-evidence.md)

### Learning and mastery

- [Public adaptive mastery architecture](ADAPTIVE_MASTERY.md)
- [`learning/` generic engine and catalog](../learning/)

Public learning material uses generalized interfaces and synthetic examples. Real learner curricula, grades, progress, assessments, evidence, and personalized skill maps are private.

### Agents and orchestration

- [Authorized swarm broker design and trust limits](../SWARM.md)
- [Swarm runtime v3 status](../SWARM_V3.md)
- [`swarm_runtime.py`](../swarm_runtime.py)

The broker validates bounded proposals and capabilities. It is not an operating-system sandbox for arbitrary code and is not described as an autonomous model scheduler.

## Research and evidence

- [Research index](RESEARCH_INDEX.md)
- [Model qualification research](MODEL_QUALIFICATION_RESEARCH.md)
- [Enterprise AI systems portability](ENTERPRISE_AI_SYSTEMS_PORTABILITY.md)
- [Testing and evidence](testing-and-evidence.md)
- [Work orders and implementation records](work-orders/)

Research and work orders preserve the reasoning and scope of prior slices. Their presence does not make a proposal a current runtime capability; check the implementation, tests, and stated status.

## Privacy boundary

This public documentation describes generalized software and architecture. Do not place real learner state, job applications, employer-specific preparation, private conversations, client records, credentials, or personal operational data here. Use synthetic examples in public tests and docs.

## Capability labels

HumanOS distinguishes **implemented**, **tested**, **verified**, **documented**, **specified**, and **planned** work. A test run establishes only the behavior it exercises; CI, local host checks, and provider-level evidence are separate.
