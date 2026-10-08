# Codex LOW reasoning defaults — Mac installation (candidate)

This is the Codex configuration that applies to local Codex Desktop/CLI clients;
it is not the internal HumanOS ModelRouter and not ChatGPT Work.

In the HumanOS repository, `.codex/config.toml` sets project defaults (loaded
when the project is trusted). The script `scripts/codex_low_setup.py` applies
matching **user-level** defaults to `~/.codex/config.toml`, retaining unrelated
settings and making a backup of a previous file. No model is called by the script.

### Usage

From an updated checkout containing this candidate:

```sh
python3 scripts/codex_low_setup.py --dry-run
python3 scripts/codex_low_setup.py
```

Python 3.11 or later is required for the standard-library `tomllib` validator.
The script is idempotent and uses an atomic replace. Review any reported custom
agent overrides and restart/reopen Codex for **new** sessions.

### Effective defaults

- root and planning: `low`;
- spawned-agent reasoning: `low`;
- spawned-agent model if not explicitly chosen: `gpt-6-luna`;
- up to one concurrent spawned agent per Codex session (excluding the primary).

Codex's documented config precedence means CLI `--config` flags, explicit
session settings, project-local values, and explicit subagent spawn settings can
override defaults. A custom `.codex/agents/*.toml` file may also override
effort. Existing in-flight threads are not guaranteed to change.

### Budget limits: not yet hard-enforced in Codex Desktop

No documented `config.toml` token-usage cap is installed here. Project
`AGENTS.md` adds an advisory STOP/REPLAN policy, but does not interrupt an
already-expensive live model request. The Python governor in draft PR #63 is
not wired to Codex Desktop. Do not claim that this script implements a hard
token budget or owner-approval broker. Hard enforcement would require a
supported trusted dispatch boundary and provider usage accounting.

### Backout

Restore the script-created `config.toml.backup-<UTC timestamp>` to
`~/.codex/config.toml` if you want to revert the user-level change. Removing
the repo's project config reverts only that project's defaults. Neither action
alters model billing or usage already incurred.
