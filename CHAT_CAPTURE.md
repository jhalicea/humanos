# HumanOS host-level ChatGPT capture

This component captures exact finalized text visibly rendered as USER or ASSISTANT
turns on `https://chatgpt.com/`. It is local-first, provider-specific only at
the observation adapter, and uses no model calls.

## Data path

1. The content script observes visible ChatGPT message nodes.
2. USER text is captured when visible. ASSISTANT text is captured only after it
   is stable and generation has stopped.
3. The extension service worker accepts events only from a ChatGPT tab.
4. Chrome native messaging delivers the record to `chat_capture_host.py`.
5. `capture_ledger.py` validates it and commits it to the shared SQLite WAL at
   `HumanOS_Vault/runtime/capture-ledger.sqlite3`.
6. Records remain `PENDING`. Nothing in this interceptor uploads, summarizes,
   exposes evidence to a model, or deletes evidence.

The pending WAL is intentionally separate from the single-writer Life Notebook.
A later deterministic importer can append verified records into the canonical
Notebook without allowing the browser process to contend for Notebook ownership.

## Install on macOS Chrome

Check out the branch, then open `chrome://extensions`, enable Developer mode,
choose **Load unpacked**, and select `chat-capture-extension/`. Copy the
extension ID shown by Chrome and run:

```sh
cd <HUMANOS_ROOT>
python3 install_chat_capture.py <EXTENSION_ID>
```

Reload the extension and reload each open ChatGPT tab. Installation of the
unpacked extension is the owner's explicit consent to capture visible turns.
Removing the extension stops capture.

## Verify

After sending a test turn, run:

```sh
cd <HUMANOS_ROOT>
python3 - <<'PY'
import sqlite3
from pathlib import Path
path = Path("HumanOS_Vault/runtime/capture-ledger.sqlite3")
db = sqlite3.connect(path)
print(db.execute(
    "SELECT message_id,chat_id,role,length(text),state "
    "FROM pending_turns ORDER BY rowid DESC LIMIT 5"
).fetchall())
PY
```

The verifier prints metadata and length, not transcript text. A repeated
identical message ID is idempotent. The same ID with different evidence is
rejected and recorded in `capture_conflicts`.

## Boundaries

- Chrome desktop only; this cannot intercept the ChatGPT iOS/macOS native app or
  modify OpenAI's server-side host.
- Only visible USER/ASSISTANT message nodes are captured. Hidden reasoning,
  credentials, cookies, tool internals, and deleted/unavailable messages are not.
- Capture timestamps are observation times. ChatGPT does not expose an
  authoritative per-message creation timestamp through the page contract.
- DOM changes at ChatGPT can break capture. Failure is visible as absence from
  the local pending ledger; it must never be represented as captured.
- Compaction is not part of this slice and remains forbidden until exact Drive
  readback verification and a durable receipt exist.
