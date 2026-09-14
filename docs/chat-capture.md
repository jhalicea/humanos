# Exact Chat Capture

Status: **capture engine implemented on `feature/exact-turn-capture`; ChatGPT transport not yet connected.**

HumanOS treats exact transcript preservation and AI-derived interpretation as two separate lanes.

## Lane A — exact capture

This lane runs on every turn and does not call a language model.

1. The host receives the human's exact visible message.
2. `ExternalTurnCapture.begin_turn(...)` writes it to the Life Notebook.
3. The Notebook projects the page and performs integrity/readback verification.
4. The host may then allow the external model/service to continue.
5. When the exact visible assistant message is available, the host calls `finish_turn(...)`.
6. HumanOS appends the assistant text, checkpoints the transaction, projects it, and verifies it again.

If step 2 fails, the host must not report the turn as saved. If step 5 never arrives, the transaction remains `EXTERNAL_CAPTURE_PENDING`; HumanOS does not invent the missing assistant response or run a local model to fill it in.

The capture path stores exact visible text. It does not summarize, rewrite, classify, or infer.

## Lane B — checkpoint intelligence

This lane is separate and optional. It may run at explicit checkpoints such as session end, every N completed turns, or an owner-requested checkpoint.

Checkpoint workers may create summaries, decisions, tasks, discoveries, contradictions, course evidence, or other derived records. Derived records must cite the underlying Life Notebook transcript and never replace it.

Because the expensive intelligence lane does not run on every message, transcript durability does not require repeated LLM token use.

## Identity and idempotency

The external host supplies stable `conversation_id` and `turn_id` values. HumanOS derives a vault-keyed local digest from those identifiers and uses it to create the local transaction ID. Raw external identifiers are not copied into content-light audit events.

Retries with the same IDs and exact text are idempotent. A retry with different text fails closed rather than changing preserved evidence.

## Transport boundary

`external_capture.py` is transport-independent. It deliberately does **not** scrape ChatGPT, expose a network port, or depend on a single provider.

A transport adapter still needs to deliver two events to HumanOS:

- `human_visible` -> `begin_turn`
- `assistant_visible` -> `finish_turn`

Possible adapters include the existing HumanOS browser/native-messaging bridge for supported desktop web sessions, a future authenticated local desktop bridge, and an import/reconciliation adapter for historical exports.

Native mobile ChatGPT sessions require a supported source of turn events before they can be guaranteed in real time. Until such an adapter is connected and verified, HumanOS must not claim that every ChatGPT turn is automatically saved.

## Promotion gate

Do not merge this feature based only on code review. Promotion requires:

- exact whitespace/Unicode round-trip tests;
- idempotent retry tests;
- conflicting retry fail-closed tests;
- crash-window recovery tests;
- full HumanOS regression suite on macOS and Linux;
- a live adapter test proving one human message and one assistant message appear exactly once in the Life Notebook and survive restart/readback.
