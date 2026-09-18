# HOS-CTX-007 — Trusted Mirror Timezone Source

Status: PROMOTED / POST-PROMOTION VERIFIED  
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

## Promotion evidence

- Verified candidate: `4d539bf2962cfb0dffdf658b275762ec1c6a4153`
- Pull request: #74
- Canonical merge: `44caa5b0cb9c81fb1f08f350869aebad55cad38a`
- Post-promotion regression run `35300420153`: SUCCESS
- Post-promotion encrypted-backup run `35300420082`: SUCCESS
- Post-promotion Pages run `35300419751`: SUCCESS
- No release or tag created.
