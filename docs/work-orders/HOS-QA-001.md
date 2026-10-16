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
