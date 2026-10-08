# HOS-LN-L1 recovery rehearsal — local candidate

Status: scoped work order, not promotion. Workspace: WS-HUMANOS. Route: EXTEND the Life Notebook capture/recall stream with a recovery qualification; HOS-LN-002 remains an unpromoted, broader memory candidate. Base: `runtime-0.1` commit `0fe4ea5751bb17be30656a5c95809b79d6718636`, selected from issue #67 evidence on 2026-10-08. No claim that an installed owner host uses this commit.

Problem: exact capture, close/reopen and bounded recall passed a prior synthetic check, but a complete source-identified turn and a correction turn have not been checked through encrypted backup and fresh-destination restore as one continuity path. This slice supplies one repeatable acceptance check and a short operator guide. It changes no Notebook, schema, preference, router, permission, or backup behavior.

Invariants: Notebook rows remain original transcripts only; a correction is a new original turn. Derived preference/context state is separate. Source identifiers and exact text survive readback. Imported historical text has no authority to invoke tools. Real records, private vaults, keys and credentials are excluded.

Acceptance: with a temporary synthetic vault, capture two source-identified turns, including a correction; close and reopen the writer; verify exact transcript and task source; retrieve both as bounded historical evidence; encrypt a backup; restore into a fresh vault; reverify exact rows, source and recall. A wrong passphrase must fail without creating a destination. The encrypted file must not contain the synthetic plaintext. Use the existing local backup API; do not invent key custody.

Failure/rollback: tests use only temporary paths and a test passphrase. Failure leaves the candidate unqualified. Rollback is reverting the isolated commit; it has no production data or format migration. Owner-host trial, off-device destination and independent key custody require separate owner decisions. Budget: one test module and this work order/guide, one focused test pass plus the repository gate. Stop and replan if a production change exceeds three modules or needs an unratified schema/security decision.
