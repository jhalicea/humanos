# HOS-ARCH-001 — HumanOS Project-State Reconciliation

Date: **2026-10-07**  
Status: **CANDIDATE / REVIEW REQUIRED**  
Source baseline: `runtime-0.1` at `0fe4ea5751bb17be30656a5c95809b79d6718636`  
Change type: public-safe project metadata and documentation only.

**Runtime-consumed data caveat:** `context_registry.public.json` is consumed by the deterministic Context Router. Adding workstream records can change which existing workstream a new request matches, even though no Python source, permission broker, Notebook schema, or model adapter is edited. Registry validation and topic-routing regression checks remain mandatory.

## Intent

This is an **as-observed evidence map**, not a new Foundation, runtime, Notebook, work router, or independent governing document. A user can find what was built, approved, tested and still blocked without pretending that chat memory or a mutable status note is source-of-truth. Neither these sources nor this audit provide direct enumeration of every ChatGPT Project conversation.

## Existing sources and roles

| Source | Proper responsibility |
|---|---|
| Human owner / verified owner decisions | Ratification, consent, approved changes within specific scope |
| Ratified Constitution and Foundation instruments | Governing requirements in their valid scope; conflicts require explicit human disposition |
| Life Notebook, outside public Git | Original chronological messages and verified capture/checkpoint receipts |
| Code and immutable commits | Implementation/version evidence, not proof of an owner deployment |
| CI and local runtime readback | Tested behavior on identified software and environment; not unlimited capability claims |
| [Context Registry](../../config/context_registry.public.json) | Workstream identity, discovery, status, relationships and next action |
| [Work orders](../work-orders/) | Bounded acceptance contract and candidate evidence |
| [Issue #67](https://github.com/jhalicea/humanos/issues/67) | Mutable navigation pointer only |
| Root [STATUS.md](../../STATUS.md) | Dated baseline/branch snapshot, never an auto-updating universal dashboard |

## Resolved documentation drift in this candidate

| Drift | Evidence and correction |
|---|---|
| Stale root status asserted HOS-LN-002 not promoted | [PR #122](https://github.com/jhalicea/humanos/pull/122) merged to `runtime-0.1` October 2; status now says promoted **bounded explicit-preference memory**, not full LN-1 |
| Workstream registry omitted four active/recent efforts | Add **HOS-ARCH-001**, **HOS-LN-001**, **HOS-LN-002**, **HOS-MCP-001** using existing schema, not a parallel system |
| GitHub Foundation register only emphasized September 11 | Add public-safe pointer to **September 29** owner-recorded Foundation Standard v1.0 ratification; preserve differing scope and unresolved constitutional compatibility |
| Roadmap grouped BodyFixOS with HumanOS applications | Clarify **BodyFixOS is a separate product**, connectable only through an authorized narrow versioned interface |
| Roadmap implied only one workstream can exist | Clarify existing policy: concurrent separate workstreams are allowed, one focused execution slice within the selected workstream/session |

## What is actually known now

| Area | State | Critical limit |
|---|---|---|
| Context Registry/Context Engine | Promoted deterministic workstream routing and graph substrate | Private whole-human graph population and full semantics remain separate work |
| Life Notebook HOS-LN-002 | Promoted Oct 2, bounded tested preference-memory path | Universal external-chat capture, LN-1 hardening, and production qualification not proved |
| PRE-LN-1 HOS-LN-001 | [PR #117](https://github.com/jhalicea/humanos/pull/117) draft design | ADR owner acceptance and LN-1 implementation pending; PR targets another branch |
| Architecture HOS-ARCH-001 | [PR #120](https://github.com/jhalicea/humanos/pull/120) baseline merged | [PR #121](https://github.com/jhalicea/humanos/pull/121) independent-review/governance proposal still unratified |
| Control Room HOS-MCP-001 | [PR #87](https://github.com/jhalicea/humanos/pull/87) draft with automated test evidence | R3 review, owner-host pairing, and promotion gates outstanding |
| Academy | Generic kernel and public material promoted | Full private curriculum experiences and learner workflow still need owner-environment evidence |

## Candidate branch-only source provenance (checked 2026-10-10)

The new Context Registry entries preserve a `branch` alongside a `work_order` path. A work-order path may exist **only at that branch ref**; do not treat a registry pointer as proof that the file is present on canonical `runtime-0.1`.

- **HOS-LN-001:** `docs/work-orders/HOS-LN-001.md` was readable on `life-notebook-ln1-schema-integrity` (draft [PR #117](https://github.com/jhalicea/humanos/pull/117)); that path was **not** present on the inspected canonical branch or this reconciliation candidate. Its base is `life-notebook-ln0`; no LN-1 promotion is inferred.
- **HOS-MCP-001:** `docs/work-orders/HOS-MCP-001.md` was readable on `feature/control-room-mcp-v1` (draft [PR #87](https://github.com/jhalicea/humanos/pull/87)); that path was **not** present on the inspected canonical branch. MCP remains a candidate, independently gated and subject to registry reconciliation.
- **HOS-ARCH-001:** The registry points at `architecture/independent-review-reconciliation-v1` (draft [PR #121](https://github.com/jhalicea/humanos/pull/121)). This **separate** public-safe status reconciliation is draft [PR #123](https://github.com/jhalicea/humanos/pull/123), `architecture/hos-arch-001-project-reconciliation-v1`. The existing architecture baseline/work order was introduced separately through merged [PR #120](https://github.com/jhalicea/humanos/pull/120); neither draft supersedes the other by default.
- **HOS-LN-002:** `docs/work-orders/HOS-LN-002.md` is already on canonical, but its candidate-era heading required the dated correction included in PR #123. Historical pre-promotion acceptance detail is preserved.

Before routing a continuation to a candidate, resolve **workstream ID → declared branch → work-order file at that exact ref → current PR/commit state**. Missing-at-canonical is not missing-everywhere, and a draft work order is not promoted authority.

## October 11 routing-risk reconciliation (candidate)

The public Context Registry is a behavior-bearing input, not only a list of links. A read-only translation of the current deterministic token scoring showed that **adding new broad topic labels** could redirect existing requests: for example, `continue external ChatGPT capture` matched new `HOS-MCP-001` over existing `HOS-NB-CAPTURE-001`; `continue life notebook restart and recall` matched new `HOS-LN-002` instead of existing `HOS-NB-RECALL-001`; a Foundation/Constitution question became ambiguous.

**Bounded correction on this draft branch:** Narrow topics *only on the four newly introduced workstream records*. Remove the generic `foundation` topic from HOS-ARCH-001, `life notebook` from HOS-LN-001 and HOS-LN-002, and `chatgpt`/`external interface` from HOS-MCP-001. Keep their specific architecture, schema, memory, and MCP/Control Room terms, as well as all original 25 workstream records/metadata unchanged. No status, branch, relation or permission changes are intended.

**Behavior acceptance:** New tests in existing `tests/test_context_registry.py` pin the historical external conversation-capture, Notebook recall, generic Notebook and Foundation request routes, and verify that specific architecture/PRE-LN-1/semantic-memory/MCP queries still resolve to the newly added workstreams. The initial comparison was an independent JS translation, **not native Python execution**. Fresh repository CI, native validator/route smoke checks, independent reviewer analysis and owner approval remain separate gates. This change supersedes the older seven-file candidate and its earlier exact-commit review evidence; do not promote without qualifying the final eight-file SHA.

## Open authority and continuity gaps — do not silently resolve

1. **Constitution/Foundation:** The August 2 Constitution v0.2 requires a recorded amendment process. The September 29 owner-recorded ratification changes its declared operating role. A final authoritative Foundation v1.0 artifact/hash binding has not been verified. Preserve both decisions and do not adjust permissions merely because this note was written.
2. **Notebook checkpoint lag:** The accessible Drive Active Index and capture runtime state were last observed modified September 29, while significant GitHub state changed October 1–2. The later facts are **not recorded as verified Drive Notebook checkpoints** by this audit. Report `CHECKPOINT LAG` until capture/checkpoint readback.
3. **ChatGPT host integration:** Neither ChatGPT Project presence nor a project instruction proves automatic whole-conversation capture or global interception. Every captured section needs completeness/idempotency/readback evidence.
4. **Historical Git privacy:** Pull-request references and remote history exposure must be independently verified; no clean-history assertion is made.
5. **PR overlap and actual loss-of-record risk:** Draft Control Room [PR #87](https://github.com/jhalicea/humanos/pull/87) changes `config/context_registry.public.json`. Its branch registry has 25 workstream entries, but compared with the current canonical baseline it **omits the already-promoted `HOS-LEARN-002` Academy workstream** while adding HOS-MCP-001. Rebase/reconcile it against the current registry before merging. This candidate preserves both promoted Academy and the Control Room entry (with source metadata), and does not change PR #87 itself. Draft architecture PR #121 retains separate unratified policy proposals.
6. **Owner-device reality:** CI cannot substitute for real host-local browser, Model, Control Room and Notebook user acceptance.

## Bounded next work

1. Review this public-safe metadata patch; run the native registry parser plus relevant regression/CI tests and inspect the diff for private-data leaks. **No merge without owner-approved promotion.**
2. If accepted, update Issue #67's pointer without turning the issue into a second ledger.
3. Resolve constitutional compatibility as a distinct owner-governed decision; no spontaneous security changes.
4. Test one complete owner-local conversation → exact evidence → restart → semantic recall → correction → provenance path. Log evidence and bring Drive Notebook checkpoints forward or explicitly mark lag.
5. Separately triage open PRs based on verified code/evidence and present an approval-ready set; do not bulk merge or bulk close.

**Non-changes:** No executable Python source, local Mac files, private Notebook payloads, credentials, authorization rules, database schemas, backups, release artifacts, or destructive history actions are changed. **Public registry input does change and may affect deterministic routing; treat it as bounded behavior-bearing configuration, not only prose.**
