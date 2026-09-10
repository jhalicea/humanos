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
2. DeepSeek or Gemini for bounded production work.
3. Grok for an independent challenge when disagreement would be useful.
4. Claude only when the decision merits scarce high-quality review.
5. ChatGPT integrates, verifies, and decides whether evidence is sufficient.
6. Human approves consequential merge/release decisions.

Do not call every model for every task. Parallelism is justified only when independence or diversity improves confidence.

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
- model metadata source (`api`, `ui`, `self_report`, `config`, `unknown`);
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

### Work
- Route to the lowest-cost capable worker.
- Archive request, response, and metadata immediately.
- Escalate only when the first worker is insufficient.

### Integrate
- ChatGPT/local HumanOS reviewer compares answer to requirements.
- Run local tests/evidence checks.
- Fix only demonstrated issues.

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

Comparisons must preserve task, context, acceptance criteria, temperature/settings when exposed, and commit/data version so results are interpretable.

## Immediate capability priorities

1. Reliable Life Notebook/ledger and recovery.
2. Local model routing + model-run logging.
3. Local retrieval over HumanOS knowledge with provenance.
4. Browser/research workflow with citations and archived sources.
5. Safe file operations and generated-artifact handling.
6. Calendar/email/connectors through explicit permissions.
7. Multi-model benchmarking and naturalization tests.
8. Optional remote/server deployment after local behavior is stable.
