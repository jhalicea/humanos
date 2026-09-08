# Non-blocking turn recovery

## Problem

An unfinished transaction on a verified Notebook page caused every later human
message to fail before transaction capture. The terminal simultaneously said the
human could continue chatting, which was false. Exact rejected inputs survived
only in the fallback recovery ledger.

## Change

New transactions may start while an older transaction remains unfinished. The
older task stays independently resumable or closable and is never executed in the
background. Global transcript sequence records the actual capture order, so a
late answer to an older turn appears when it is produced. Startup recovery imports
fallback human inputs as pending transactions without synthesizing an assistant
response.

## Review and rollback

Run `python3 -m unittest discover -s tests -v`. Regression tests cover a new turn
and late resume on one page, exact sequence order, fallback input recovery, and
readback verification. Review that transaction identity/idempotency checks remain
unchanged and that no model or tool runs during startup recovery.

Rollback code baseline: `2372ef7`. Keep newer Notebook evidence even if code is
rolled back. This change does not close or discard existing recovery items.
