# MLAB-P1-T3-TERRA — Objective score

**Status:** OBJECTIVE SCORED / JON-FIT AND EFFICIENCY PENDING

## Objective score — 55/60

- Task completion: **20/20** — supplies a concrete 7-day build, one working HumanOS capability, one oral-interview question, one debugging exercise, one measurable acceptance test, and a clear defer list.
- Correctness and evidence discipline: **10/15** — technically strong overall, but the acceptance-test accounting is internally ambiguous: “20 inputs: 16 unique valid, 2 duplicates, 2 transient failures” reads as four disjoint categories totaling 20, while “first run creates 16 Inbox items and records 2 retryable failures” implies the failed items may also already be among the 16 created. The expected first-run state is therefore not unambiguous.
- Judgment / prioritization: **10/10** — starts with polling, idempotency, provenance, observability, retries, and local durable jobs; explicitly avoids distributed infrastructure and defers orchestration tools.
- Instruction following: **10/10** — stays within the requested scope and includes every required element.
- Calibration: **5/5** — clearly distinguishes a real Gmail read from a mocked path and says to document an unverified live step rather than implying it works.

## Comparative notes

Terra shows strong scope discipline and a practical learning sequence. Relative to Luna, it is narrower and defers n8n/Make entirely until the core mechanics are understood. Relative to Astra, it is similarly conservative but gives more emphasis to observability and cursor semantics. The main objective weakness is the acceptance-test arithmetic/state ambiguity, which is similar in kind to GPT-5.5 Task 3.

Jon-fit and efficiency remain pending until comparative scoring is completed.
