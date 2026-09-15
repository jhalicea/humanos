# Capture MCP durability review

Status: LOCAL CANDIDATE — review findings addressed; no remote push, pull request, merge, deployment, or ChatGPT connection is claimed.

## Scope and acceptance criteria

This change is limited to the local Capture Fabric importer. It must preserve exact visible text and make recovery truthful when the remote relay, local staging inbox, or Life Notebook importer is interrupted.

| Requirement | Evidence |
| --- | --- |
| Exact append and duplicate retry | `tests.test_capture_fabric` and `tests.test_capture_mcp_recovery` |
| Receipt survives before staging | Fresh-process receipt-before-staging crash test |
| Staging transaction survives interruption | Fresh-process uncommitted-staging crash test |
| Partial and completed Notebook writes recover without duplication | Fresh-process crash inside the human event after `Notebook.start` and before `EXTERNAL_CAPTURE_STARTED`; pre-acknowledgment crash test |
| Named Notebook storage errors have truthful queue behavior | SQLite lock restart proof; injected `ENOSPC` retries; injected permission loss becomes visible `ERROR` until explicit owner requeue |
| Importer state cannot record a failure | Fresh-process, actual SQLite `max_page_count` exhaustion test: loud import failure, no false failure-history record, remote relay remains recoverable |
| Permanent errors do not stop later captures | Importer permanent-error test |
| Historical failure reason and owner requeue remain attributable | Append-only `failure_history` tests |

## Review dispositions

| Finding | Disposition |
| --- | --- |
| Permanent errors were retried and could block the queue | Fixed: only explicit SQLite lock/busy messages, selected transient OS errors, and timeouts retry. |
| Existing `ERROR` rows were invisible | Fixed: status reports permanent and retryable counts; `requeue_error` is explicit. |
| Requeue discarded failure context | Fixed: terminal and owner-requeue records append to `failure_history`. |
| Importer storage failure could be mistaken for a recorded Notebook failure | Fixed: failure-history persistence is transactional with queue disposition. If that SQLite transaction cannot commit, `drain()` raises a loud error stating that no failure record was written; the remote relay remains the recovery source. |
| Restart proof was only orderly object reopen | Fixed: child-process tests terminate after receipt, after a staged commit, inside an uncommitted staging transaction, after a partial Notebook write, and after a completed Notebook write before acknowledgment. |

## Validation

Validated locally for implementation commit `fe4fe21b869668fb79d40b90bcf5d9677bb2f384`:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_capture_importer tests.test_capture_mcp_recovery tests.test_capture_fabric tests.test_conversation_capture tests.test_conversation_transport tests.test_external_capture tests.test_recovery_jsonl_tail
```

The focused command completed with **63 tests passed**. The added fresh-process SQLite-full case increases the prior 62-test result by one. The suite uses temporary vaults, synthetic transcript content, a local SQLite relay, and no provider credentials.

## Limits and rollback

This does not validate the encrypted PostgreSQL relay, an MCP HTTP endpoint, a ChatGPT developer-mode connection, provider transcript visibility, device-loss recovery, physical host-disk exhaustion, permission repair, or importer-state-directory loss. The fresh-process `max_page_count` case is a real SQLite-full condition in the importer database, but remains a constrained SQLite test rather than host filesystem proof. The `ENOSPC` and permission cases are controlled fault injection at the Notebook boundary; they prove queue disposition, not physical-storage recovery. The local relay remains a test adapter, not production evidence.

Rollback is `git revert` of the candidate series beginning at `b89de9f`. No schema migration destroys prior importer data: existing inbox rows remain readable, and `failure_history` is additive.
