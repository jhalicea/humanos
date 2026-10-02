# Local Development Workspace Policy

Status: **CANDIDATE — HOS-ARCH-001 / OWNER RATIFICATION REQUIRED FOR PERMANENT LAYOUT**  
Date: 2026-10-01

This policy prevents HumanOS development artifacts from spreading across a developer's home directory and prevents independent products from being accidentally coupled by filesystem layout.

It is a target policy. Applying it to an existing machine requires a read-only inventory, a verified backup/snapshot, and explicit approval before consequential moves or deletion.

## Principles

1. One canonical checkout per product repository.
2. Independent products have independent repositories and top-level project folders.
3. Git worktrees live in one designated worktree area, not beside personal documents.
4. Private HumanOS runtime state remains outside the public repository.
5. Generated evidence, exports and temporary files have designated locations.
6. Backups are distinguishable from live repositories and worktrees.
7. `~/Documents`, `~/Desktop`, and the home-directory root are not default build/artifact destinations.
8. Development repositories should not live in iCloud-synchronized Desktop/Documents locations.
9. Nothing is deleted merely because a filename looks old; classify and verify first.
10. Unknown destination means stop, not “write to the current directory.”

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

Exact paths may differ after local inventory and owner ratification. The invariant is separation by purpose and product.

BodyFixOS private operational state uses its own separately defined application-data location and must not be stored under `~/.humanos/`.

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

`UNKNOWN` blocks deletion and automatic relocation.

## Phase 0 — backup and freeze destructive action

Before moving repositories, worktrees, private state, or source-of-truth documents:

1. confirm a current full-machine or equivalent recoverable backup exists;
2. take a separate snapshot/backup of `~/.humanos` private runtime state;
3. preserve any BodyFixOS private-state/document root separately from HumanOS;
4. record checksums for irreplaceable loose files before moving them;
5. perform no deletion, history rewrite, worktree removal, or destructive cleanup during inventory.

A backup is not considered verified merely because a backup folder exists; record enough evidence to know it is readable/restorable.

## Phase 1 — read-only repository and worktree inventory

For every repository-looking directory, capture:

- absolute path;
- canonical repository or linked Git worktree status;
- remote URL(s);
- branch and exact `HEAD` commit;
- `git status --porcelain`;
- untracked files;
- `git stash list`;
- commits not present on the configured upstream branch;
- `git worktree list --porcelain` from the owning repository;
- ignored files that may contain important local state, using targeted inspection such as `git status --ignored` or `git check-ignore` rather than indiscriminately publishing paths;
- `.env`/secret-bearing local configuration presence without copying secrets into reports;
- local databases or private runtime state;
- virtual environments and generated caches;
- repository size and last-modified evidence as useful;
- classification and proposed destination;
- confidence and verification required.

Do not move a repository or worktree merely because it appears duplicated.

## Phase 2 — loose files, documents, artifacts and manuals

For files outside canonical repositories:

1. record path/name, size, modified time and type;
2. calculate a checksum for files that may be preserved/moved;
3. identify whether the item is referenced by a work order, migration, backup or audit record;
4. identify source-of-truth versus generated copy/export where possible;
5. classify it;
6. propose a destination or dated quarantine/archive location.

Private BodyFixOS manuals and operational documents are not automatically repository-safe. Client records, private operational data, credentials, protected information, or sensitive clinic material must remain outside public Git repositories.

## Phase 3 — proposed mapping

For every item, record:

`current location → classification → proposed location → reason → confidence → verification needed → authority required`

No “miscellaneous” destination is permitted as a permanent solution.

## Phase 4 — safe move rules

Move only items with high-confidence classification and an approved destination.

### Git worktrees

Use Git-aware movement rather than Finder drag-and-drop when a path is a registered worktree:

```text
git worktree move <old-path> <new-path>
git worktree repair
```

Then verify `git worktree list --porcelain`, branch, `HEAD`, and dirty state.

### Canonical repositories

After moving a canonical checkout, verify:

- remote(s);
- branch/upstream;
- `HEAD`;
- dirty state;
- project-specific build/test commands;
- scripts/configuration that contain absolute paths.

### Python virtual environments

Python virtual environments may contain absolute paths and should normally be recreated after a repository/worktree move rather than trusted in place. Preserve dependency metadata, not the environment directory as canonical source.

### Unknown / legacy material

Unknown or legacy-candidate material moves only to a dated quarantine/archive location. It does not go to Trash during the cleanup project.

## Phase 5 — verification

After approved moves:

- repository remotes/branches still resolve;
- worktrees are correctly registered and repaired;
- unpushed commits/stashes remain present;
- ignored private files are still available where required and were not accidentally committed;
- tests/builds run from canonical checkouts;
- HumanOS private runtime state resolves correctly;
- BodyFixOS private state remains independent from HumanOS;
- no secrets/private data were introduced into Git;
- backups remain readable/restorable;
- scripts/docs no longer point at stale paths;
- virtual environments are recreated as required;
- generated artifacts now land only in approved output roots.

## Phase 6 — archive/delete

Only after an agreed retention period, successful verification, and explicit owner approval may quarantined duplicates/temp artifacts be deleted.

Deletion is a separate decision from organization.

## File-output rule for future automated work

Automated tools and agents must never choose the home-directory root, `~/Documents`, or `~/Desktop` as an implicit output directory.

Every generated file must have an explicit destination class:

- repository source/doc → canonical repository/worktree;
- private runtime state → designated application-private state;
- evidence → project artifact directory;
- import/migration → project import directory;
- temporary → system/project temporary directory;
- backup → backup/archive directory;
- user-facing document → explicitly selected user document location.

### Output allowlist

This rule should be enforced in tool wrappers where practical, not only documented. A writer/executor should receive an allowlist of approved output roots. A proposed path outside those roots fails closed or requires explicit human approval.

Until that enforcement exists, this rule is **DOCUMENTED, NOT ENFORCED**.

## Cross-product rule

HumanOS and BodyFixOS may share engineering ideas, but not filesystem ownership. One project's repositories, worktrees, artifacts, private data, backups and generated files must not be stored inside the other project's repository or private runtime-state directory.

A future connector does not change this ownership rule.

## Judgment Disclosure

The exact permanent local folder layout is an architectural/operational judgment, not a mechanical fact. This document proposes a layout because the current home-directory sprawl needs explicit destinations, but the final paths require local inventory and owner ratification. The separation invariants are stronger than the illustrative directory names.
