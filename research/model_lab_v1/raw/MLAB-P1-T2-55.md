# MLAB-P1-T2-55 — Raw Response

**Decision: HYBRID INCREMENTAL**

For the next 90 days, keep Python as the product runtime and introduce Rust only at narrow, measured trust boundaries once Python tests expose a real reliability or safety bottleneck.

**3 strongest reasons:**

1. **The architecture risk is authority, not language.** The critical invariant is that models cannot grant themselves permissions. That is enforced by broker design, tests, state transitions, auditability, and verification. A Rust rewrite does not automatically improve those boundaries.
2. **Python is already carrying momentum.** There is a runtime and growing test suite now. Rewriting the authoritative kernel immediately would trade known behavior for a second implementation whose bugs are harder to distinguish from design drift.
3. **Rust is valuable where failure costs are concentrated.** Use Rust surgically for stable, narrow components: capability policy evaluation, path normalization, signed audit records, deterministic state transition validation, or SQLite integrity tooling. Keep orchestration, experiments, adapters, and UI-facing workflows in Python.

**Strongest argument against HYBRID INCREMENTAL:**

It can become a permanent compromise where the trusted core remains too large in Python and Rust is added decoratively. Avoid that by defining crisp ownership: Python orchestrates; the broker-critical rules and canonical validators migrate only when specified, tested, and smaller than the Python surface they replace.

**90-day trigger to revisit:**

Revisit the decision if, during normal development, **three or more production-relevant reliability or security defects in the permission broker/canonical-state path are traced to Python runtime behavior, dynamic typing, dependency ambiguity, or untestable state transitions**, and each would plausibly have been prevented by a smaller typed kernel.

Until then: **HYBRID INCREMENTAL**. Build reliability by shrinking and testing the trusted surface first, not by rewriting the system on faith.
