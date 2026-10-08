# Local Development Workspace Policy

Status: **CANDIDATE v0.2 — HOS-ARCH-001 / OWNER RATIFICATION REQUIRED FOR PERMANENT LAYOUT**  
Original: 2026-10-01; reconciliation: 2026-10-08

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

## Candidate canonical Developer headquarters — actual cleanup naming

**Design decision candidate, not a command to move files:** Preserve the numbered `~/Developer` scheme used during the reported October 2 Mac cleanup. It supersedes the generic illustrative `~/Developer/repos`, `~/Developer/worktrees`, and `~/Developer/artifacts` examples in older proposals. These names are stable **targets** pending host-local verification and owner ratification; no local filesystem mutation is authorized by this document.

```text
~/Developer/                         # SINGLE DEVELOPMENT HEADQUARTERS
  00_Map.md                          # target navigation index: existence NOT verified
  10_Repos/
    humanos/                         # only canonical checkout of public HumanOS
    humanos-academy-private/         # separate private repository
    <other-independent-repo>/        # separate owner; NEVER nest in humanos/
  20_Worktrees/
    humanos/
      <workstream-slug>/             # registered Git worktrees; not independent repos
    <other-product>/
      <workstream-slug>/
  30_Labs/                           # disposable experiments, by owner/project
  40_Artifacts/
    humanos/<workstream>/<run-id>/   # generated reports, test evidence, exports
    <other-product>/<workstream>/<run-id>/
  50_Imports/
    humanos/<intake-id>/             # untrusted inbound files; not automatically canonical
    <other-product>/<intake-id>/
  90_Archive/
    humanos/<date-or-ticket>/        # classified retained legacy material
    <other-product>/<date-or-ticket>/
```

Do not create additional `HumanOS/`, `HumanOS_New/`, `humanos-copy/`, `humanos-final/` or alternate repository roots. The **canonical public code** has one owner checkout: `~/Developer/10_Repos/humanos`. Each approved branch may have an isolated, registered worktree under `20_Worktrees/humanos/`; worktrees are **not duplicate projects**. Filenames that look like older releases are not a basis for deletion.

### Exceptions: one *navigation root* is not one *security/storage boundary*

The Developer headquarters is where human and AI workers discover engineering work. It is **not** a mandate to put every byte in a single directory or disk.

| Kind | Canonical principle | Where to find it from Developer |
|---|---|---|
| Public HumanOS source and project docs | `10_Repos/humanos/`, governed Git repository | Map its exact current checkout in `00_Map.md` |
| Active HumanOS branches/worktrees | `20_Worktrees/humanos/` as registered with Git | `git worktree list --porcelain`; map work order and branch |
| HumanOS private runtime/Notebook, credentials | Outside public Git, access-controlled, encrypted as required; historic `~/.humanos/` location is **not to be moved silently** | `00_Map.md` contains only a safe pointer and classification, not secrets or personal data |
| Human-visible personal documents | Existing approved iCloud Drive/Jon structure for phone access; **not Git and not worktree storage** | Optional safe pointer; avoid automatic iCloud synchronization of repo or live databases |
| Ollama models / UTM / VMs / large managed assets | Managed by their actual host apps; no duplication into 10_Repos or 40_Artifacts | Safe pointers plus owner-approved capacity notes |
| Recovery backups | An independently recoverable copy, ideally on **another device/offsite**, with tested restore and distinct key custody | Recovery manifest pointer; never claim a same-disk recovery packet is a disaster backup |
| BodyFixOS | Independent product checkout, runtime state, permission scope, and release process | Can share Developer *parent*, not HumanOS source, Notebook, or secrets |

`00_Map.md` is a **local read-only navigation aid** (not a second registry or authority ledger): location class, owner/product, verified path, last checked date, source Git remote/worktree identification, and recovery/verification reference. Use relative paths within `~/Developer` and the smallest safe pointer to approved external locations. Never put credentials, full personal transcripts, private identifiers, or public-facing local roots into Git. Do not auto-create this map or mark it verified from a chat-only inspection.

### Evidence of previous Mac cleanup (reported, not host-verified here)

The October 2 conversation history describes a sequence of small approved batches, **not a single all-at-once cleanup**:

- **Batch A:** created the numbered folder structure.
- **Batch B:** reportedly relocated **three canonical repositories and 12 registered HumanOS Git worktrees** under `~/Developer`; **10 stale worktree registrations** were preserved, not silently pruned.
- **Later batches C–G:** organized additional verified human documents and artifacts, including a separate BodyFix navigation index. They do not establish that BodyFixOS and HumanOS share a repository or data authority.
- **Batch H:** reportedly added AI/virtual-machine navigation indexes under `30_Labs`; **18 Ollama models, 4 UTM VMs and 1 VirtualBox VM remained in managed app storage**, not copied into the source tree.
- **Batch I / `00_Map.md`:** a completed authoritative developer-root index is **not evidenced** by the recovered history. Verify whether it exists; if absent, propose it as a separate tiny owner-approved local creation, not a Git-tracked personal path map.
- **V-05 Git staging:** ended with `INSUFFICIENT_EVIDENCE`; do not declare staged data restored or safe to discard without a new inspection.

An external/disaster backup was unavailable at that time. Same-Mac recovery packets mitigate some move mistakes, **not disk loss**. These are prior-session reports, not independent current inspection of the owner's Mac.

**Next step is verification, not a second migration.** Compare the actual current folders, Git worktree registry, ignored files/stashes/unpushed changes, project tests, and application data paths against this proposed map. Do not drag, delete, prune, rewrite history, relocate private databases, or create a new root automatically.

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

## Architecture acceptance checks — candidate

Before certifying the standard, an owner-host audit must confirm: exactly one canonical `humanos` checkout; the intended remotes/HEAD/dirty state; all registered worktrees and any stale registrations without automatic pruning; approved output destinations; external state paths that still function; no private state inside public Git; representative build and Notebook reopen; and restore readiness (marked UNQUALIFIED until a genuine independent backup/restore exists). The numeric folders may already exist, but their *content and correctness* are not proven merely by the folder names.

## Judgment Disclosure

The exact permanent local folder layout is an architectural/operational judgment, not a mechanical fact. This document proposes a layout because the current home-directory sprawl needs explicit destinations, but the final paths require local inventory and owner ratification. The separation invariants are stronger than the illustrative directory names.
