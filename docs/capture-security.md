# HumanOS Capture Security Model

Status: experimental. Real private conversations are **not approved for remote capture yet**.

## Security goal

Preserve exact conversation evidence without making a cloud database or broad
runtime credential equivalent to the HumanOS Life Notebook.

## Production-intended path

```text
provider / ChatGPT tool call
        |
        | plaintext exists transiently at the capture gateway
        v
HumanOS Capture MCP gateway (stateless)
        |
        | validate, then encrypt with owner public key
        v
X25519 + HKDF-SHA256 + AES-256-GCM envelope
        |
        v
least-privilege encrypted append function
        |
        v
remote PostgreSQL relay (ciphertext mailbox only)
        |
        v
owner-controlled local HumanOS reader
        |
        | private X25519 key exists here only
        v
decrypt + authenticate + verify ciphertext digest
        |
        v
local mirror -> CaptureSpool -> Life Notebook
```

The remote relay is not canonical memory. The Life Notebook remains the
owner-controlled source of truth.

## What each system is allowed to know

### Provider / ChatGPT

Already knows the conversation because it is the conversation provider.

### Render / remote MCP gateway

May see the incoming message transiently in process memory because it receives
the tool request. It receives only:

- a dedicated encrypted-writer database credential;
- the HumanOS recipient **public** key;
- a relay-token HMAC secret used for opaque retry/conflict tokens.

It must never receive the HumanOS recipient private key, a local reader
credential, Life Notebook files, or a general database owner credential.
Application code must not intentionally log request bodies or transcript text.

### Neon / PostgreSQL relay

Production encrypted storage contains ciphertext envelopes plus minimum routing
and integrity metadata. It does not need plaintext transcript text, raw
conversation IDs, role labels, or provider turn IDs. A database-only disclosure
therefore should not reveal transcript plaintext.

### Local HumanOS

The owner-controlled device holds the recipient private key and the separate
reader credential. Decryption occurs locally before events enter the private
local mirror and CaptureSpool.

## Cryptographic envelope

Each event uses a fresh ephemeral X25519 key. X25519 shared-secret material is
expanded with HKDF-SHA256 into a 256-bit AES key. AES-256-GCM provides
confidentiality and authenticated integrity. The envelope metadata is bound as
additional authenticated data (AAD), so tampering fails closed.

Encryption is randomized. Re-encrypting the same event produces different
ciphertext. For remote retry semantics, keyed HMAC tokens provide:

- an opaque idempotency token derived from the logical event id;
- an opaque conflict token derived from the exact canonical plaintext event.

The database can reconcile safe retries without storing a naked plaintext hash.

## Least-privilege database identities

Do not use a provider-created owner/admin role as an application credential.
HumanOS defines separate NOLOGIN capability roles:

- `humanos_capture_encrypted_writer_limited` can execute only
  `humanos_append_capture_envelope(jsonb)`;
- `humanos_capture_encrypted_reader_limited` can execute only
  `humanos_capture_envelopes_after(bigint, integer)`.

The writer cannot SELECT the table, use the reader function, call the plaintext
bakeoff function, UPDATE, or DELETE. The reader cannot append or call plaintext
reader functions. Production LOGIN identities should receive only the matching
capability and should be independently rotatable.

CI checks *effective* PostgreSQL privileges with `has_function_privilege` and
`has_table_privilege`; it does not trust the appearance of GRANT statements.

## Local key rule

Generate the capture recipient keypair on the owner device:

```bash
python capture_keygen.py
```

The command prints only the public key and key id. The private key is stored as
an owner-only local file and refuses silent overwrite. Never paste the private
key into ChatGPT or upload it to Render, Neon, GitHub, Drive, CI, issue trackers,
or logs.

The public key is intentionally distributable and can be configured on the
remote gateway.

## Secrets and separation

Production should use four separately rotatable trust items:

1. remote encrypted-writer database credential — Render only;
2. remote relay-token HMAC secret — Render only;
3. owner recipient private key — local HumanOS only;
4. remote encrypted-reader database credential — local HumanOS only.

A single leaked writer credential must not grant read/decrypt/delete authority.
A database-only leak must not reveal plaintext. A public-key leak is not a
confidentiality failure.

## Transport and deployment requirements

- TLS must be required for gateway and PostgreSQL connections.
- Prefer strict certificate/hostname verification where supported.
- Do not put secrets in Git or build arguments.
- Disable application request-body logging for the capture endpoint.
- Use a dedicated service/environment for capture.
- Apply rate limits and endpoint authentication before production use.
- Rotate credentials after suspected exposure.
- Keep staging and production credentials separate.
- Keep Google Drive out of the live transaction path; use it only for approved
  encrypted backups or distilled exports.

## Important limitation: not true end-to-end encryption from ChatGPT to Mac

The current MCP architecture encrypts at the HumanOS gateway. Therefore the
remote gateway necessarily sees the message transiently before encryption. This
is still a major improvement over storing plaintext remotely, but Render remains
a trusted processing boundary.

True provider-to-device end-to-end encryption would require a supported capture
source that encrypts before the message reaches the remote gateway. HumanOS must
not claim that property until such a source actually exists and is tested.

## Production promotion gate

Do not send real private conversations until all of the following are evidenced:

- cryptographic unit tests pass;
- encrypted PostgreSQL round-trip passes;
- role-boundary tests pass;
- full HumanOS regression suite passes;
- owner-local key generation is completed without exposing the private key;
- remote database uses dedicated encrypted writer/reader identities;
- raw database inspection proves no transcript plaintext is stored;
- duplicate and conflicting retries behave correctly;
- restart/recovery produces no duplication or loss;
- gateway authentication, rate limiting, and logging policy are configured;
- owner explicitly approves production capture.
