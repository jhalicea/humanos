# MLAB-P1-T3-ASTRA — Objective score

**Status:** OBJECTIVE SCORED / JON-FIT AND COMPARATIVE EFFICIENCY PENDING

## Objective score — 60/60

- Task completion: **20/20** — provides a concrete seven-day build, a working HumanOS capability by Day 7, one oral-interview question, one debugging/failure exercise, one measurable acceptance test, and explicit deferrals.
- Correctness and evidence discipline: **15/15** — distinguishes fixture/local webhook proof from live provider delivery, keeps implementation claims bounded, and explicitly states repository implementation is unverified.
- Judgment / prioritization: **10/10** — narrows the first capability to durable email intake, starts with fixtures/polling, enforces idempotency and provenance, and defers n8n/Make/agents until the intake path is reliable.
- Instruction following: **10/10** — concise, practical, within the requested length, and follows all explicit output constraints.
- Calibration: **5/5** — avoids claiming that a local webhook proves provider delivery and uses read-only mailbox access plus explicit test/replay boundaries.

## Comparative notes

Astra's strongest signal on Task 3 is scope discipline. Compared with Luna, it postpones n8n and model enrichment and focuses the seven-day build on one production-relevant HumanOS capability. It also uses a cleaner acceptance test: 20 distinct messages replayed in full must still yield exactly 20 Inbox items, while injected failures and restart behavior are tested separately.

One item to track during Jon-fit scoring: Day 3 introduces real OAuth/mailbox integration earlier than the fixture-only path, which raises setup complexity, but the answer keeps access read-only and the final acceptance test remains concrete.

Jon-fit and efficiency remain pending until the Task 3 cohort is complete.
