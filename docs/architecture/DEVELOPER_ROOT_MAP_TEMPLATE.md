# Developer Headquarters — Local Navigation Map (Template)

Status: **TEMPLATE ONLY / NOT INSTALLED ON OWNER MAC**  
Authority: Local navigation aid under [HOS-ARCH-001 workspace policy](LOCAL_DEVELOPMENT_WORKSPACE_POLICY.md). It is **not** a new canonical registry, project ledger, Notebook, or security policy.

Copy and complete locally as `~/Developer/00_Map.md` **only after confirming the chosen folder locations with the owner**. Never commit the completed local map if it contains private paths, identities or metadata. This public template carries no current-Mac proof.

## How to use this map

Start from `~/Developer` when you need software work. Look for the project under `10_Repos`, active work under `20_Worktrees`, and evidence under `40_Artifacts`. The only authoritative source for what a branch contains is its actual Git/work-order evidence, not this file. This map is a human-friendly doorway.

| Location | Purpose | Current verification |
|---|---|---|
| `10_Repos/humanos/` | **Candidate** canonical public HumanOS checkout | UNVERIFIED until Git remote, HEAD, branch, and owner intent checked |
| `10_Repos/humanos-academy-private/` | Separate private Academy repository, when present | UNVERIFIED |
| `10_Repos/<separate-product>/` | Independent projects, never nested under HumanOS | UNVERIFIED |
| `20_Worktrees/humanos/` | Registered feature worktrees belonging to HumanOS | UNVERIFIED until `git worktree list --porcelain` checked |
| `30_Labs/` | Deliberately disposable experiments and app-managed asset pointers | UNVERIFIED |
| `40_Artifacts/humanos/` | Reports, test evidence and workstream-specific outputs | UNVERIFIED |
| `50_Imports/humanos/` | Untrusted inbound data awaiting approved intake | UNVERIFIED |
| `90_Archive/` | Retained history; **not an independent disaster backup** | UNVERIFIED |

## Governed external locations (pointers, not migrations)

- **HumanOS private runtime / Notebook:** preserve existing approved location outside public Git (historically `~/.humanos/`). Check application config and owner authorization before using or changing any path.
- **Human-readable personal documents:** use the separately approved document/phone-sync area; do not move app databases or live Git trees into iCloud Documents.
- **Managed AI models and VMs:** use Ollama/UTM/VM application directories in place; don't clone assets into `10_Repos`.
- **BodyFixOS:** independent product with its own repository and private app state. Only the shared Developer *parent* is organizational.
- **Backups:** independently restorable external/offsite backup and keys must be tested before claiming disaster recovery; an archive or same-disk copy is not equivalent.

## Checkpoint (fill locally, never invent evidence)

| Check | Status | Evidence reference | Last checked |
|---|---|---|---|
| Expected `~/Developer` folders exist | UNVERIFIED | — | — |
| Exactly one intended HumanOS canonical checkout | UNVERIFIED | Safe local Git verification | — |
| HumanOS registered worktrees match actual folders | UNVERIFIED | Local `git worktree list --porcelain` readback | — |
| Dirty, ignored, stashed and unpushed changes preserved | UNVERIFIED | Private inventory record | — |
| Previous V-05 discrepancy investigated | UNVERIFIED | Private recovery reference | — |
| Stale worktree registrations dispositioned | UNVERIFIED | Approved local worktree evidence | — |
| Private Notebook/data location still operates | UNVERIFIED | Owner-local readback; no private bytes here | — |
| Independent backup and sample restore verified | UNVERIFIED | Private recovery receipt | — |
| Full project tests run from canonical checkout | UNVERIFIED | Commit-specific CI + owner-host result | — |

## Safe local verification examples

In Terminal on the owner Mac, **after confirming the directories exist**:

```bash
cd ~/Developer/10_Repos/humanos
git rev-parse --show-toplevel
git remote -v
git status --short --branch
git worktree list --porcelain
```

Those commands **inspect** Git; they do not move or delete files. Output may include private paths/metadata. Do not paste it into a public issue or PR without sanitizing it.

For a bounded Developer-only inventory, once the draft script has been approved and installed in the local checkout:

```bash
python3 scripts/audit_local_workspace.py \
  --developer-root "$HOME/Developer" \
  --output-dir "$HOME/Developer/40_Artifacts/humanos/workspace-audit"
```

Its reports are local and may contain private metadata. **Never commit those raw outputs**. The script creates reports only; it does not repair repositories or prove a backup exists.

## Ownership and freshness

This map is maintained only when a real location changes and the owner verifies it. Project/workstream scope and status belong in the existing Context Registry, work orders and Issue #67; policy and authority are governed elsewhere. If a path is stale, mark it `UNKNOWN` and inspect—do **not** infer, create a replacement HumanOS repo or move files autonomously.
