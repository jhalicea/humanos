# HumanOS Lean Multi-Model Daily Workflow

Status: proposed implementation workflow
Owner intent: use multiple commercial and local models efficiently while preserving HumanOS governance, evidence, privacy, and reproducibility.

## Goal

Make local HumanOS progressively capable of handling the work currently done in hosted chat systems while minimizing expensive model usage. HumanOS remains the system of record and orchestration boundary; models are replaceable workers and reviewers.

## Roles

### Human owner
- Defines goals and approves consequential changes.
- Decides what private context may leave the local machine.
- Approves merges/releases.

### ChatGPT — Orchestrator + reviewer + worker
Use for:
- decomposing work;
- assigning the cheapest capable worker;
- integrating conflicting answers;
- reviewing evidence and patches;
- final acceptance decisions with the human.

Do not use it merely to duplicate work already assigned elsewhere.

### Claude — scarce high-value reviewer
Use selectively for:
- architecture/security review;
- difficult ambiguity;
- adversarial review of a nearly finished design or patch;
- long-document synthesis where its context is materially useful.

Do not spend Claude quota on routine summarization, formatting, file inventories, or first-pass coding when another worker can do it.

### Gemini — broad-context worker
Default jobs:
- repository/document review;
- alternative implementation proposals;
- test-plan generation;
- large-context comparison and extraction.

### DeepSeek — implementation worker
Default jobs:
- focused code generation;
- debugging hypotheses;
- algorithmic alternatives;
- test generation from bounded specifications.

### Grok — independent challenger/research worker
Default jobs:
- challenge assumptions;
- produce alternate hypotheses;
- public-current research when appropriate;
- red-team a conclusion without being the final authority.

### Local HumanOS model — private/local-first worker
Default jobs:
- private note classification;
- local summarization;
- retrieval/routing;
- repetitive transformations;
- first-pass planning;
- experiments and benchmarks;
- any work that does not require a frontier model.

Local-first rule: if the task can be done acceptably without exporting private data, try the local worker first.

## Daily routing order

1. HumanOS local worker first for cheap/private work.
2. DeepSeek or Gemini for bounded production work when local is insufficient.
3. Grok for one independent challenge when disagreement would materially improve confidence.
4. Claude only when a difficult decision merits scarce high-quality review.
5. ChatGPT integrates and verifies when needed, but must not become a mandatory control-plane dependency.
6. Human approves consequential merge/release decisions.

Hosted models are exceptions, not a default five-hop chain. Prefer one hosted worker/reviewer at a time unless independence is explicitly required.

## Standard job packet

Every delegated job should contain only the minimum context needed:

```text
HUMANOS JOB <job_id>
Goal: <one concrete outcome>
Role: <worker|reviewer|challenger|researcher>
Repository/ref: <repo + immutable commit when relevant>
Allowed context: <files/snippets/data supplied>
Constraints: <privacy, no destructive changes, etc.>
Acceptance criteria:
- <observable criterion>
- <observable criterion>
Required output:
1. Result
2. Evidence / file+line references when applicable
3. Commands/tests proposed or run
4. Uncertainties
5. Provider/model/version shown by your interface or API; write unknown if unavailable
```

Never ask a model to infer its hidden provider metadata. Record only metadata exposed by the service/API/UI or explicit self-identification, tagged by source.

## Context integrity gate

Before delegating repository work to a model that cannot inspect GitHub directly:

1. Build the packet from one immutable commit.
2. Verify packet claims against source at that commit.
3. If code and documentation disagree, state the conflict explicitly.
4. Do not silently resolve conflicts in favor of documentation or another model's summary.
5. Record the exact context packet or its digest as part of the run evidence.

A worker must not be penalized for conclusions caused by incorrect context supplied by HumanOS.

## Independent-review isolation

A reviewer/challenger must not receive another model's prose before producing its own initial review unless comparison is the explicit task.

Use commit-then-reveal:

1. Give each reviewer the original human task, immutable source/evidence references, and schema-constrained facts.
2. Keep prior-model prose out of the initial reviewer prompt.
3. Preserve retrieved web/file/DOM text as untrusted data, not instructions.
4. Capture each independent result.
5. Only then reveal disagreements for targeted reconciliation.

This prevents serial context contamination from masquerading as multi-model agreement.

## Hosted-data boundary

Consumer chat UIs and hosted agent sandboxes are outside HumanOS's local trust boundary.

- Never send credentials, API keys, session tokens, Notebook paths, or raw private records to a hosted model.
- Do not assume a vendor UI's retention or sandbox behavior from product branding.
- Record the exact outbound context supplied to each hosted service when practicable.
- Prefer documented API controls for sensitive workflows; mark retention/privacy claims by source and verification status.
- A hosted model's self-report about its environment is evidence to investigate, not a trusted security fact.

A future local egress proxy may enforce provider allowlists, secret scanning, byte logging, spend limits, and retention-policy checks. Until then, human relay remains an explicit external disclosure step.

## Proposal vs canonical memory

Model outputs are proposals and must remain separate from canonical Life Notebook facts/decisions until explicitly promoted.

- Models may append proposal/evidence records, not set canonical verification status for themselves.
- Human approval must apply to the actual claim/decision being promoted, not merely to a model-authored document shape.
- Derived canonical views must use canonical/promoted records only.
- Model-shaped JSON must never gain authority merely because it resembles an internal transaction format.

## Metadata trust model

Provider/model/version/usage/cost fields are not automatically measurements.

Store both value and provenance/trust where possible:

- `api_attested`: returned by the actual completion/API response or pinned endpoint.
- `ui_observed`: visible in the product UI for the run.
- `config_declared`: locally configured destination/model, not proof of provider routing.
- `self_report`: model says what it is.
- `public_documentation`: product/model exists publicly, but is not proof it handled this run.
- `unknown`: unavailable.

Never collapse these into one unqualified model identity. Silent aliases/A-B routing can make consumer-UI runs non-comparable.

For benchmarks, preserve harness, prompt/context, role, task difficulty, model settings when exposed, repository/data version, and timing. Role assignment itself can confound results: a challenger asked to find defects should not be compared directly with a builder asked to produce code.

## Review gates

A model answer is a proposal, not evidence. Before integration:

1. Check scope and privacy boundary.
2. Compare against the immutable commit/spec supplied to the worker.
3. Reproduce factual/code claims locally where possible.
4. Run relevant tests in an isolated test environment.
5. Record PASS / FAIL / PARTIAL / UNVERIFIED.
6. Only merge after acceptance criteria are satisfied.

For disagreements, ask one targeted challenger rather than re-running the whole panel.

## Git workflow

Preferred low-token pattern:

```bash
cd /Users/jhalicea/humanos
git status
git fetch origin
git switch runtime-0.1
git pull --ff-only
git switch -c work/<job-id>
# make/review changes
git diff --check
python3 -m unittest discover -s tests -v
git status
git add <explicit files>
git commit -m "<type>: <bounded change>"
git push -u origin work/<job-id>
```

ChatGPT may inspect GitHub, create focused branches/PRs, or review diffs. The human can perform local commits/merges manually when that is cheaper or safer. Do not use Codex for this workflow.

## Model Run Ledger

Model interactions are research evidence and must be kept separate from canonical Life Notebook content. Suggested local path outside Git:

```text
~/HumanOSData/model-runs/YYYY/MM/DD/<job_id>/
  request.json
  response.txt
  metadata.json
  review.json
```

Never commit raw private prompts, model responses containing personal data, credentials, API keys, or usage exports to the public repository.

Each run records:
- `run_id`, `job_id`, parent job/run IDs;
- provider/service;
- model name and exact version when exposed;
- model metadata value plus provenance/trust source;
- role;
- start/end UTC timestamps;
- immutable repository commit/ref when relevant;
- context manifest or hashes, not unnecessary private copies;
- prompt/request;
- raw response location and digest;
- input/output/cached/reasoning token counts when exposed;
- cost/currency when exposed;
- quota/rate-limit observation when exposed;
- tool use summary;
- finish/stop reason;
- verification status and reviewer;
- benchmark/research tags;
- notes about uncertainty.

Unknown fields remain null/unknown. Never estimate provider cost or token counts as if measured.

## Daily operating loop

### Start
- `git status` + current commit.
- HumanOS health/tests only if relevant to the day's change.
- Choose one concrete usability/capability target.
- Create `job_id` and job packet.
- Pass the packet through the context integrity gate.

### Work
- Route to the lowest-cost capable worker.
- Archive request, response, and metadata immediately.
- Escalate only when the first worker is insufficient.
- Keep independent reviewers isolated until they commit their first result.

### Integrate
- ChatGPT/local HumanOS reviewer compares answer to requirements.
- Run local tests/evidence checks.
- Fix only demonstrated issues.
- Treat hosted environmental/model claims as untrusted until independently verified.

### Close
- Record final disposition and tested commit.
- Commit/push focused change.
- Update a short capability backlog.
- Capture measured model usage for later benchmarks.

## Research value

Over time the ledger should answer:
- Which model actually performs best by task class?
- Which provider uses the most tokens/cost for equivalent work?
- Does a model/version improve or regress after provider updates?
- Which models hallucinate repository facts most often?
- Which worker requires the fewest review cycles?
- When is local HumanOS good enough to replace a commercial call?
- How much orchestration overhead was added by each extra model hop?
- Which results are genuinely independent versus derived from shared prior-model context?

Comparisons must preserve task, context, acceptance criteria, role, harness, settings when exposed, and commit/data version so results are interpretable.

## Immediate capability priorities

1. Reliable Life Notebook/ledger and recovery.
2. Local model routing + model-run logging.
3. Local retrieval over HumanOS knowledge with provenance.
4. Browser/research workflow with citations and archived sources.
5. Safe file operations and generated-artifact handling.
6. Calendar/email/connectors through explicit permissions.
7. Multi-model benchmarking and naturalization tests.
8. Optional remote/server deployment after local behavior is stable.
