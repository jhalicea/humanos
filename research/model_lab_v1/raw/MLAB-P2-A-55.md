# HumanOS Model Lab v1 — Phase 2 Trial A — GPT-5.5 RAW

The real decision is not “sync write vs queue vs batch.”

The real decision is: **what is the first trustworthy local record of a visible conversation turn?**

Everything else is downstream.

For HumanOS, I would make the durable local journal the first source of truth for capture, then materialize the Life Notebook from it. Not because queues are fashionable, but because your constraints conflict in a very specific way: you want “never lose turns” and “do not slow every turn.” The clean answer is to make the per-turn operation extremely small, local, append-only, and auditable.

My recommendation:

**For the next 30 days, build a local durable turn journal as the capture boundary.** Every visible turn gets appended immediately to SQLite in a minimal `conversation_turn_journal` table, in the same local HumanOS runtime, with enough provenance to later prove what was seen, where it came from, when it was captured, and whether it has been materialized into the canonical Life Notebook.

Then run notebook materialization asynchronously from that journal.

That gives you a truthful status model:

- captured locally: yes/no
- materialized into notebook: yes/no
- provider/connector synced: yes/no
- export/checkpointed: yes/no

Those are different claims. HumanOS should never blur them.

The assumption I would challenge hardest is that “Life Notebook capture” means writing directly into the notebook. I think that’s too much responsibility for the notebook layer. The notebook should be a readable, canonical projection. The journal should be the loss-prevention layer.

I would also challenge the hidden assumption that all providers can expose turns the same way. ChatGPT, Claude, Gemini, local models, and your own UI will have different capture surfaces. So the invariant should not be “all providers write to the notebook.” It should be: **all capture adapters emit the same local turn event envelope**. The adapter can be provider-specific; the journal schema should be boring and stable.

I would not choose pure synchronous canonical writes. Too much latency and too much coupling. If the notebook transform, provenance enrichment, deduplication, title inference, or connector layer stalls, the user feels it.

I would not choose batch-only capture. It violates the emotional and operational requirement: losing conversation history is unacceptable. Batching is fine for materialization, compaction, export, and checkpointing. It is not fine as the first durable record.

The hybrid I’d use is simple:

1. **Immediate local append**
   Capture each visible turn to SQLite with a durable commit. Keep the record small: conversation id, turn id, role, visible text/content refs, provider, source surface, timestamps, capture method, content hash, parent/sequence info, and raw-ish payload where appropriate.
2. **Async materializer**
   A worker reads unmaterialized journal rows and updates the Life Notebook. This can batch every few turns or every few seconds. If it fails, rows remain pending.
3. **Readback/status**
   HumanOS can say: “12 turns captured locally, 10 materialized, 2 pending.” That is the truthful status you care about.
4. **Idempotency and dedupe**
   Every turn event needs a deterministic key or hash strategy so retries do not duplicate notebook entries.
5. **Checkpoint/export later**
   Periodically checkpoint the journal and notebook projection, but do not rely on checkpoints as primary capture.

For the next 30 days, I would keep scope brutally narrow:

**Week 1:** Define the turn event envelope and SQLite journal table. Write tests for append, retry, dedupe, ordering, crash recovery, and status reporting.

**Week 2:** Implement one capture adapter against the easiest local surface you control. Do not start with every provider. Prove the invariant first.

**Week 3:** Build the async materializer into the Life Notebook, with pending/failed/replayed states and readback verification.

**Week 4:** Add one second provider/interface path and run failure drills: provider unavailable, connector broken, app closes mid-turn, duplicate replay, materializer crash, notebook write failure.

The acceptance criterion should be concrete: after simulated crashes and connector failures, every visible captured turn is still present in the local journal, deduplicated, ordered, and either materialized or truthfully marked pending/failed.

That is not architecture for architecture’s sake. It is the smallest design that respects the thing you said is non-negotiable: local continuity must survive everything else.
