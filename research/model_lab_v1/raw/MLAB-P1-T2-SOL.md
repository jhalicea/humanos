# MLAB-P1-T2-SOL — Raw Response

**Decision: HYBRID INCREMENTAL for the next 90 days.**

Keep Python as the authoritative runtime during this period. Strengthen its permission boundaries and reliability evidence, then evaluate one small Rust component behind an explicit interface. Avoid a kernel rewrite.

The three strongest reasons:

1. **Reliability comes from enforced invariants, not language alone.** Rust can prevent many memory and concurrency errors, but it cannot automatically prevent incorrect permissions, unsafe SQL transactions, or models influencing authorization. First establish broker checks that fail closed, transaction guarantees, and tests proving that model output cannot grant authority.
2. **An immediate rewrite would replace working evidence with migration risk.** The existing Python runtime and growing tests represent accumulated knowledge. A rewrite can introduce behavioral differences in authorization, recovery, and canonical state. Incremental replacement preserves that knowledge and allows direct comparison against the established behavior.
3. **A small extraction can establish whether Rust earns its cost.** Select a component with a clear boundary and a demonstrated problem—such as processing untrusted input or a concurrency-sensitive operation. Keep the application as one local system, without adding services. Measure correctness, failure rate, performance, and maintenance effort before expanding Rust’s role.

**The strongest argument against this choice:** maintaining two languages creates build, packaging, debugging, and interface costs. If Python already meets the reliability target, even a small Rust component could consume engineering time better spent improving tests and recovery.

**The next 90 days:** spend the first month documenting and testing authorization and transaction invariants, including crash recovery. Use the second month to collect failure evidence and select one justified extraction. During the final month, test that component against the Python implementation. If no suitable problem emerges, finish with stronger Python and no production Rust.

**Measurable revisit trigger:** revisit whether to move the authoritative kernel to Rust if **two independently reproduced, high-severity authorization or canonical-state failures within 90 days share a root cause that a specified Rust design would structurally eliminate**. Confirm that claim with a prototype and regression tests before approving the larger migration.
