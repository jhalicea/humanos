# HOS-LN-L1 recovery rehearsal — local candidate

Status: scoped work order, not promotion. Workspace: WS-HUMANOS. Route: EXTEND the Life Notebook capture/recall stream with a recovery qualification; HOS-LN-002's bounded explicit-preference memory was incorporated into canonical `runtime-0.1` by merged PR #122; this L1 rehearsal is still a separate, unpromoted candidate. Base: `runtime-0.1` commit `0fe4ea5751bb17be30656a5c95809b79d6718636`, selected from issue #67 evidence on 2026-10-08. No claim that an installed owner host uses this commit.

Problem: exact capture, close/reopen and bounded recall passed a prior synthetic check, but a complete source-identified turn and a correction turn have not been checked through encrypted backup and fresh-destination restore as one continuity path. This slice supplies one repeatable acceptance check and a short operator guide. It changes no Notebook, schema, preference, router, permission, or backup behavior.

Invariants: Notebook rows remain original transcripts only; a correction is a new original turn. Derived preference/context state is separate. Source identifiers and exact text survive readback. Imported historical text has no authority to invoke tools. Real records, private vaults, keys and credentials are excluded.

Acceptance: with a temporary synthetic vault, capture two source-identified turns, including a correction; close and reopen the writer; verify exact transcript and task source; retrieve both as bounded historical evidence; encrypt a backup; restore into a fresh vault; reverify exact rows, source and recall. A wrong passphrase must fail without creating a destination. The encrypted file must not contain the synthetic plaintext. Use the existing local backup API; do not invent key custody.

Failure/rollback: tests use only temporary paths and a test passphrase. Failure leaves the candidate unqualified. Rollback is reverting the isolated commit; it has no production data or format migration. Owner-host trial, off-device destination and independent key custody require separate owner decisions. Budget: one test module and this work order/guide, one focused test pass plus the repository gate. Stop and replan if a production change exceeds three modules or needs an unratified schema/security decision.

## User-facing local flow extension (2026-10-08)

Problem: the rehearsal is API-only. Existing `humanos turn/project` writes a ledger and projects it, but has no owner-directed exact Notebook read or recall command; projection also omits the source label from task state. Acceptance: one explicit-vault command captures an already-observed source-identified complete turn, prints its transaction and binding; a fresh command process reads back exact HUMAN/ASSISTANT rows plus source; a fresh command process performs bounded owner-directed recall with source labels. No default vault, model, summary, or implicit authority. Reject missing vault/source and malformed requests before opening a vault. Scope: one new CLI module over existing Notebook/capture/recall APIs and one subprocess integration test. Rollback: revert the extension commit; temporary synthetic vaults only. Required gate: focused test and full repository suite once under supported cryptography 49.0.0. Freeze a new commit for independent review, with no promotion claim.

Independent review repair: exact read now requires an owner, checks the transaction's verified binding, and uses the existing privacy-filtered Notebook page projection. A transaction with any hidden row is withheld in full. Capture rejects blank human or assistant text before opening a writer. Synthetic subprocess checks cover both rejection paths and a different-owner read. No schema or Notebook API changes.

## Exact-read existence privacy follow-up (2026-10-08)

Finding: the CLI returned distinguishable errors for an unknown transaction, a transaction owned by someone else, and a transaction whose transcript was hidden. Acceptance: all three cases return the same exit status, empty stdout, and identical stderr; hidden transcript text is never emitted. Also verify recall returns no rows for a different owner and omits a hidden transcript row. Scope: `notebook_local.py`, its subprocess test, and this work order. Focused gate: `python -m unittest tests.test_notebook_local -v` under the already-qualified Python 3.13.15 / cryptography 49.0.0 environment. This is local single-user privacy behavior, not authentication or multi-user authorization. No Notebook data, schema, format, or real-vault behavior changes.

## October 11 privacy and optional-CI remediation (candidate only)

The earlier `notebook_local.py capture` interface placed original HUMAN/ASSISTANT text in command-line arguments. Search queries and owner identifiers also appeared in argv. Such arguments may appear in process listings and shell history. This violates the intended privacy-by-default interface even when Notebook storage itself is local. This candidate now accepts one **bounded JSON object on stdin** for each `capture`, `read`, or `recall` operation; only the explicit vault path and command selector remain in argv. Required request fields:

- `capture`: `owner`, `source`, `conversation_id`, `turn_id`, `human`, `assistant`; optional `hcid` for an existing verified binding.
- `read`: `owner`, `tx`.
- `recall`: `owner`, `query`.

The CLI rejects malformed, oversized (more than 1 MiB of JSON characters), incomplete, or unknown-field requests **before** opening/creating a vault. Requests must be valid JSON on stdin; passing transcript text as flags is no longer supported. Do not embed private JSON in shell command lines or shell-history-backed `echo` commands. This is a synthetic-owner local tool, not a multi-user authentication service or guarantee that terminal output, OS memory, the vault path in argv, or caller logs cannot expose data.

Focused negative cases explicitly assert that unknown transaction, wrong owner, and hidden original transcript result in identical nonzero exit status, **empty stdout**, and equal generic stderr, without quoting exception contents. The original source evidence is not rewritten, summarized, or granted authority.

**CI incident and narrow repair:** On prior candidate head `96fe8eed1cdde9fb9ee845f7f20408b9fed37f8a`, the four general-regression jobs failed because the new encrypted-restoration rehearsal invoked optional `cryptography` even though the standard-library-only regression workflow does not install it. The four encrypted-backup/full-suite jobs succeeded with the optional dependency installed. The rehearsal now skips **only that encryption-dependent test** if `cryptography` is unavailable; the dedicated encrypted-backup workflow continues to exercise the full encrypted-restoration test on both OS and Python versions. This is not a waiver of encrypted-restore acceptance.

**Qualification required on the final immutable candidate SHA:** Verify regression and encrypted-backup/full-suite matrix success, with the encrypted-restoration test **executed** (not skipped) in the dedicated workflow; verify stdin privacy cases; review the diff independently. The candidate remains DRAFT/NOT PROMOTED. No owner-host/private-vault trial, merge, schema, cryptographic-key policy, or remote capture adapter is authorized by this note.

## October 11 retry idempotency follow-up (candidate only)

**Review finding:** `notebook_local.py capture` previously called `Notebook.bind()` before checking whether an exact provider/source conversation-turn ID already existed. A retry without an `hcid` created a new identity and then collided with the previous transaction. The underlying Notebook intentionally preserves collision evidence, so this could generate avoidable protected-page and recovery state from an ordinary caller retry. It did not satisfy the promised idempotent local capture interface.

**Bounded repair:** Reuse the existing `UniversalConversationCapture` vault-keyed source-turn transaction derivation to resolve an existing transaction **before** creating a new Notebook identity. Only an existing, verified same-owner binding with matching source, input and completed response can be replayed. Wrong-owner, mismatched HUMAN/ASSISTANT, or mismatched `hcid` requests fail with a generic error before invoking Notebook's collision recovery path. New turns retain the original capture contract. No canonical Notebook or capture-module code changed.

**Synthetic acceptance:** retry without `hcid` returns the same transaction, page and binding as the first capture; explicit matching-`hcid` retry does likewise. No additional identity, transaction, transcript, recovery or audit event is created. Conflicting text, owner and binding fail with indistinguishable generic CLI output and leave those record counts unchanged. These checks complement—not replace—the original source/read/recall/restore rehearsal.

**Limit:** This candidate invokes the capture module's current internal vault-keyed derivation helpers to avoid duplicating transaction-ID logic. Review that coupling before promotion; if a stable public capture lookup API is later required, design it as a separate bounded change rather than adding a new store or routing subsystem now. Original vaults, provider observers, and real owner data remain out of scope.

## October 11 whole-transaction recall privacy (candidate only)

**Review finding:** The earlier exact-read CLI denied a transaction if **any** transcript row was hidden, while its recall command delegated to the reusable row-scoped `search_notebook()` and could still return an unhidden assistant answer quoting a hidden human message (or vice versa). PR #125 promises hidden transactions will be withheld in its local CLI, so this mismatch is a real disclosure path within that candidate.

**Narrow protection:** After bounded source-backed recall, `notebook_local.py` suppresses every result whose transaction contains any `privacy_state.state='HIDDEN'` row, and recalculates `result_count`. Synthetic tests capture an assistant reply that repeats a human statement, hide the human row and the assistant row **independently**, verify no rows or quoted text for that transaction are returned from recall/read, verify an unrelated transaction remains retrievable, then unhide and recheck restoration.

**Limit:** This is a CLI-specific conservative filter using existing privacy state, **not** a change to the global `notebook_recall.py` policy or the canonical source transcript. Filtering after bounded ranking can return fewer than the allowed maximum visible results; it does not claim exhaustive redaction of copied material in unrelated transactions or model outputs, owner authentication, or secure deletion. Those require separate permission/data-lifecycle design and tests.

**Gate:** Run full regression and encrypted-backup suites on the exact changed candidate SHA; independent privacy review and explicit owner promotion remain required. No real Notebook data or keys are accessed.
