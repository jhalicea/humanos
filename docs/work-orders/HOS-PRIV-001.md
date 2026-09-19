# HOS-PRIV-001 — FRIEND Outbound Privacy Firewall

Status: CANDIDATE / OWNER-APPROVED IMPLEMENTATION  
Branch: `feature/friend-privacy-firewall-v1`  
Baseline: `bde51b0f370f64301fc6752cc03babd5c5afc9e1` (`runtime-0.1`)

## Objective

Add a deterministic privacy/sanitization firewall between validated FRIEND packets and any future external/cloud dispatcher.

## Scope

1. Validate FRIEND packets before privacy processing.
2. Keep LOCAL execution content unchanged after validation.
3. Allow EXTERNAL export only for PUBLIC and INTERNAL FRIEND packets.
4. Fail closed for CONFIDENTIAL, RESTRICTED, and LOCAL_ONLY packets.
5. Redact deterministic high-risk content from external packets:
   - private-key blocks;
   - known token formats;
   - labeled API keys/tokens/passwords/secrets;
   - email addresses;
   - US SSN format;
   - common US phone format;
   - macOS/Linux home paths;
   - Windows user-home paths.
6. Preserve relative repository paths needed for bounded collaboration.
7. Detect authority-bearing language and record it as evidence while preserving the contract rule that packet content remains DATA_ONLY.
8. Return sanitization findings separately from the FRIEND packet; do not add undeclared fields to the strict FRIEND schema.
9. Do not mutate the original packet.
10. Run focused tests plus full regression and encrypted-backup matrices.

## Out of scope

- Automatic cloud dispatch.
- Automatic provider/model selection.
- Work Order compilation.
- Semantic/LLM-based PII detection.
- Client-specific declassification policy.
- Cross-dock routing.
- Existing Context Router or swarm modification.
- BodyFixOS.

## Security requirements

- Sensitive privacy classes cannot be silently downgraded for external use.
- Invalid FRIEND packets fail before sanitization.
- Secrets and private keys are never preserved in an externally exportable copy when deterministically detectable.
- Local absolute home paths are redacted from external copies.
- Relative repo paths remain intact.
- Authority-like text remains DATA_ONLY and cannot elevate packet authority.
- Sanitization grants no execution, filesystem, network, model, merge, deployment, or declassification authority.
- Any residual deterministically recognized hard secret blocks export.

## Acceptance tests

- INTERNAL external packet with no sensitive content passes unchanged.
- LOCAL processing preserves validated content, including CONFIDENTIAL content.
- CONFIDENTIAL/RESTRICTED/LOCAL_ONLY external export fails closed.
- Deterministic secret, PII-like, and local-path patterns are redacted.
- Relative repo paths survive.
- Authority-bearing language is surfaced in findings without being elevated.
- Original packet remains unchanged.
- Invalid FRIEND packet fails before sanitization.
- Existing regression and encrypted-backup matrices remain green.

## Rollback

Revert the candidate branch. No Notebook/runtime data migration is part of this slice.

## Provenance

- Parent canonical commit: `bde51b0f370f64301fc6752cc03babd5c5afc9e1`.
- Parent promoted foundation: HOS-EXEC-CONTRACTS-001.
- Existing HumanOS private-context design already follows minimum-disclosure and private-metadata host-side principles.

## Done condition

The external FRIEND boundary deterministically rejects sensitive privacy classes, removes supported sensitive patterns from eligible packets, preserves contract validity, and passes the full CI matrices without dispatcher integration.

## Next candidate

Minimal Work Order compiler, subject to a new Jon Gate.
