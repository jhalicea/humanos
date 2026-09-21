# HumanOS Developer Environment v0.1 — SDLC Checkpoint

Status: SPECIFIED / IMPLEMENTATION PENDING
Owner: Jon Alicea
Date: 2026-09-16

## Problem

HumanOS development currently depends on ad hoc workstation state. The repository does not yet define one canonical development environment, one supported editor workflow, or a reproducible setup/verification path. This creates avoidable drift between local machines, CI, documentation, and future contributors.

## Owner direction

The HumanOS development environment will be documented and implemented in its own focused branch and pull request rather than being mixed into Model Router v1 or another feature branch.

The current canonical direction is:

- VS Code is the canonical HumanOS development IDE.
- Zed is a supported secondary editor for fast reading, focused edits, and experimentation.
- The repository must remain editor-independent; all required build, test, verification, and recovery operations must be possible from the CLI.
- Official CPython is the initial Python distribution standard.
- Python's built-in `venv` is the initial environment-isolation standard.
- Python 3.13 is the canonical local development target; CI compatibility remains authoritative for supported test targets.
- Git + GitHub remain the source-control and review system.
- Local AI execution remains the default development path. Ollama is currently an adapter/runtime, not a permanent HumanOS dependency.
- Cloud AI/provider access is outside this increment and requires separate privacy/provider policy and SDLC work.

## Scope

This increment may add or update:

- canonical developer-environment documentation;
- documented VS Code role and minimum recommended extension set;
- documented Zed secondary-editor role;
- supported/canonical Python version guidance;
- environment creation and activation guidance;
- a future bounded bootstrap/verification script if separately implemented and tested within this branch;
- documentation links and corrections needed to remove environment/version drift.

## Non-goals

This increment does not:

- change HumanOS runtime authority or permission boundaries;
- alter Model Router v1 behavior;
- introduce cloud-model credentials or provider accounts;
- make VS Code, Zed, Ollama, Homebrew, `uv`, `pyenv`, Poetry, Conda, or any other developer tool a runtime dependency of HumanOS;
- install software on the owner's machine through repository code;
- move personal Notebook content, credentials, or private local paths into Git;
- claim that future bootstrap automation is implemented until it exists and is tested.

## Foundation constraints

- HumanOS remains provider-neutral and local-first.
- Development tooling must not become an authority source.
- Human ownership and explicit approval remain above models, editors, extensions, and automation.
- Dependencies should be minimized and justified.
- Setup must be inspectable, reproducible, reversible, and truthful about what is installed or configured.
- Repository documentation must distinguish current verified behavior from planned tooling.

## Observable acceptance criteria

1. The repository names one canonical IDE and explains why it is canonical.
2. The repository documents Zed as supported but secondary rather than treating editor choice as a runtime requirement.
3. Required HumanOS development operations remain possible from the CLI without either editor.
4. The canonical Python development target is documented and does not silently replace Apple's system Python.
5. Environment-isolation guidance uses an explicit project/developer environment rather than system-site packages.
6. Developer documentation does not require a cloud-model account.
7. Ollama is described as a current local adapter/runtime rather than a permanent HumanOS dependency.
8. Existing documentation that conflicts with the tested Python matrix is corrected or explicitly scoped.
9. Any added setup or verification script has deterministic checks, failure behavior, and tests before being described as working.
10. The focused diff is reviewed for supply-chain expansion, privacy leakage, accidental local paths, authority changes, and misleading status language.
11. Repository-wide tests are run if executable repository behavior is changed; docs-only commits do not claim runtime verification.
12. Owner approval is required before merge.

## Rollback

This work is isolated on `feature/developer-environment-v0.1`, based on `runtime-0.1`. Closing the pull request leaves the runtime unchanged. Documentation-only commits do not mutate local workstation configuration.

## Review gate

Before merge:

- inspect the final diff against this scope;
- verify all tooling claims against actual repository behavior or official tool documentation;
- record any new dependency or supply-chain decision explicitly;
- run relevant tests if executable files are added or changed;
- obtain owner approval for merge/release.
