# Universal Conversation Capture

Status: **capture engine and verified local transcript batching are implemented on the current feature branch; live ChatGPT transport and automatic Google Drive transport are not yet connected.**

Universal Conversation Capture is the HumanOS mechanism for preserving exact visible conversations from supported hosts such as ChatGPT, Claude, Gemini, Grok, or a local model UI. The provider is a source label; the Life Notebook remains the source of truth.

HumanOS separates transcript preservation, off-device backup, and AI-derived interpretation.

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

## Lane B — verified off-device backup

Google Drive is a replica/backup target, not the primary write path.

`TranscriptBatchOutbox` reads only transcript rows that already exist in the verified local Life Notebook. It creates an immutable local batch containing:

- `transcript.jsonl` — exact machine-readable transcript rows;
- `transcript.md` — readable projection of the same rows;
- `manifest.json` — sequence range, byte counts, SHA-256 values, and a vault-keyed manifest proof.

The batch is written to a private local outbox and read back before it is eligible for upload. A Drive transport then uploads the two transcript artifacts. It must read the remote bytes back and calculate their SHA-256 values. Only after those hashes match the local manifest does HumanOS advance its authenticated backup cursor.

If Drive is unavailable, the batch remains pending locally and conversation capture continues. A retry reuses the same pending batch rather than producing overlapping transcript ranges.

The cursor is the commit point for remote backup. A crash after remote verification but before local housekeeping is repaired on the next backup pass.

The intended path is:

`provider -> Universal Conversation Capture -> local SQLite evidence -> verified projections -> transcript batch outbox -> Google Drive readback verification -> backup cursor commit`

This batch lane is separate from full-vault disaster recovery. HumanOS already has authenticated portable-vault backups and AES-256-GCM encrypted vault backups. Those encrypted vault snapshots should also be copied off-device periodically so recovery does not depend only on transcript files.

## Lane C — checkpoint intelligence

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

`conversation_capture.py` and `transcript_backup.py` are transport-independent. They deliberately do not scrape a provider, expose an unauthenticated network port, or depend on a single vendor.

A conversation transport adapter needs to deliver two events to HumanOS:

- exact human-visible message -> `begin_turn`
- exact assistant-visible message -> `finish_turn`

A backup transport adapter needs to:

1. obtain the pending batch artifact paths;
2. upload each artifact to the configured private destination;
3. read the remote bytes back;
4. calculate SHA-256 from the readback bytes;
5. call `confirm_upload(...)` with the remote file IDs and verified hashes.

The existing HumanOS browser/native-messaging bridge is a candidate conversation transport for supported desktop web sessions. Historical exports can use an import/reconciliation adapter. A future desktop bridge can use the same capture API.

Native mobile ChatGPT sessions require a supported source of turn events before HumanOS can guarantee real-time capture. Until such an adapter is connected and verified, HumanOS must not claim that every mobile ChatGPT turn is automatically saved.

## Privacy and repository boundary

The public GitHub repository contains code, tests, and documentation only. It must not contain Life Notebook transcript payloads, Google Drive folder IDs, access tokens, OAuth credentials, backup passphrases, or other private runtime configuration.

Transcript batches and encrypted vault snapshots belong in the owner's private local/Drive storage.

## Promotion gate

Do not merge this feature based only on code review. Promotion requires:

- exact whitespace/Unicode round-trip tests;
- idempotent retry tests;
- conflicting retry fail-closed tests;
- crash-window recovery tests;
- source-isolation tests;
- transcript-batch cursor and remote-hash fail-closed tests;
- full HumanOS regression suite on macOS and Linux;
- a live conversation adapter test proving one human message and one assistant message appear exactly once in the Life Notebook and survive restart/readback;
- a live Drive adapter test proving one prepared batch is uploaded, read back byte-for-byte, confirmed locally, and not duplicated on retry.
