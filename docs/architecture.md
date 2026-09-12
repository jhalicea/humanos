# Architecture

HumanOS separates durable human records, model inference, governed tools, and visible interaction so that no model is treated as the operating system itself.

## Core components

| Component | Responsibility |
|---|---|
| Mirror | Human-facing interface and status surface |
| Notebook | Durable transcript, transaction, and recovery state |
| Model adapter | Replaceable inference boundary; local Ollama in Runtime 0.1 |
| Capability registry | Narrow tool contracts and argument validation |
| Work executor | Authorized execution with persisted scope and outcomes |
| Audit and integrity | Append-only events, hashes, provenance, and verification |
| Recovery | Explicit handling of interrupted or uncertain operations |

## Control flow

1. The human supplies a request.
2. HumanOS captures the request and its authorized scope.
3. Mirror routes local queries or invokes the configured model.
4. Requested tools are validated against capability and permission boundaries.
5. Results, failures, and state transitions are persisted.
6. Final output is read back before emission.

Human authority remains above model suggestions. Remote providers, broader tool access, and autonomous execution require separate policies and are not implied by this architecture.
