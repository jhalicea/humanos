# MLAB-P1-T2-LUNA — Raw Response

HYBRID INCREMENTAL

Keep Python as the authoritative kernel for the next 90 days, while isolating performance- or safety-critical boundaries behind narrow, language-neutral interfaces. Prototype Rust only where measurements justify it—such as parsing, cryptographic primitives, storage adapters, or sandbox helpers—and retain Python as the orchestration and policy layer.

Three strongest reasons:

1. The highest-risk correctness lies in authorization, provenance, SQLite transactions, and fail-closed behavior—not raw execution speed. A rewrite would replace a growing, testable system precisely where regressions are most expensive.

2. Incremental boundaries preserve reversibility. Rust components can be tested against Python reference implementations, introduced behind feature flags, and removed without changing the capability model or canonical data format.

3. Reliability improves fastest through focused tests, deterministic broker behavior, transaction verification, observability, and failure recovery. A full rewrite consumes the 90-day window without guaranteeing any of those outcomes.

The strongest argument against this choice is that maintaining Python and Rust together creates interface complexity, duplicated implementations, and a larger testing burden. That cost is real, so Rust experiments must remain small, explicitly measured, and limited to stable seams.

Revisit the decision if, after 90 days of representative workload testing, profiling shows that a clearly isolated Python component consumes at least 50% of total runtime or causes at least 20% of reliability failures, and a Rust replacement demonstrates a minimum 3× improvement without changing authorization or persistence semantics. At that point, consider rewriting that component—not the authoritative kernel by default.
