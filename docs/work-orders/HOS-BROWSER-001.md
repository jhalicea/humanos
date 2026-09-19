# HOS-BROWSER-001 — Browser Bridge Activation & Governed Web Access

Status: PROMOTED / LOCAL PAIRING PENDING
Workspace: `WS-HUMANOS`
Project: Capabilities and Tooling
Workstream: `HOS-BROWSER-001`
Branch: `feature/browser-activation-v1`
Baseline: `runtime-0.1` at `b45f4eb94be026660ed3415f3213d132bda7955d`
Privacy class: INTERNAL

## Routing decision

`CONTINUE HOS-BROWSER-001`.

The public Context Registry already contains the Browser Broker and Tools workstream.
Historical branches `feature/browser-broker` and `feature/browser-tools` are strict
ancestors of the canonical runtime. This slice reconciles that stale UNKNOWN metadata
and extends the existing implementation; it does not create a competing browser system.

## Objective

Make the already-merged HumanOS Browser Bridge operably installable and truthfully
usable by local Mirror on macOS Chromium-family browsers while preserving HumanOS
owner authority, selected-tab control, least privilege, auditability, and explicit
approval for browser side effects.

## Baseline findings

1. Browser broker, native host, extension, and Mirror tool integration already exist.
2. The extension manifest lacks Chrome's required `nativeMessaging` permission.
3. The registered native host executable requires `--socket` and `--secret`, but
   Chromium native-messaging manifests supply an executable path, not custom installer
   arguments. A local launcher/configuration layer is required.
4. The tracked `config.json` has no browser block; local secrets/paths must not be
   added to Git.
5. The permission scope currently grants `browser_inspect` but does not provide an
   effectful-browser authorization path for navigate/click/type after scope validation.
6. Natural requests such as "search the web" or "browse the internet" do not currently
   establish browser scope unless the literal word "browser" appears.
7. Runtime capability truthfulness now distinguishes registered from configured state;
   this slice must preserve that behavior.

## Scope

1. Add the extension `nativeMessaging` permission.
2. Add a deterministic local browser setup module and CLI commands that:
   - create an owner-only HumanOS browser control directory outside the repository;
   - create a 32-byte owner-only HMAC secret;
   - create an executable native-host launcher that supplies socket/secret arguments;
   - install a native-messaging host manifest for an explicitly selected supported
     Chromium-family browser and extension ID;
   - create a local runtime browser config outside Git;
   - report setup/readiness diagnostics without exposing secret material.
3. Make the default runtime discover the local browser config when no explicit browser
   config is supplied.
4. Construct short-lived Browser Broker run envelopes at runtime rather than persisting
   an expiring envelope in the repository.
5. Extend browser permission derivation so explicit web/browser/internet requests may
   use browser tools, while navigate/click/type still require exact interactive approval.
6. Preserve the unconfigured state: if setup is absent, browser tools remain unavailable
   to the model and Mirror explains the next action.
7. Add isolated tests for setup artifacts, modes, validation, runtime config loading,
   permission boundaries, and backward compatibility.
8. Update public browser documentation and reconcile the context registry metadata.

## Out of scope

- Silent browser extension installation or modifying a browser profile database.
- Browser credential/cookie extraction.
- Arbitrary JavaScript, DevTools, shell access, or a general network proxy.
- Disabling per-action human approval for effectful browser actions.
- Cloud browser control.
- Safari/Firefox support in this slice.
- Search-engine ranking or a new public-web search backend.
- Cross-workspace/private-data transfer.
- Broadening host allowlists without explicit local owner configuration.
- BodyFixOS.
- Replacing the HumanOS Context Router, Work Order contract, or Browser Broker.

## Responsibility routing

- **Jon / Owner:** grants implementation/promotion authority; performs the unavoidable
  browser UI act of loading/selecting the unpacked extension and supplies its extension
  ID to the local setup command.
- **HumanOS Context Router:** selects WS-HUMANOS / HOS-BROWSER-001 only; it grants no
  execution authority.
- **Work Order / SDLC:** bounds scope, acceptance criteria, rollback, and evidence.
- **Local setup module:** writes owner-controlled local pairing/config artifacts only.
- **BrowserBroker:** enforces immutable run scope, host/capability/action/byte/time
  budgets, HMAC transport, audit records, and stop state.
- **Native host:** authenticated transport between broker Unix socket and extension
  stdio; no policy authority.
- **Browser extension:** operates only the explicitly selected tab; no policy authority.
- **Mirror / Agent:** may request only runtime-ready tools under human-derived task scope.
- **HumanOS runtime approval gate:** separately approves browser side effects.
- **CI/tests:** executable evidence only; they do not grant promotion authority.

## Security requirements

- No secret bytes, local home paths, Notebook content, browser data, or credentials in Git.
- Local control/config directories are owner-only; secret/config/manifest/launcher files
  use restrictive modes where the platform supports them.
- Extension IDs and browser targets are strictly validated.
- Native host manifest contains one exact allowed extension origin; no wildcard.
- Local runtime config contains paths and policy metadata but never secret contents.
- Browser run envelope is short-lived and generated by trusted host code, never the model.
- Host allowlist remains explicit and bounded.
- Side-effecting browser actions remain approval-gated.
- Unconfigured/invalid local setup fails closed.
- Existing static registry validation remains backward compatible.
- Setup/status commands must not open the active Life Notebook or run a model.

## Acceptance tests

- Extension manifest contains `nativeMessaging`.
- Setup rejects malformed extension IDs, unsupported browser targets, invalid hosts, and
  unsafe local paths.
- Setup creates secret/config/launcher/manifest with expected contents and restrictive
  permissions in an isolated temporary HOME.
- Generated native-host launcher supplies exact socket and secret arguments to the
  canonical `browser_native_host.py`.
- Local config loader validates structure and builds a future short-lived envelope.
- No local setup artifact is created beneath the repository in tests.
- Default runtime remains browser-unconfigured when local config is absent.
- Browser tools are not advertised to the model when setup is absent.
- Explicit browser/web/internet intent grants browser scope; unrelated conversation does not.
- Navigate/click/type require both browser scope and the existing interactive approval gate.
- Existing browser broker tests remain green.
- Full regression matrix remains green on Ubuntu/macOS × Python 3.11/3.13.
- Encrypted-backup/full-suite matrix remains green.
- Exact candidate diff contains no local paths, secrets, or private Notebook data.

## External verification note

Chrome's current native-messaging documentation states that the browser launches the
host executable from the manifest `path`, communicates over stdin/stdout, requires
`nativeMessaging` permission, requires exact `allowed_origins`, and on macOS uses
browser-specific NativeMessagingHosts locations. The implementation is designed to
those platform constraints; repository tests remain the implementation evidence.

## Rollback

Revert the candidate/merge commit. The local setup command is create/replace-only for
HumanOS-owned browser-control artifacts and does not mutate Life Notebook evidence.
A local uninstall/status path must identify/remove only the HumanOS native-host manifest
and HumanOS browser control directory, never browser profiles or user browsing data.

## Known unknowns

- Exact browser extension ID is assigned by the owner's local browser profile unless a
  future deterministic extension-key mechanism is deliberately adopted.
- Chromium-family native-host search paths vary by browser/version; this slice supports
  explicit known targets and reports the selected path.
- Real end-to-end browser readiness requires local post-promotion pairing/readback on
  Jon's Mac and cannot be proven by repository CI alone.

## Provenance

- Owner instruction: "do it" in the current conversation, 2026-09-19.
- Router/index: GitHub issue #67 and `config/context_registry.public.json`.
- Foundation workflow: `docs/foundation/WORKFLOW_STANDARD.md`.
- Repository agreement: `AGENTS.md`.
- Historical browser implementation: PR #10 browser broker and PR #11 browser tools.
- Baseline recovery/capability-truth repair: `b45f4eb94be026660ed3415f3213d132bda7955d`.

## Verification evidence

- Verified candidate head: `b1ceadb7fe2d0165b98cce2f8463e932f72049c3`.
- HumanOS regression workflow run `35454724814`: SUCCESS across Ubuntu 24.04/macOS 15 × Python 3.11/3.13.
- Representative full regression count: 528 tests, 8 skipped, no failures.
- Encrypted-backup/full-suite workflow run `35454724812`: SUCCESS.
- Exact candidate diff reviewed against `runtime-0.1@b45f4eb94be026660ed3415f3213d132bda7955d`.
- Diff contains the intended browser activation/runtime/docs/tests/registry slice only; no local owner paths, credentials, Notebook content, or secret bytes were found.
- Chrome native-messaging behavior was cross-checked against current Chrome documentation: exact allowed origins, nativeMessaging permission, absolute macOS/Linux host path, stdin/stdout framing, and browser-specific NativeMessagingHosts locations.
- Promotion PR #91 merged at `02869089cd336ffac17751a771bd61adcf21229d`.
- Real browser end-to-end readiness remains intentionally unverified until the owner pulls the promoted commit and completes the browser UI pairing/readback on the Mac.

## Done condition

The activation/configuration path is implemented and repository-verified, full CI is green,
the exact diff has been reviewed, rollback is preserved, and owner authorization to proceed
was given by "do it" in the current conversation. Repository promotion may proceed. Local
browser readiness remains a separate post-promotion verification step because GitHub cannot
load an extension or click a browser toolbar button on the owner's Mac.

## Next action

Promote the verified candidate, then pull `runtime-0.1` on the owner Mac, run
`humanos --browser-setup`, load the unpacked HumanOS extension once, select a tab,
and verify with `humanos --browser-status` plus one bounded browser action.
