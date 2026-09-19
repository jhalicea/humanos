# HumanOS Portability & Exit Standard — Candidate v0.1

Status: FOUNDATION CANDIDATE
Workstream: HOS-FND-002
Canonical impact: NONE until promoted
Date: 2026-09-18

## Purpose

Define portability in observable terms so HumanOS does not confuse architectural intent, self-hosting, or open-source components with proven independence.

## Core rule

A capability is portable only to the level demonstrated by evidence.

Interfaces are necessary but insufficient. Exit ability is proven with open/exportable state, alternate/fake implementations where appropriate, documented restore/switch procedures, and executed drills.

## Relationship types

### Port
A provider/runtime implementation can be substituted without changing HumanOS capability semantics.

A meaningful port should be shaped by HumanOS concepts rather than provider objects. Provider-specific payloads terminate at the adapter boundary.

Where lock-in/risk is material, a port should eventually have:
- a fake implementation for tests/development;
- a shared contract/evaluation suite;
- an alternate implementation or documented replacement path;
- a tested provider-switch drill.

### Connector
HumanOS intentionally interoperates with an external product/system.

A connector should have:
- scoped credentials/permissions;
- explicit inbound/outbound data classes;
- HumanOS-owned identifiers/state where HumanOS is authoritative;
- external reference mapping rather than provider IDs as canonical IDs;
- replay/idempotency rules for events;
- import/export/reconciliation semantics;
- graceful outage/reconnect behavior.

## Independence levels

- L0 Provider-leaky
- L1 Exportable
- L2 Replaceable
- L3 Deployable elsewhere
- L4 Self-operated

Self-operation is not the goal by default. The goal is sufficient owner control, exit ability, and continuity.

## Replacement triggers

Do not replace a working provider merely because a future phase arrived. Revisit replacement when evidence shows:
- unacceptable security/privacy posture;
- repeated reliability failure;
- owner autonomy requirement;
- significant cost threshold;
- missing capability;
- regulatory/customer requirement;
- provider shutdown/hostile terms;
- exit drill failure revealing unacceptable lock-in.

## Standards preference

Prefer open standards/formats when they satisfy the requirement because they reduce adapter and migration cost. Avoid lowest-common-denominator abstractions that erase valuable capability.

## Evidence examples

- encrypted Notebook restore on a clean environment;
- provider/model substitution against the same bounded eval;
- Git repository mirror/restore verification;
- connector disconnect/reconnect without duplicate durable effects;
- export/import preserving HumanOS IDs, provenance, and relationships;
- browser unavailable while core runtime remains functional.

## Preservation

Observed exit times, blockers, data-loss risks, and drill evidence belong in the relevant work order/review artifact, not only in chat or model memory.
