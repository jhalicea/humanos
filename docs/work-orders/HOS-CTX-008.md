# HOS-CTX-008 — Temporal Resolution Hardening

Status: REVIEW  
Branch: `feature/context-temporal-resolution-hardening-v1`  
Parent: extends promoted `HOS-CTX-007`  
Baseline: `1388a3bb4ceb7736655315e6ee052bc856bb1089`

## Outcome

Close three temporal-resolution integration gaps before the Context Engine expands into richer entity/relationship context.

1. Historical continuation phrases using `today`, `most recent`, or `latest` must enter verified Notebook recovery rather than silently fall through to ordinary model routing.
2. Archived/superseded workstreams must be removed before temporal ranking so a newer terminal record cannot hide the newest eligible workstream.
3. Naive Notebook timestamps must never inherit the host operating system timezone. If a timestamp has no timezone offset, temporal projection falls back to the canonical stored date.

## Security / trust boundary

- Notebook verification remains mandatory.
- No model recollection becomes authority.
- No IP, geolocation, device location, or inferred timezone is introduced.
- No branch/tool/merge authority is added.
- Raw transaction identifiers remain host-side.
- Canonical Notebook evidence is not rewritten by temporal interpretation.

## Acceptance

- `continue the work today`, `continue the most recent work`, and `resume the latest work` are recognized as explicit historical-continuation candidates.
- Most-recent recovery chooses the newest eligible verified workstream, skipping archived/superseded records.
- Naive timestamps use canonical `created_date` rather than the host timezone.
- Existing CTX-003 through CTX-007 routing behavior remains compatible.
- Full regression and encrypted-backup matrices pass.
- Promotion remains owner-gated.

## Deferred

Entity/relationship graph work remains a later Context Engine slice. This slice is correctness hardening only.
