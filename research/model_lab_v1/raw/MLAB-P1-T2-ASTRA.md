# MLAB-P1-T2-ASTRA — Raw Response

**HYBRID INCREMENTAL**

For the next 90 days, keep Python as the authoritative runtime, strengthen its permission boundaries and recovery behavior, and make one narrow component replaceable. Introduce Rust only where measurements demonstrate a reliability benefit.

The three strongest reasons:

1. **Reliability comes primarily from explicit invariants.** Permissions must be checked at execution time, models must never grant authority, and interrupted operations must leave recoverable state. Rewriting does not establish these properties automatically. Testing them in the existing runtime addresses risk immediately.
2. **A full rewrite would replace known behavior with unproven behavior.** The growing Python test suite is an asset. Use it to define observable contracts for authorization, SQLite transactions, retries, and recovery before changing implementations. This also makes a future Rust component verifiable against existing behavior.
3. **Selective replacement preserves simplicity and flexibility.** A stable, narrow interface allows a component to move to Rust without replacing orchestration, integrations, and every working feature. Keep a single local application; language boundaries do not require microservices.

**90-day execution**

- **Days 1–30:** Document authorization and state invariants. Establish reliability measurements. Add tests for permission denial, revocation, crashes, and interrupted writes.
- **Days 31–60:** Fix demonstrated failures. Centralize broker enforcement and separate policy decisions from filesystem, browser, network, and app adapters. Test retries without duplicate external effects.
- **Days 61–90:** Run fault-injection tests and review results. If a specific component has failures Rust could prevent, prototype that component behind the same interface and run identical tests against both implementations. Otherwise, retain Python and the replacement seam.

**Strongest argument against this choice:** Two languages add build, packaging, debugging, and interface complexity. For a small team, that cost could exceed the reliability benefit. A Rust prototype must earn production adoption through measured results.

**Measurable revisit trigger:** Revisit kernel migration if, within a rolling 30-day period, **two independently reproduced, high-severity failures** in authorization or canonical-state integrity are traced to a mechanism that a proposed Rust design demonstrably prevents, with regression tests proving prevention.

The decision is **HYBRID INCREMENTAL**: improve and measure the working system now; replace proven weak points selectively.
