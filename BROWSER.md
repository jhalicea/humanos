# HumanOS Browser Bridge

Workstream: `HOS-BROWSER-001`  
Status: activation candidate on `feature/browser-activation-v1`

HumanOS has a local Chromium-family browser capability with a narrow trust
boundary. Mirror can inspect and search through the tab that **you explicitly
select**, and can navigate, click, or type only through the governed Browser
Broker and HumanOS approval path.

The model never receives browser credentials, cookies, extension-management
authority, arbitrary JavaScript, DevTools, shell access, or a general network
proxy.

## Responsibility boundary

- **Owner:** installs/loads the unpacked extension once, selects the active tab,
  approves browser side effects, and controls promotion.
- **Mirror/model:** proposes only registered/runtime-ready browser tools.
- **HumanOS task scope:** derives whether the human actually asked for web/browser
  access; unrelated conversation receives no browser authority.
- **BrowserBroker:** enforces host allowlist, capabilities, time/action/byte limits,
  HMAC transport, stop state, and the independent audit ledger.
- **Native host:** transports authenticated broker requests to the extension over
  Chrome native messaging; it does not decide policy.
- **Extension:** acts only on the tab selected through its toolbar button.

## What is implemented

The extension lives at `browser-extension/`. It is Manifest V3, declares
`nativeMessaging`, and carries a pinned development public key so its unpacked
extension ID remains stable:

`hdmlcfjlepjknagpdebdlnbdlnjoijbn`

`browser_setup.py` creates owner-only pairing state outside the repository.
By default that state is:

`~/.humanos/browser/`

It contains:

- `runtime.json` — paths, allowlisted hosts, budgets, and search-provider metadata;
- `secret.bin` — 32-byte HMAC secret, mode 0600;
- `native-host` — owner-only launcher that supplies the canonical native host with
  its socket/secret arguments;
- `state/` — BrowserBroker audit/stop state;
- `bridge.sock` — present only while the extension/native host connection is alive.

The secret contents are never written to `config.json`, Git, the Life Notebook,
model prompts, or the extension.

## Setup on Jon's Mac

First update to the verified HumanOS release that contains this workstream.

Then run:

```bash
humanos --browser-setup
```

The setup command detects Brave, Chrome, or Chromium when possible. You can select
one explicitly:

```bash
humanos --browser-setup --browser-target brave
```

The default governed search provider is DuckDuckGo. To choose Google instead:

```bash
humanos --browser-setup --browser-target brave --browser-search-provider google
```

Additional HTTPS hosts can be authorized locally at setup time:

```bash
humanos --browser-setup --browser-target brave \
  --browser-host github.com \
  --browser-host developer.chrome.com
```

Host entries are DNS names only—no URL paths, wildcards, credentials, ports, or
schemes.

### Load the extension

In the selected Chromium-family browser:

1. Open the browser's Extensions management page.
2. Enable **Developer mode**.
3. Choose **Load unpacked**.
4. Select the HumanOS repository's `browser-extension/` directory.
5. Verify the extension ID is:
   `hdmlcfjlepjknagpdebdlnbdlnjoijbn`.
6. Pin the HumanOS Browser Bridge extension if convenient.
7. On the tab you want HumanOS to control, click the HumanOS Browser Bridge toolbar
   button. That tab becomes the explicit selected-tab boundary.

No browser profile database, cookie store, history database, or credentials are
read or modified by the setup command.

## Verify setup

Run:

```bash
humanos --browser-status
```

The status response reports only non-secret setup facts such as the extension path,
extension ID, selected browser target, allowlisted hosts, manifest/launcher/secret
readiness, and whether the native socket is currently present.

A configured broker is reported as configured but connection-unverified until an
actual bounded browser action succeeds. HumanOS must not claim the extension/tab is
connected merely because local configuration files exist.

## Use from Mirror

After setup and selecting a tab, ordinary explicit web requests may invoke browser
tools. Examples:

- “search the web for the Chrome native messaging documentation”
- “browse the internet for HumanOS references”
- “inspect the browser tab”
- “open this allowlisted URL in the browser”

The model-facing registry contains these governed browser tools:

- `browser_search`
- `browser_inspect`
- `browser_navigate`
- `browser_click`
- `browser_type`

`browser_search` navigates the selected tab to the owner-configured search provider
and then inspects bounded page text.

`browser_inspect` is read-only. Search, navigation, click, and type are effectful
browser actions and require HumanOS's explicit approval path. A saved permission
scope never becomes broader merely because HumanOS was upgraded.

## Native messaging architecture

Chrome/Chromium native messaging launches the executable declared in a registered
native-host manifest and communicates over stdin/stdout. The browser supplies the
extension origin to that executable. HumanOS therefore generates an owner-local
launcher because the canonical `browser_native_host.py` also needs HumanOS-specific
socket and secret arguments.

The generated native-host manifest allows exactly:

`chrome-extension://hdmlcfjlepjknagpdebdlnbdlnjoijbn/`

Wildcards are never used.

On macOS, Chrome/Chromium use browser-specific NativeMessagingHosts directories.
Current Brave source intentionally points its macOS native-messaging lookup to
Chrome's standard user NativeMessagingHosts location, and HumanOS setup follows that
behavior.

## Broker security

The trusted runtime creates a short-lived envelope for each HumanOS process. It
contains the run ID, owner authorization label, expiry, explicit hosts, browser
capabilities, and action/byte budgets. The model cannot construct or widen that
envelope.

Broker requests are HMAC-authenticated across an owner-only Unix socket. The
BrowserBroker validates the request before transport and records a keyed audit event
before and after each action. An extension-side `ok:false` response remains a failed
tool action; transport success is never treated as browser-action success.

Page inspection is bounded. The extension never evaluates model-provided JavaScript.
The special `tab_id: 0` value means only “the tab selected by the human in the
HumanOS extension”; nonzero IDs must match that selected tab exactly.

## Removal

To remove only HumanOS-owned Browser Bridge pairing artifacts:

```bash
humanos --browser-uninstall
```

This removes the HumanOS native-host manifest and `~/.humanos/browser/`. It does
not delete the browser profile, browsing history, cookies, saved passwords, or other
native-host manifests. Remove the unpacked extension separately from the browser UI
if desired.

## Failure states

HumanOS distinguishes registration from actual runtime readiness:

`REGISTERED -> CONFIGURED -> CONNECTION VERIFIED BY ACTION`

If setup is missing, Mirror reports `REGISTERED_NOT_CONFIGURED` and does not advertise
browser tools to the model as executable. If setup exists but the extension/native
host is not connected or no tab is selected, the browser action fails closed with the
actual transport/extension error.

## Platform references

Implementation was checked against Chrome's current Native Messaging documentation:
https://developer.chrome.com/docs/extensions/develop/concepts/native-messaging

The pinned extension key follows Chrome's development manifest key mechanism:
https://developer.chrome.com/docs/extensions/reference/manifest/key

Brave's current macOS native-messaging override is visible in:
https://github.com/brave/brave-core/blob/master/app/brave_main_delegate.cc

Repository tests and local post-promotion readback, not these documents alone,
establish HumanOS implementation truth.
