# Capture MCP durability review

Status: LOCAL CANDIDATE — review findings addressed; no remote push, pull request, merge, deployment, or ChatGPT connection is claimed.

## Scope and acceptance criteria

This change is limited to the local Capture Fabric importer. It must preserve exact visible text and make recovery truthful when the remote relay, local staging inbox, or Life Notebook importer is interrupted.

| Requirement | Evidence |
| --- | --- |
| Exact append and duplicate retry | `tests.test_capture_fabric` and `tests.test_capture_mcp_recovery` |
| Receipt survives before staging | Fresh-process receipt-before-staging crash test |
| Staging transaction survives interruption | Fresh-process uncommitted-staging crash test |
| Partial and completed Notebook writes recover without duplication | Fresh-process partial-turn and pre-acknowledgment crash tests |
| Storage lock remains retryable across restart | SQLite lock and fresh-process recovery tests |
| Permanent errors do not stop later captures | Importer permanent-error test |
| Historical failure reason and owner requeue remain attributable | Append-only `failure_history` tests |

## Review dispositions

| Finding | Disposition |
| --- | --- |
| Permanent errors were retried and could block the queue | Fixed: only explicit SQLite lock/busy messages, selected transient OS errors, and timeouts retry. |
| Existing `ERROR` rows were invisible | Fixed: status reports permanent and retryable counts; `requeue_error` is explicit. |
| Requeue discarded failure context | Fixed: terminal and owner-requeue records append to `failure_history`. |
| Restart proof was only orderly object reopen | Fixed: child-process tests terminate after receipt, after a staged commit, inside an uncommitted staging transaction, after a partial Notebook write, and after a completed Notebook write before acknowledgment. |

## Validation

Run from the candidate checkout:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_capture_importer tests.test_capture_mcp_recovery tests.test_capture_fabric tests.test_conversation_capture tests.test_conversation_transport tests.test_external_capture tests.test_recovery_jsonl_tail
```

The test suite uses temporary vaults, synthetic transcript content, a local SQLite relay, and no provider credentials.

## Limits and rollback

This does not validate the encrypted PostgreSQL relay, an MCP HTTP endpoint, a ChatGPT developer-mode connection, provider transcript visibility, or device-loss recovery. The local relay remains a test adapter, not production evidence.

Rollback is `git revert` of the candidate series beginning at `b89de9f`. No schema migration destroys prior importer data: existing inbox rows remain readable, and `failure_history` is additive.
