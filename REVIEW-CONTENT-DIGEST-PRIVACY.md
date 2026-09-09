# Content digest privacy hardening

## Problem
HumanOS Runtime 0.1 stored naked SHA-256 hashes of exact human/model text in Notebook integrity metadata and delivery audit events. Predictable plaintext could therefore be confirmed from copied metadata without access to the original payload.

## Change
New Notebook content integrity values use HMAC-SHA256 with a random 32-byte per-vault key stored at `runtime/integrity.key` with owner-only permissions. New digest values are prefixed `hmac-sha256:`. The key is never projected into page/index/binding artifacts.

Legacy transcript rows and in-flight delivery state containing the previous naked SHA-256 format remain verifiable so the existing local vault does not require destructive rewriting. New delivery audit events use `content_digest` rather than a naked `sha256` value. Loss or replacement of the vault integrity key makes new protected rows fail verification closed.

## Verification
`tests/test_content_digest_privacy.py` covers keyed-not-plain digests, cross-vault unlinkability, key permissions/non-projection, legacy transcript compatibility, wrong-key fail-closed behavior, protected delivery-event digests, and legacy in-flight delivery compatibility.

The full repository regression suite is required on macOS and Linux under Python 3.11 and 3.13 before merge.

## Scope
This does not encrypt transcript plaintext at rest and does not rename the legacy SQLite `sha256` column. Those are separate migrations. It removes the plaintext confirmation-oracle behavior for newly generated integrity/audit digests while preserving current Notebook evidence and recovery semantics.
