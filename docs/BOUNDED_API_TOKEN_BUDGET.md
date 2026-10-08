# HumanOS HOS-MR-001 — Provider-Capped Token Budget (API-only)

**Status: IMPLEMENTED CANDIDATE.** Not merged, not deployed on the owner's Mac,
no live API acceptance yet. This extends the existing Model Router and imports
`budget_governor.py`; it does not create a second router.

## Boundary and what is precisely enforced

For **one text-only OpenAI Responses API request dispatched through this module**:

1. The input-token endpoint counts `model + input + instructions` before dispatch.
2. The durable task ledger reserves **that input count plus the complete generated
   output cap**. `max_output_tokens` is enforced by the Responses API and
   includes hidden reasoning tokens; `reasoning.effort` is always `low`.
3. If context, total reserved tokens, output cap, call count, or authorization
   fails, the model request is **not sent**.
4. The reservation is atomically saved before the paid request. On crash,
   timeout, missing metering, or uncertain response, no silent retry occurs.
5. After a response, validate actual input/output/total-token usage, preserve
   conservative reservations (do not credit back unused tokens) and record a
   privacy-minimized evidence entry.

Input counting is for identical **text content and instructions**; model usage
metadata is checked against the input bound after the call. Unknown accounting
fails closed. Output is capped by the provider; the program cannot restrict
model calls made through unrelated clients, ChatGPT plan, or Codex Desktop.

## Limits of the promise

- **Cannot enforce a hard token limit for existing Codex Desktop sessions.**
  Sign in with ChatGPT / Codex plan mode does not support `max_output_tokens`.
  Existing LOW effort defaults and hooks are useful guardrails only.
- **Separate API billing applies** to this execution path. The command requires
  `--authorize-api-charges` and an independently configured `OPENAI_API_KEY`.
  This branch does not create, capture, upload, or persist credentials.
- Token limit is **not an exact USD ceiling**. Models have different rates;
  cached tokens, rate changes, or other billable activities need separate
  pricing logic. This text-only path disables model tools and backgrounds.
  For account-level defense, apply a project hard spend limit in OpenAI's API
  settings; hard spend limits may slightly exceed during enforcement lag.
- No automatic replan/restart, hidden additional workers, model upgrade,
  output streaming, tool use, or multi-turn context replay.
- Task quotas are **provisional**; the caller must define immutable bounds.
- This is an owner-controlled software boundary, not a defense against an
  owner/agent intentionally bypassing the runner and directly calling APIs.

## Canonical locations

Code: PR #63 on `feature/model-router-v1`.

- `bounded_responses.py` — existing BudgetGovernor-connected transport.
- `scripts/bounded_api_run.py` — deliberately opt-in CLI.
- `tests/test_bounded_responses.py` — offline provider mocks and negative tests.
- `~/.humanos/private/.../<task>.json` — **explicit owner-private** budget
  checkpoint, no prompt text or API keys saved; no public Git files.

The owner's verified public checkout remains
`/Users/jhalicea/Developer/10_Repos/humanos`. Its current local branch is
`local-kernel-ledger-v2`; do not switch, reset, or overwrite that branch.
An isolated candidate lab may use
`/Users/jhalicea/Developer/30_Labs/humanos-bounded-api/` following the
HumanOS October 2 numbered workspace scheme.

## Local offline acceptance before API authorization

Retrieve these three files at an immutable reviewed candidate commit into an
isolated 30_Labs workspace: `budget_governor.py`, `bounded_responses.py`,
`scripts/bounded_api_run.py`. Copy focused test(s) if running locally.
The CLI requires a bounded prompt file and an **absolute private ledger path**.
Example (never sends an API request):

```sh
python3 scripts/bounded_api_run.py --model gpt-6-luna \\
  --prompt-file /Users/jhalicea/Developer/30_Labs/humanos-bounded-api/prompt.txt \\
  --ledger /Users/jhalicea/.humanos/private/model-budgets/demo-v1.json \\
  --budget-total 16000 --context-cap 8000 --calls-cap 4 \\
  --output-cap 2000 --dry-run
```

Only a separate **explicit run** with `--authorize-api-charges` and the
`OPENAI_API_KEY` environment set sends API requests. Never paste the key
into a chat or Git repository. Check API account/project budgets first.

## SDLC acceptance

Run full regression matrix and focused offline negative tests at exact SHA,
verify JSON ledger owner-only permissions and no prompt persistence, then
owner-Mac dry run, one explicitly approved minimal live Responses API call,
and verify input count, actual usage, provider low effort/output cap, response
status, crash recovery, and no unauthorized additional API dispatch.

**Do not promote** until the owner reviews evidence and approves integration
with a trusted HumanOS execution policy broker. Hosted Codex/ChatGPT remains
out of the enforced scope even after this approval.
