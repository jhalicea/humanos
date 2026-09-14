# Universal Conversation Capture

Status: **capture engine implemented on the current feature branch; live ChatGPT transport is not yet connected.**

Universal Conversation Capture is the HumanOS mechanism for preserving exact visible conversations from supported hosts such as ChatGPT, Claude, Gemini, Grok, or a local model UI. The provider is a source label; the Life Notebook remains the source of truth.

HumanOS separates transcript preservation from AI-derived interpretation.

## Lane A — exact transcript capture

This lane runs on every turn and does not call a language model.

1. A host receives the human's exact visible message.
2. `UniversalConversationCapture.begin_turn(...)` writes it to the Life Notebook.
3. The Notebook projects the page and performs integrity/readback verification.
4. The host may then continue normal conversation processing.
5. When the exact visible assistant message is available, the host calls `finish_turn(...)`.
6. HumanOS appends that assistant text, checkpoints the transaction, projects it, and verifies it again.

If the human-message write cannot be verified, HumanOS must not report it as saved. If the assistant message never arrives, the transaction remains pending and HumanOS does not invent a response.

The capture path stores exact visible text. It does not summarize, rewrite, classify, or infer.

## Lane B — checkpoint intelligence

This lane is separate and optional. It may run at explicit checkpoints such as session end, every N completed turns, or an owner-requested checkpoint.

Checkpoint workers may create summaries, decisions, tasks, discoveries, contradictions, course evidence, or other derived records. Derived records must cite the underlying Life Notebook transcript and never replace it.

Because the expensive intelligence lane does not run on every message, transcript durability does not require repeated LLM token use.

## Identity and idempotency

The host supplies a `source`, stable `conversation_id`, and stable `turn_id`. HumanOS derives a vault-keyed local digest from those identifiers and uses it to create the local transaction ID. Raw host identifiers are not copied into content-light audit events.

Retries with the same IDs and exact text are idempotent. A retry with different text fails closed rather than changing preserved evidence.

Different sources are isolated: the same conversation and turn IDs from ChatGPT and Claude resolve to different local transaction identities.

## Internal compatibility name

Runtime 0.1 already recognizes the internal phase `EXTERNAL_CAPTURE_PENDING`. That name stays for compatibility. In this context, "external" only means "outside the local HumanOS runtime." The user-facing feature is **Universal Conversation Capture**.

## Transport boundary

`conversation_capture.py` is transport-independent. It deliberately does not scrape a provider, expose an unauthenticated network port, or depend on a single vendor.

A transport adapter needs to deliver two events to HumanOS:

- exact human-visible message -> `begin_turn`
- exact assistant-visible message -> `finish_turn`

The existing HumanOS browser/native-messaging bridge is a candidate transport for supported desktop web sessions. Historical exports can use an import/reconciliation adapter. A future desktop bridge can use the same capture API.

Native mobile ChatGPT sessions require a supported source of turn events before HumanOS can guarantee real-time capture. Until such an adapter is connected and verified, HumanOS must not claim that every mobile ChatGPT turn is automatically saved.

## Promotion gate

Do not merge this feature based only on code review. Promotion requires:

- exact whitespace/Unicode round-trip tests;
- idempotent retry tests;
- conflicting retry fail-closed tests;
- crash-window recovery tests;
- source-isolation tests;
- full HumanOS regression suite on macOS and Linux;
- a live adapter test proving one human message and one assistant message appear exactly once in the Life Notebook and survive restart/readback.
