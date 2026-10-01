# Local Development Workspace Policy

Status: **CANDIDATE — HOS-ARCH-001**  
Date: 2026-10-01

This policy prevents HumanOS development artifacts from spreading across a developer's home directory and prevents independent products from being accidentally coupled by filesystem layout.

It is a target policy. Applying it to an existing machine requires a read-only inventory and explicit approval before moves/deletions.

## Principles

1. One canonical checkout per product repository.
2. Independent products have independent repositories and top-level project folders.
3. Git worktrees live in one designated worktree area, not beside personal documents.
4. Private HumanOS runtime state remains outside the public repository.
5. Generated evidence, exports and temporary files have designated locations.
6. Backups are distinguishable from live repositories and worktrees.
7. `~/Documents` and the home-directory root are not default build/artifact destinations.
8. Nothing is deleted merely because a filename looks old; classify and verify first.

## Proposed developer layout

```text
~/Developer/
  repos/
    humanos/
    humanos-academy-private/
    career-ops-private/
    bodyfixos/                 # independent product, not inside HumanOS
  worktrees/
    humanos/
      <workstream>/
    bodyfixos/
      <workstream>/
  artifacts/
    humanos/
    bodyfixos/
  imports/
    humanos/
    bodyfixos/

~/.humanos/
  private/
    ...                        # HumanOS private runtime state; never BodyFixOS data

~/Archives/
  humanos/
  bodyfixos/
  other-projects/
```

Exact paths may differ if the owner prefers another top-level root. The invariant is separation by purpose and product.

BodyFixOS private operational state should use its own separately defined application-data location and must not be stored under `~/.humanos/`.

## Canonical classification for every existing item

Before cleanup, classify each item as exactly one of:

- `CANONICAL_REPO`
- `ACTIVE_WORKTREE`
- `PRIVATE_RUNTIME_STATE`
- `SOURCE_OF_TRUTH_DOCUMENT`
- `GENERATED_EVIDENCE_ARTIFACT`
- `IMPORT_MIGRATION`
- `BACKUP_ARCHIVE`
- `TEMP_CACHE`
- `LEGACY_CANDIDATE`
- `UNKNOWN`

`UNKNOWN` blocks deletion.

## Read-only inventory procedure

For each repository-looking folder:

1. determine whether it is a Git repository or worktree;
2. capture remote URL;
3. capture current branch/HEAD;
4. capture `git status --porcelain`;
5. capture worktree relationships with `git worktree list --porcelain` from the owning repository;
6. identify untracked files;
7. identify whether the folder contains private state that must not be pushed;
8. classify the folder before proposing a destination.

For loose files/artifact folders:

1. record path/name, size, modified time and type;
2. calculate a checksum for files that may be preserved/moved;
3. identify whether the item is referenced by a work order, migration, backup or audit record;
4. classify it;
5. propose destination or quarantine.

## Cleanup phases

### Phase 0 — Freeze destructive action
No deletes, repository moves, worktree removals or history rewrites.

### Phase 1 — Inventory
Generate a complete machine-local manifest and Git/worktree map.

### Phase 2 — Proposed mapping
For every item, record:

`current location → classification → proposed location → reason → verification needed`

### Phase 3 — Quarantine/move
Move only approved items. Legacy/unknown material goes to a dated quarantine/archive area instead of Trash.

### Phase 4 — Verification
After approved moves:

- repository remotes/branches still resolve;
- worktrees are correctly registered or intentionally recreated;
- tests/builds run from canonical checkouts;
- HumanOS private runtime state resolves correctly;
- no secrets/private data were introduced into Git;
- backups remain restorable/readable;
- scripts/docs no longer point at stale paths.

### Phase 5 — Archive/delete
Only after an agreed retention period and successful verification may quarantined duplicates/temp artifacts be deleted.

## File-output rule for future automated work

Automated tools/agents must never choose the home-directory root or `~/Documents` root as an implicit output directory.

Every generated file must have an explicit destination class:

- repo source/doc → canonical repo/worktree;
- test/runtime private state → designated app-private state;
- evidence → project artifact directory;
- temporary → system/project temp directory;
- backup → backup/archive directory;
- user-facing document → explicitly selected user document location.

If destination is ambiguous, stop and ask rather than dropping the artifact into the current directory.

## Cross-product rule

HumanOS and BodyFixOS may share engineering ideas, but not filesystem ownership. One project's worktrees, artifacts, private data, backups and generated files must not be stored inside the other project's repository or private runtime-state directory.
