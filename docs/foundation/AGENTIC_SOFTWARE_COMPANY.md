# HumanOS — Agentic Software Company Operating Model v0.1 (CANDIDATE)

**Owner:** Human owner. **Workstream:** HOS-QA-001 (first worker / company prototype).
**State:** Proposal and runnable synthetic first slice; NOT an incorporated company, staffed workforce, launched product, or production release.
**Workspace:** WS-HUMANOS. **Canonical authority:** HumanOS governance and owner approval.

## Business thesis

One human owner directs an AI-assisted software studio. Models produce bounded
proposals and implementation artifacts; deterministic infrastructure carries out
explicitly authorized operations; independent QA examines the result; HumanOS
preserves evidence and permissions. The owner chooses products, budgets, risk,
pricing, clients, and when anything is published.

This is **not** a promise that AI agents are legally employees or that a company
can operate without human legal, tax, contractual, privacy and financial duties.
Those duties remain with the owner and, later, qualified human professionals.

## The company workflow — first useful operating loop

Owner chooses a product and approves a bounded work order
  → Mirror routes it to an existing HumanOS workstream
  → Research / product worker proposes evidence and specifications
  → Engineering worker creates a reviewed draft patch
  → **HOS-QA-001** checks the exact candidate with trusted synthetic tests
  → Local AI worker suggests adversarial hypotheses (no tools or permissions)
  → Security findings are reproduced and classified
  → Human owner reviews cost, scope, risk and evidence
  → Owner may authorize a separate merge/release transaction
  → Life Notebook/evidence ledgers preserve the decision and test receipts.

Worker outputs are **data/proposals**, not authority. No model self-approval.
A model can be correct and still lack permission: Capability Is Not Authority.

## Workforce roadmap (roles, not unbuilt agents)

| Role | Immediate status | Future deliverable |
|---|---|---|
| Founder/product owner | Human: ACTIVE | Priorities, approvals, contracts, capital |
| Mirror/Work Supervisor | Existing HumanOS components | Controlled dispatch and owner-facing status |
| Engineering worker | Existing model/tool loops; no autonomous software-company worker launched | Patches on bounded candidate branches |
| **QA worker HOS-QA-001** | **This candidate implements a narrow executable version** | Exact-SHA synthetic validation, audit questions and evidence |
| Security/Red Team | Existing specialist broker for authorized targets; NOT a software-release auditor | Adversarial code test role under separate scope |
| Research/Product manager | Planned | Verified requirements and product discovery |
| Release/Operations | Planned | Owner-approved deployment, monitoring, rollback |
| Customer support/Finance | Planned | Client-facing process with privacy and legal controls |

Do not create workers without measurable value. Scale only after the first
end-to-end workflow is reliable.

## Execution invariants

1. One owner-approved task, clear objective, frozen SHA, finite file scope,
   evidence criteria and rollback per slice.
2. One least-expensive capable AI worker at LOW reasoning effort when exposed;
   local deterministic methods first. Never escalate automatically.
3. A QA worker **cannot** merge, deploy, grant permissions, read private owner
   Notebook state or classify itself as independent human security approval.
4. It may run trusted repository test code in an isolated detached worktree,
   using only synthetic HOME/config paths. This is **not an OS sandbox**; run
   only reviewed repository code on an owner-controlled host. Add real sandboxing
   before untrusted code or arbitrary agents are executed.
5. Models receive only bounded host-derived observations. No raw logs,
   credentials or personal records are sent. This first worker does NOT pass
   the source diff into its model; it suggests hypotheses from file names and
   checked outcomes, not a complete code audit.
6. Every report names immutable baseline and candidate SHA. Test execution
   success and model opinion are separate fields. Evidence SHA is an ordinary
   integrity checksum, **not an authenticated signature**.
7. Rebase/new commit => stale QA evidence; rerun checks.
8. Independent human reviews may be recommended for high-stakes operations,
   but do not invent a constitutional rule requiring them for every ordinary
   software change. A release-specific stronger gate remains in force until
   the owner explicitly decides otherwise.

## First sprint and metrics

1. **RUNNABLE QA:** synthetic test suite + optional localhost model advisory.
   Definition: QA worker catches failing tests, changed commits, missing scripts,
   bad repository identity, and unsafe model output while never publishing.
2. **PRODUCT LOOP:** apply QA to the frozen Life Notebook candidate; record
   truthful pass/fail/advisory evidence with explicit owner action.
3. **OPERATIONS:** owner approves the intended staged promotion and rollback.
   Only then investigate one controlled real conversation; do not bulk ingest.
4. **FIRST REVENUE PRODUCT:** select a narrow externally useful software offer
   after HumanOS itself proves repeatable delivery and privacy boundaries.

Metrics: evidence completeness, reproduced QA defects, test pass rate,
owner interventions, end-to-end lead time, tokens/$ per approved artifact,
recoverability, and whether owners can replay/review the underlying proof.
Do not treat generated code volume or number of agents as success.

## Initial QA invocation

In a separate detached checkout of the QA PR candidate, use
\`python3 qa_agent.py --repo /absolute/verified/humanos/repo --baseline
<exact-40-hex-canonical-sha> --target <exact-40-hex-candidate-sha>\`.
Use \`--model <local-ollama-name>\` only after checking its identity and
availability; no network discovery, remote provider, or real data access.
No model => tests run, advisory is visibly NOT CONFIGURED and QA verdict
is INCONCLUSIVE, not fabricated.

The owner-Mac local canonical ref can differ from GitHub canonical; this
prototype never resets or rebases it. QA branch remains independent of the
Life Notebook release stack and Astra PR #127.

## Boundaries and future decisions

The agent is **not a daemon**, not automatically scheduled, not an end-to-end
corporate workforce, not a replacement for security certification, and does
not itself modify software. It does not accept arbitrary shell/model tools.
Future workers should reuse the established HumanOS broker/work contracts,
permission checks, state provenance and owner gates rather than creating
a parallel agent operating system. Company incorporation, finances,
client data, products and deployment require separate owner decisions.
