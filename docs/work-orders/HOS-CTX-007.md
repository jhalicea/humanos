# HOS-CTX-007 — Trusted Mirror Timezone Source

Status: REVIEW  
Branch: `feature/context-trusted-timezone-source-v1`  
Parent: extends promoted `HOS-CTX-006`

## Outcome

Wire CTX-006's timezone-safe temporal primitive into Mirror using an explicit owner/runtime configuration source.

Mirror reads `HUMANOS_TIMEZONE`; absent configuration defaults to UTC. The value is passed into verified Notebook historical resolution. Invalid IANA timezone values are handled by CTX-006's safe UTC fallback.

## Trust boundary

The runtime MUST NOT derive timezone from IP address, geolocation, device location, model output, user-message inference, or hosted-provider metadata. Environment configuration is host-side and explicit.

## Acceptance

- `inspect_history` accepts and forwards an explicit timezone without changing canonical Notebook evidence.
- Mirror supplies only the explicit host setting, defaulting to UTC.
- Existing routing/session/history behavior remains compatible.
- Full regression and encrypted-backup matrices pass.
- Promotion remains owner-gated.

## Deferred

A future owner/workspace settings service may replace the environment variable while preserving this same explicit trust boundary.
