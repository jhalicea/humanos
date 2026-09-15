# MLAB-P2-A-TERRA — Phase 2 Trial A Score

**Model:** GPT-5.6 Terra  
**Trial:** Thought Partner / Problem Framing — supplemental continuing-model run  
**Raw preserved:** `research/model_lab_v1/raw/MLAB-P2-A-TERRA.md`  
**Efficiency:** UNKNOWN — no attributable wall-clock or before/after usage evidence was supplied.

## Known score — 89/90

- **Job outcome quality — 40/40**
  - Reframed the decision around the smallest local durability boundary required before HumanOS may consider a turn captured.
  - Recommended a narrow synchronous durable journal plus asynchronous/recoverable downstream projection.
  - Added a useful three-state distinction: `Captured`, `Projected`, and `Reconciled`.
  - Produced a concrete 30-day implementation and failure-test plan.

- **Working fit / conversation — 19/20**
  - Clear, concise, low-ceremony, and practical.
  - More methodical/state-model oriented than exploratory or conversationally reframing; this is inferred from the answer itself, not from owner preference.

- **Judgment and scope control — 15/15**
  - Kept the design deliberately small: one local SQLite journal, one projection/outbox worker, one adapter first, no external queue service.
  - Correctly separated capture durability from notebook presentation and provider reconciliation.

- **Evidence / reliability discipline — 10/10**
  - Bounded the no-loss claim to locally acknowledged events and called upstream unobservability out explicitly.
  - Distinguished WAL from backup/recovery and required tested restore behavior.
  - Preserved corrections/predecessors rather than silently overwriting.

- **Correction burden / steering responsiveness — 5/5**
  - No clarification or correction required in the first response.

## Distinctive behavior versus the other Trial A runs

Terra's strongest differentiator is a **methodical state-and-reconciliation model**:
- explicitly separates `Captured`, `Projected`, and `Reconciled`;
- treats provider adapters as imperfect sources with different delivery guarantees;
- emphasizes immutable source events plus a readable projection;
- raises privacy/noise concerns around capturing every token or transient partial response;
- uses a conventional, maintainable engineering slice rather than expanding the architecture.

It overlaps heavily with Sol and Luna on the durability boundary, but is less focused on Sol's authority/truth semantics and less compressed than Luna's minimal-execution framing. It also explores fewer outer failure domains than Astra.

## Measurement note

The owner's prior qualitative statement that Astra feels more like GPT-5.5 was **not used** in this score. This score is based only on Terra's answer and the frozen Trial A rubric.

## Provisional role signal

**GENERAL ENGINEER / METHODICAL SYSTEMS PLANNER / THOUGHT-PARTNER CANDIDATE**
