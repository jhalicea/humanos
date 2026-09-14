# Universal Conversation Capture

Status: **capture engine, durable local transport/spool, ChatGPT web adapter code, and verified local transcript batching are implemented on the current feature branch. The desktop adapter is not yet installed/live-tested on Jon's Mac, native iOS ChatGPT capture is not available, and automatic Google Drive transport is not yet connected.**

Universal Conversation Capture is the HumanOS mechanism for preserving exact visible conversations from supported hosts such as ChatGPT, Claude, Gemini, Grok, or a local model UI. The provider is a source label; the Life Notebook remains the source of truth.

HumanOS separates transcript preservation, off-device backup, and AI-derived interpretation.

## Lane A — exact transcript capture

This lane runs on every turn and does not call a language model.

1. A host receives the human's exact visible message.
2. The local transport fsyncs it into the independent capture spool and verifies readback.
3. When the Life Notebook writer is available, `CaptureIngestor` passes the preserved event through `UniversalConversationCapture.begin_turn(...)`.
4. The Notebook projects the page and performs integrity/readback verification.
5. When the exact visible assistant message is finalized, the host repeats the same path and `finish_turn(...)` checkpoints the turn.

If the Notebook writer is temporarily busy, the already-fsynced spool event remains local and pending. HumanOS does not discard it or pretend it reached the canonical Notebook. If the assistant message never arrives, the human half-turn remains preserved without inventing a response.

The capture path stores exact visible text. It does not summarize, rewrite, classify, or infer.

## Local transport and writer-lock boundary

The Life Notebook deliberately has a single-writer lock. Universal Conversation Capture does not weaken that guarantee merely to accept browser events.

`conversation_transport.py` therefore adds a small independent SQLite capture spool under the private HumanOS runtime. It uses WAL mode, synchronous FULL, owner-only files, a separate 32-byte transport secret, HMAC identities, exact-text proofs, idempotent event IDs, append-only event triggers, and readback verification.

The resulting local path is:

`ChatGPT web -> browser content adapter -> Chrome native messaging -> authenticated Unix socket -> capture spool (durable local receipt) -> Life Notebook ingestor -> canonical transcript`

The capture daemon attempts Notebook ingestion immediately after each event. If another HumanOS process owns the Notebook writer lock, the event stays in the spool. The daemon periodically retries. Once the writer lock is free, the event is moved through the normal Universal Conversation Capture API and receives an ingest receipt.

This creates two distinct truthful states:

- **stored locally** — exact text is durably present in the capture spool;
- **Notebook ingested** — exact text is also present in the canonical Life Notebook and verified there.

A crash between those states is recoverable: replay from the spool is idempotent, so a retry either reuses the preserved transaction or fails closed if content differs.

## ChatGPT web adapter

The feature branch includes a ChatGPT content adapter for desktop Chromium-based browsers. It observes rendered nodes carrying ChatGPT's user/assistant author-role attributes, preserves `innerText` without trimming or normalization, waits for assistant output to stop streaming and stabilize, and forwards the event to a dedicated native-messaging host.

The browser page never receives HumanOS secrets. The extension service worker talks to `com.humanos.conversation_capture`; the local native host reads the owner-only secret/config and signs requests for the capture daemon.

Because ChatGPT's web DOM is controlled by the provider and can change, this adapter must pass a live browser acceptance test before promotion. DOM fallback identifiers and regenerated-response handling are deliberately fail-closed/idempotent rather than silently overwriting a prior turn.

Native iOS ChatGPT is a separate transport problem: a Mac browser extension cannot observe turns inside the iOS native app. HumanOS must not claim those turns are automatically captured until a supported iOS/share/export/app integration supplies the exact turn events.

## Lane B — verified off-device backup

Google Drive is a replica/backup target, not the primary write path.

`TranscriptBatchOutbox` reads only transcript rows that already exist in the verified local Life Notebook. It creates an immutable local batch containing:

- `transcript.jsonl` — exact machine-readable transcript rows;
- `transcript.md` — readable projection of the same rows;
- `manifest.json` — sequence range, byte counts, SHA-256 values, and a vault-keyed manifest proof.

The batch is written to a private local outbox and read back before it is eligible for upload. A Drive transport then uploads the two transcript artifacts. It must read the remote bytes back and calculate their SHA-256 values. Only after those hashes match the local manifest does HumanOS advance its authenticated backup cursor.

If Drive is unavailable, the batch remains pending locally and conversation capture continues. A retry reuses the same pending batch rather than producing overlapping transcript ranges.

The cursor is the commit point for remote backup. A crash after remote verification but before local housekeeping is repaired on the next backup pass.

The intended end-to-end path is:

`provider -> local capture spool -> Universal Conversation Capture -> local SQLite evidence -> verified projections -> transcript batch outbox -> Google Drive readback verification -> backup cursor commit`

This batch lane is separate from full-vault disaster recovery. HumanOS already has authenticated portable-vault backups and AES-256-GCM encrypted vault backups. Those encrypted vault snapshots should also be copied off-device periodically so recovery does not depend only on transcript files.

## Lane C — checkpoint intelligence

This lane is separate and optional. It may run at explicit checkpoints such as session end, every N completed turns, or an owner-requested checkpoint.

Checkpoint workers may create summaries, decisions, tasks, discoveries, contradictions, course evidence, or other derived records. Derived records must cite the underlying Life Notebook transcript and never replace it.

Because the expensive intelligence lane does not run on every message, transcript durability does not require repeated LLM token use.

## Identity and idempotency

The host supplies a `source`, stable `conversation_id`, and stable `turn_id`. The local transport converts provider identifiers into keyed local identities before persistent storage. The Life Notebook then derives its own vault-keyed local transaction identity. Raw provider identifiers are not copied into content-light audit events.

Retries with the same IDs and exact text are idempotent. A retry with different text fails closed rather than changing preserved evidence.

Different sources are isolated: the same conversation and turn IDs from ChatGPT and Claude resolve to different local identities.

## Internal compatibility name

Runtime 0.1 already recognizes the internal phase `EXTERNAL_CAPTURE_PENDING`. That name stays for compatibility. In this context, "external" only means "outside the local HumanOS runtime." The user-facing feature is **Universal Conversation Capture**.

## Transport boundary

`conversation_capture.py` and `transcript_backup.py` remain transport-independent. `conversation_transport.py` is the local ingress boundary. Provider-specific adapters should be thin and replaceable.

A backup transport adapter needs to:

1. obtain the pending batch artifact paths;
2. upload each artifact to the configured private destination;
3. read the remote bytes back;
4. calculate SHA-256 from the readback bytes;
5. call `confirm_upload(...)` with the remote file IDs and verified hashes.

Historical exports can use an import/reconciliation adapter. Other desktop providers can reuse the same local spool/native-host boundary without changing the Life Notebook format.

## Privacy and repository boundary

The public GitHub repository contains code, tests, and documentation only. It must not contain Life Notebook transcript payloads, Google Drive folder IDs, access tokens, OAuth credentials, capture secrets, backup passphrases, or other private runtime configuration.

Transcript batches and encrypted vault snapshots belong in the owner's private local/Drive storage.

## Promotion gate

Do not merge this feature based only on code review. Promotion requires:

- exact whitespace/Unicode round-trip tests;
- idempotent retry tests;
- conflicting retry fail-closed tests;
- crash-window recovery tests;
- source-isolation tests;
- local spool / Notebook writer-lock recovery tests;
- transcript-batch cursor and remote-hash fail-closed tests;
- full HumanOS regression suite on macOS and Linux;
- a live ChatGPT desktop adapter test proving one human message and one assistant message appear exactly once in the Life Notebook and survive restart/readback;
- a live Drive adapter test proving one prepared batch is uploaded, read back byte-for-byte, confirmed locally, and not duplicated on retry.
