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
  → Local QA model chooses allowlisted read, diff, focused tests and declarative security probes; trusted host enforces each action
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
| **QA worker HOS-QA-001** | **v2 candidate: model-directed inspect/test/probe loop with host enforcement** | Source-aware investigations, experimental declarative tests, evidence |
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
5. In v2, an **explicitly selected local-only model** may receive bounded
   excerpts from Git-tracked Python/Markdown source, reviewed diffs and synthetic
   test observations. It never receives owner Notebook or arbitrary host files.
   Local model trust is not OS isolation; use only explicitly approved,
   synthetic/test-only code and never send secret source to hosted models.
   Executable test code is already in the verified candidate checkout. Agent
   authored tests are bounded **declarative probes**, not arbitrary Python.
6. Every report names immutable baseline and candidate SHA. Test execution
   success and model opinion are separate fields. Evidence SHA is an ordinary
   integrity checksum, **not an authenticated signature**.
7. Rebase/new commit => stale QA evidence; rerun checks.
8. Independent human reviews may be recommended for high-stakes operations,
   but do not invent a constitutional rule requiring them for every ordinary
   software change. A release-specific stronger gate remains in force until
   the owner explicitly decides otherwise.

## First sprint and metrics

1. **RUNNABLE QA V2 CANDIDATE:** mandatory synthetic tests followed by a
   localhost model-directed tool/observation loop. The host decides permissions;
   model chooses inspection and test actions within exact-SHA bounds.
   Test results and model assessments remain distinct. The worker cannot publish.
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

## HOS-QA-001 v2 — first agentic operation (candidate)

The first version was a deterministic QA runner with a one-shot AI opinion.
v2 adds a **real bounded agent loop** in `qa_investigator.py` behind
`qa_agent.py --agentic --model llama3.2:latest`.

The host always runs the mandatory three tests first. A local model then may
choose `list_files`, `read_file`, `inspect_diff`, `run_test`, or
`run_probe` (the currently implemented declarative probe is the macOS HOME
alias workspace-denial check). It receives the prior observation and may
change its next action. Tools are executed by a trusted host broker in a
temporary detached worktree, with strict relative-path validation and an
eight-step limit. Neither model proposals nor outputs have merge permissions.

**Safety and truth:** This makes the worker **agentic**, but it does not
make it a full engineer, code-writing agent, OS sandbox, independent security
reviewer, or autonomous company. The model cannot run shell commands or
supply arbitrary Python. The current probe catalog is deliberately tiny;
additional probes require an explicit security-reviewed host change.

The v2 JSON receipt has model action IDs, tool outcomes, hashes, a model
conclusion with observation references, and `qa_verdict`. If all finite
checks pass, QA remains `INCONCLUSIVE` for global release; a failed
deterministic check becomes `FAIL`. The owner must decide next steps.

**Owner-host launch:** after checking exact commits and using a fresh private
report directory and a separate v2 worktree:

```text
python3 qa_agent.py --agentic --model llama3.2:latest \
    --repo /ABSOLUTE/HUMANOS/REPO \
    --baseline EXACT_40_HEX_BASE \
    --target EXACT_40_HEX_CANDIDATE \
    --report /OWNER_PRIVATE/DIRECTORY/qa-v2.json
```

The `--agentic` command is **opt-in** and does not rewrite v1 behavior.
Live owner-host validation and independent QA/security evaluation remain
pending. No user data ingestion is authorized.
