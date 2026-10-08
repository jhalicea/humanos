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
