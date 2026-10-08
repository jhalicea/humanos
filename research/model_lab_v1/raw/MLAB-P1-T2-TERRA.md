# MLAB-P1-T2-TERRA — Raw Response

Choose: **HYBRID INCREMENTAL**

For the next 90 days, keep the authoritative kernel in Python while extracting only proven hot-path or security-critical components behind narrow, tested interfaces.

The 3 strongest reasons:

1. Reliability comes first from clearer boundaries, invariants, and tests—not a language rewrite. Strengthen the SQLite transaction model, capability broker policy checks, audit trail, and failure-mode tests where the system already runs.
2. An immediate Rust rewrite creates maximum migration risk precisely in the authority-bearing code. It would slow feature learning, duplicate logic during transition, and make it harder to tell whether defects are design problems or porting errors.
3. Python is appropriate for rapid iteration on a local-first system with replaceable models and no need for distributed infrastructure. Rust can be introduced selectively for components that demonstrably need memory safety, performance, or a stronger deployment boundary—without turning the system into a multi-language architecture by default.

Single strongest argument against this choice: Python cannot provide Rust’s compile-time memory-safety guarantees for a security-critical authoritative kernel. If the broker increasingly handles untrusted extensions or processes hostile inputs, that is a serious limitation.

Measurable revisit trigger: revisit the decision if, after adding targeted tests and profiling, the capability broker or canonical-state transaction path causes **three production reliability incidents or fails its defined latency/SLO target in a rolling 30-day period**, with root causes attributable to Python runtime behavior rather than policy/design defects.

For the 90-day plan: harden the Python kernel, define stable interfaces around the broker and persistence layer, measure failure and latency data, and prototype one isolated Rust component only if the evidence identifies a specific need.
