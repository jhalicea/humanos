# HOS-QA-001 — First QA Worker / Agentic Software Company Slice

**Status:** IMPLEMENTED CANDIDATE (not promoted).
**Workspace:** WS-HUMANOS; relation: EXTENDS the existing SDLC/work-contract
framework; related HOS-SWARM-001 is a separate authorized-red-team profile.
**Baseline:** runtime-0.1 @ 0fe4ea5751bb17be30656a5c95809b79d6718636.
**Scope:** qa_agent.py, tests/test_qa_agent.py and this bounded operating model.
**Owner request:** build first AI worker; make the envisioned owner-directed
agentic software company documented and executable.

## Problem and acceptance

There is no scoped QA worker currently proving independent-of-coder evidence
against an exact repository candidate. The HumanOS release stack requires
repeatable QA without granting agents merge or private-data capabilities.

Acceptance:
- valid GitHub repository identity, exact baseline and target, ancestry,
  detached synthetic worktree and canonical local branch unchanged;
- native regression, Codex import smoke, and interruption/recovery smoke;
- each action is a fixed trusted-host command, not selected by a model;
- optional local Ollama advisory receives bounded metadata, not raw logs;
- no model or unsafe model response cannot claim independent approval;
- test failure or missing test fails even if model claims success;
- report is reproducible and contains clear release-authority denial;
- runner tests pass on macOS/Ubuntu Python 3.11/3.13.

## Explicit non-goals

No automatic PR review submission, merge, deployment, provider transcript
reading, source-code modifications, OS sandboxing, git push, arbitrary tool
execution, or credential access. First worker supplies test evidence and
bounded hypotheses, not a penetration-test certification.

## Failure handling / rollback

Reject unverifiable repository/ref, missing scripts, timeouts, and bad model
responses; do not silently convert missing results into PASS. If this candidate
proves unsuitable, close the draft PR; canonical remains unchanged. Preserve
owner-host repo mismatch until separately reconciled.

## Release checkpoints

1. Exact candidate CI on both supported operating systems.
2. Synthetic fixture demonstration with a scripted model (NOT live inference).
3. Owner-host trial with verified optional local Ollama model, if desired.
4. Owner approval to integrate first worker; no automatic change to
   HOS-CONV-001 release gates or PR #135.

## v2 agentic increment — separate unpromoted candidate

Owner specifically requested a genuine QA agent rather than one-shot advisory.
This increment extends v1 in `qa_investigator.py`; the existing deterministic
QA harness stays in `qa_agent.py` and remains the mandatory first gate.

Acceptance:
- model selects a tool, receives actual host observation, chooses a different
  tool, examines targeted tests, and submits findings with valid observation IDs;
- host rejects arbitrary shell, untracked sources, path traversal, unsafe
  test names, invented observations and unsupported probe requests;
- host executes a **declarative model-selected** HOME-alias probe using a
  fixed reviewed implementation, and fails when a synthetic vulnerable
  implementation accepts HOME as a workspace;
- step/time limits, local-model errors and missing conclusions yield
  `INCONCLUSIVE` or `FAIL`, never release approval;
- repository origin/commit/worktree checks and synthetic HOME isolation
  remain in force; no merge or deployment capability;
- exact-head matrix CI plus owner-Mac actual-model trial required.

Non-goals: arbitrary model-authored executable tests, autonomous patches,
generalized sandboxing, public deployment, running production data,
or overriding release gates for Life Notebook PR #137.

## v2.1 completion gate — owner-host acceptance failure correction

Owner-host live Llama run on `9965f36` completed four `read_file` actions
and produced a generic report, but **never ran any independently selected
test or probe**. The CLI correctly printed `NOT YET QUALIFIED` even
though the model-run status was `COMPLETED`. This is a QA workflow defect,
not a Life Notebook code regression.

Bounded acceptance for a real model-directed QA session now requires:
1. Host observes `read_file` or `inspect_diff` against an **actually changed,
   tracked** source path. Merely listing files is not inspection.
2. Host observes at least one independently model-selected `run_test` or
   `run_probe` action, with a real PASS/FAIL/TIMEOUT result. Mandatory
   regression/smoke tests do not satisfy this second requirement.
3. The final report is specific rather than parroting prompt placeholders.
4. The host rejects early/inadequate finals, explains missing evidence,
   rejects duplicate actions and allows bounded further attempts. If the
   step/time budget expires or the model errors, no artificial success.
5. System policy is pinned through rolling tool-observation context.
6. Model output is advisory; the host owns `investigation_coverage`,
   the observed test outcomes, and release authorization.

The v2.1 implementation is a draft. Exact-head GitHub CI and a fresh
owner-host local-model test must pass before qualification. A locally
successful no-merge run is not production acceptance.

## v2.2 owner-host schema failure — bounded repair, not a waived gate

Owner-host live Llama v2.1 at `ec2f5a4d` against Life Notebook
`303a24644e709e076dfe3a19da7fca9de0f22a4b`:
mandatory regression/import/recovery checks all PASS. The local model chose
two source reads, then its third proposal was rejected as `QAError` and
the agent halted in `MODEL_OR_SCHEMA_FAILURE`. No targeted test/probe was
executed. JSON evidence digest (ordinary integrity hash, not signature):
`cee77f2db9ac0a7e96a3ff17047ab98057fc61a735127a9190f4f32ddfb8cc72`.
This does NOT qualify the live model as a QA worker, and does not establish a
Life Notebook regression. The previous v2.1 receipt recorded only the
exception type, not the exact shape of the rejected model output.

v2.2 remedies model-format brittleness *without* broadening tool authority:
- Up to **two** repair turns for malformed JSON or explicitly allowlisted
  proposal-shape issues. Each rejected attempt consumes the existing bounded
  investigation loop and is recorded in evidence. A third failure stops.
- Unauthorized tool names, unsafe paths, unapproved probes and other policy
  violations immediately stop with `POLICY_DENIED`; no model retry can
  turn the unauthorized request into an executed action.
- After each observed action, trusted host guidance identifies the missing
  inspection/test coverage and a bounded list of tracked test filenames.
- Keep the original HumanOS system policy pinned and shrink source excerpts
  for the local model context budget. Do not show model output/raw private
  files in the public receipt.
- **Unchanged completion contract:** inspect a genuinely changed tracked
  source file + independently choose and run a targeted test or approved
  probe + write a specific evidence-linked report. Otherwise no `COMPLETED`
  signoff or release permission.

Qualify exact-head CI and a NEW owner-host live-model run. If the small local
model still cannot satisfy the contract, label it a model capability/format
limitation, choose a capable reviewed local model or improve parsing in a
separate candidate; never weaken permission gates to force PASS.

## v2.3 live-run evidence — investigation passed, reporting still blocked

Owner-host v2.2 exact SHA `01bd89c830ea80be4962dbf108e19afce8d02f69`
against unchanged Life Notebook candidate `303a24644e709e076dfe3a19da7fca9de0f22a4b`:
- Mandatory regression/import/recovery checks: all PASS.
- Local `llama3.2:latest` chose `read_file`, `inspect_diff`,
  `run_test`, `run_probe`, and a second `read_file`.
  Targeted test and security probe both PASS.
- Host `investigation_coverage.complete=true`; however the model first
  submitted a placeholder final, then duplicated `read_file), then sent
  arguments not matching an allowlisted tool schema.
- Host recorded `POLICY_DENIED` and `qa_verdict=INCONCLUSIVE`.
  **No unauthorized command/tool was executed; no final security approval**.
- Owner-provided SHA-256 for local JSON report (not authenticated):
  `582e2a25c183c6e243e9eca7336130e0eff98e6b898b18291fc6e6ac8adf9e03`.

**v2.3 candidate narrow remediation:**
1. When independent coverage is already complete but the model proposes a
   non-substantive final, enter a **host-owned REPORT_ONLY phase**.
   Require a specific, evidence-linked final. Further tool requests are not
   executed and consume the existing finite step budget.
2. A recognized tool with malformed argument *shape* can receive a bounded
   schema correction without executing the request. Before classifying it
   as a format-only mistake, validate any provided security-sensitive path,
   test name, probe identity and expected outcome. Unknown tools, path escapes,
   and unapproved probe behavior still fail closed as `POLICY_DENIED`.
3. Preserve the mandatory QA results, existing observation IDs, original
   immutable target, synthetic-only data policy, owner release authority,
   restricted token/model budgets, and original v2 completion criteria.
4. Add tests for report-only tool refusal, correctable extra argument without
   execution, malicious extra fields with unsafe path/probe, and truthful
   exhaustion if the model never submits an acceptable final.

**Not yet proven:** live Llama behavior at the v2.3 head. Exact-head CI and
subsequent owner-host real-model acceptance are required; scripted fixtures
are not proof of production readiness. Do not merge canonical HumanOS
or touch owner records on this authority alone.

## v2.4 — separating model agency from report authorship

Owner-host v2.3 `a3cd26d` against frozen Life Notebook
`303a24644e709e076dfe3a19da7fca9de0f22a4b`:
mandatory native regression, Codex import, and Codex recovery **PASS**.
Local `llama3.2:latest` autonomously chose `read_file`,
`inspect_diff`, and `run_test` (PASS), satisfying the host's two
investigative coverage requirements. It then submitted repeated
non-substantive final reports and an unknown tool request. The host
recorded `POLICY_DENIED`, no unsafe tool executed, and **NOT QUALIFIED**.
Owner-supplied evidence checksum (unkeyed): `162f31b9d971e009f495dcdd51bcca7cb4862cbaaac78b5cc8b14c8b0bc3dbc2`.

**Architecture correction, not another prompt patch:** A real agent's
autonomy resides in deciding which bounded authorized inspections and tests
to run. A security-relevant QA receipt must be **computed from actual host
observations**, not contingent on a small model producing fluent prose.

The host now performs a finite evidence-to-report handoff immediately
after it observes BOTH (1) changed tracked source inspection and
(2) model-selected targeted test or security probe. Its authoritative
`final` contains only observed filenames, test/probe IDs, statuses, and
known host-mandatory test statuses; confirmed failures receive evidence-ID
references. The model may receive ONE separately labeled `REPORT_ONLY`
advisory opportunity. An invalid/generic/absent model analysis cannot rewrite
the factual receipt or change the test outcome. The report declares
`report_origin=HOST_VERIFIED_OBSERVATIONS` and
`model_advisory.state` explicitly, so it cannot be mistaken for AI-written
analysis or human certification.

**Fail-closed:** an unauthorized *new* tool requested even during the
optional advisory phase is still `POLICY_DENIED` and remains unexecuted.
A model-selected test returning FAIL/TIMEOUT yields QA verdict FAIL.
No observed independent test/inspection, invalid commit/path, no model
during the investigation, or exhausted budget does NOT synthesize a success.
A complete host report does **not** authorize release or certify security.

New scripted tests cover invalid prose, model outage after confirmed
investigation, a prohibited shell request during synthesis, and failures
that must remain FAIL. This finishes a **bounded model-directed QA agent
plus deterministic report**, not a general-purpose autonomous engineer.

**Acceptance:** Exact-head CI matrix plus one owner-Mac real local-model
trial of this code. Do not merge before owner approval. Keep Life Notebook
and owner canonical branches unchanged.
