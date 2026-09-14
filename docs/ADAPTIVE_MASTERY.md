# HumanOS Adaptive Mastery Engine — v1 Candidate

## Purpose
HumanOS owns the teaching blueprint; each human owns an individualized curriculum. Courses are living skill graphs, not fixed playlists.

## Learning loop
Observe real work → capture technology/skill encounters → collect evidence → score mastery → identify gaps → choose context-appropriate practice → teach → reduce assistance → assess → update mastery.

Progression: **SEEN → INTRODUCED → ASSISTED → PRACTICED → DEMONSTRATED → MASTERED**.
Mastery requires transfer to unfamiliar situations, diagnosis, and explanation—not lesson consumption.

## Four grading dimensions
- Knowledge 25%
- Practical 30%
- Diagnostic 25%
- Communication 20%

Track separately: course completion %, mastery %, and (where applicable) career-readiness %. Do not infer one from another.

## Cross-project learning
Evidence is reusable. A BodyFix task can advance Git/API/database skills; a DFIR case can advance Windows, networking, evidence, AI verification, and reporting. Do not interrupt urgent work merely because a gap is encountered. Record it and schedule practice when useful.

## Refresh mode
When a learner has studied a topic before but is rusty, do not restart from lesson one by default. Begin with a compact diagnostic, preserve any valid evidence, then target weak or stale areas with short labs and spaced review. Exposure or a historical course does not automatically become a mastery score.

For Jon's networking refresh, the old CCENT/CCNA material is treated as prior exposure. Current networking objectives and hands-on diagnostics determine what needs review now.

Jon's 2020 Thinkful Engineering Flex work is treated the same way: surviving GitHub repositories establish prior exposure/practice and determine diagnostic starting points, but they do not automatically establish current mastery. The recovered and modernized path is documented in `docs/WEB_ENGINEERING_REACTIVATION.md`.

## Gap engine
Prefer high-priority, low-mastery skills while retaining spaced review of strong skills. Respect the human's goals, interests, available time, current projects, prerequisites, and chosen pace.

## Curriculum evolution
The system may research changes in a field and create **CANDIDATE** modules. It must not silently promote, delete, or rewrite canonical curriculum. Candidate updates require source provenance, relevance/durability analysis, redundancy check, prerequisite mapping, and human-governed promotion under HumanOS rules.

## Technology Encounter Ledger
Any meaningful technology touched in real work may become a skill node: commands, Git, Python, APIs, JSON/YAML, networking, cryptography, microprocessors, electricity/electronics, virtualization, containers, databases, LLM internals, PLC/industrial controls, and future technologies. Encounter does not equal mastery.

The current version-controlled ledger is `docs/TECHNOLOGY_LEDGER.md`. It records `SEEN`, `REFRESH`, and active encounters with provenance and maps them to course skill IDs without fabricating evidence-derived mastery.

## Flagship curricula
1. Cybersecurity, DFIR & Incident Response — preserve the historical ~47% as **career readiness**, not course completion.
2. AI Systems Engineering & HumanOS — preserve the current continuation at Transformer Architecture; do not invent a historical percentage.

Overlap between curricula is intentional.

## Reactivation curriculum
**Web & Software Engineering Reactivation — Thinkful 2020 → HumanOS 2026** restores Jon's prior Git/GitHub, JavaScript, jQuery, npm, React, routing, API, Node/Express, testing, PostgreSQL and authentication knowledge, then modernizes it for current HumanOS/AI systems work. It is refresh-first and evidence-based: old repositories establish provenance and diagnostic starting points, while new HumanOS-linked builds, failure drills, tests and teach-backs determine present mastery.

The course explicitly repairs the historical weak point around backend/authentication sequencing. HTTP failure handling, middleware, tokens/sessions/JWT, 401/403 behavior, refresh/revocation, database boundaries and end-to-end request tracing receive deeper treatment before any full-stack capstone. DSA/Big-O is intentionally sequenced after the application stack is stable rather than being piled onto an unfinished backend capstone.

Historical diagnostics may run without creating a competing production implementation slice. New React/Node/database/auth code is added to HumanOS only when a real selected HumanOS feature needs it.

See `docs/WEB_ENGINEERING_REACTIVATION.md` for the recovered evidence map, modernization baseline, skill graph, mastery gates and Noteful diagnostic.

## Supporting curriculum
**Technology Systems Literacy & Scarcity Niches** provides bounded exposure to technologies that are valuable to recognize but do not all justify specialization. It currently includes networking refresh, IAM/IDaaS/IGA and identity protocols/platforms, secure/managed file transfer, cloud and automation, IBM Netcool/event management, SAFe/RTE, front-office trading systems, kdb+/q, C++, and FPGA/HDL concepts.

High-value crossover topics such as networking, IAM, identity federation, Okta/Entra/Active Directory/SailPoint, cloud and secure file transfer are also included in the relevant flagship curricula. Niche technologies remain lower-priority unless evidence from projects or the labor market justifies promotion.

## Future domains
The same engine supports electronics, microprocessors/computer architecture, programming, networking, OSINT/intelligence, PLC/industrial controls, electricity, pumps/mechanical systems, woodworking, automotive, languages/communication, business/finance, design, and domains selected by other humans.

## Collaboration
External/commercial/local models may propose lessons, projects, sources, gap analyses, tests, and critiques. Their output remains proposal/evidence, never authority. Preserve provider/model/task metadata when available. Do not send private learner records or notebook content unless explicitly authorized and necessary.

## Human authority
The learner can pause a topic, change priorities, reject a curriculum update, request deeper mastery, or choose a different learning style. HumanOS adapts to the human; the human does not adapt to a rigid HumanOS syllabus.
