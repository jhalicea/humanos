# HumanOS Codex budget hooks (HOS-MR-001)

Status: CANDIDATE / owner-host acceptance pending. Extends PR #124, not a second router.

Codex lifecycle hooks can deny new user prompts and supported local tool calls.
They cannot cap provider tokens, interrupt in-flight reasoning, or guarantee coverage
of hosted/specialized tools. Hooks are optional, must be trusted, and may fail open
when disabled or unavailable. This is a session/action guardrail, NOT a hard token
or billing ceiling.

Scope is the verified October 2 workspace: canonical checkout at
~/Developer/10_Repos/humanos and registered worktrees under
~/Developer/20_Worktrees/humanos/. Other product folders are untouched.

Boundaries (provisional): four user turns, 24 supported local tool calls and
15 wall-clock minutes per Codex session, first threshold wins. Warning at 80%.
After threshold, supported calls receive REPLAN_REQUIRED. There is no automatic
budget increase. Starting a new session can bypass a previous session's cap.

Installer: scripts/codex_budget_setup.py. Runtime: scripts/codex_budget_hook.py.
The installer merges its commands with existing ~/.codex/hooks.json rather than
replacing unrelated hooks, saves a timestamped backup and copies the hook to
~/.codex/hooks/humanos_budget_hook.py. State is owner-only under
~/.codex/humanos-budget/. It stores hashed identifiers/counters, not messages.
The installer does not change the HumanOS repository or its worktrees.

After local install: restart Codex and trust the new hooks. Verify callbacks
actually execute and confirm fifth prompt or twenty-fifth supported tool call
is denied in an isolated test. Check hooks are not disabled in config.toml.
Do not claim this has been achieved based only on CI or configuration files.

The model-router budget_governor.py in PR #63 is a separate, tested candidate
that still needs a trusted provider dispatcher to impose a hard token ceiling.


## 2026-10-08 v2 repair — preserve budget, not disable hooks

The hard **per-session** thresholds remain **4 prompts, 24 supported local tool
calls and 15 elapsed minutes**, warning at 80%; there is no automatic budget
renewal, retry, reasoning-effort escalation or extra reviewer. Reaching a limit
produces STOP -> REPLAN_REQUIRED and instructs evidence preservation.
These are intentional conservative *action/session* limits, not token counts.

Additional safeguards on supported hook events:

- Parse the actual user Codex config and require primary and planning effort LOW,
  default spawned effort LOW, Luna as default spawned model, and one concurrent
  spawned worker. Any drift blocks the next supported action.
- Scan user custom agents (including astra.toml, sol.toml, terra.toml) and
  block if any explicitly use MEDIUM/HIGH instead of LOW.
- If the event payload explicitly reports a contradictory effective effort,
  block it. The currently documented hook payload **does not** guarantee
  that field, so settings checks cannot detect CLI/session effort overrides.
- Enforce existing per-session caps with persistent hashed identifiers and
  owner-private state; source prompts/outputs and API keys are not persisted.
- Upgrade the owner's known installed commit
  `20d601e29c3d74e92daba24d7310d8e401d9aded` only when the existing hook
  exactly matches its reviewed source. Make a backup, atomically replace the
  hook source, merge existing hook registrations without deleting other hooks,
  and reject modified/unknown copies rather than overwriting.

**Activation still requires Codex hook trust** after an update. GitHub Actions
can validate the algorithm, not prove that a user's Desktop has trusted and
executed it. Work cloud orchestration and ordinary ChatGPT do not run this
user-installed local Codex hook. Supported hooks do not intercept already
running model reasoning and cannot enforce a precise hosted-model token limit.

For an owner-Mac acceptance check: verify the installed file, inspect `/hooks`
in Codex, explicitly trust/review the updated definition, start a new session
in the verified canonical HumanOS checkout, and confirm owner-private
`~/.codex/humanos-budget/state.json` changed from an accepted bounded hook
event. Use a tiny non-billable project action and inspect only counter metadata;
never upload local prompts, private transcripts or raw state to GitHub.
Do not use paid API inference to validate hook trust.
