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
