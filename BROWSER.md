# HumanOS Browser Bridge

Status: HOS-BROWSER-001 activation candidate

HumanOS has a governed local browser capability for Chromium-family browsers. The
browser bridge is a local capability adapter: Mirror may inspect the tab selected
by the owner and may request bounded browser actions, but the model never receives
browser cookies, credentials, extension-management authority, arbitrary JavaScript,
DevTools, shell access, or a general network proxy.

## Responsibility boundary

- **Owner:** loads the bundled unpacked extension once, selects the tab HumanOS may
  operate, approves browser side effects, and chooses any additional allowed hosts.
- **HumanOS runtime:** derives browser authority from the current human request and
  presents exact approval prompts for search/navigation/click/type.
- **BrowserBroker:** enforces run expiry, capability, hostname, action and byte
  budgets; records an independent audit chain; and authenticates native-host traffic.
- **Native host:** authenticated transport only. It does not decide policy.
- **Extension:** operates only the tab the owner selected with its toolbar button.
- **Mirror/model:** proposes actions only from runtime-ready registered tools. It
  cannot configure the bridge or widen the allowlist itself.

The bundled extension has a pinned development key so its HumanOS extension ID is
stable:

`hdmlcfjlepjknagpdebdlnbdlnjoijbn`

Only the public extension key is in Git. The browser-control HMAC secret is generated
locally and never committed.

## Install / pair on the local computer

First update the HumanOS checkout to a release that contains HOS-BROWSER-001. Then,
from the repository, run:

```bash
humanos --browser-setup
```

HumanOS detects Brave, Google Chrome, or Chromium when possible. You can select one:

```bash
humanos --browser-setup --browser-target brave
humanos --browser-setup --browser-target chrome
humanos --browser-setup --browser-target chromium
```

The setup command does **not** open the Life Notebook or invoke a model. It creates
HumanOS-owned pairing state under `~/.humanos/browser/`, installs the matching
user-level native-messaging host manifest, and writes only local paths/policy to the
local runtime config. The 32-byte authentication secret remains in an owner-only
local file.

The default search provider is DuckDuckGo. Google is optional:

```bash
humanos --browser-setup --browser-search-provider google
```

Navigation is host-allowlisted. The selected search provider is automatically added;
add other sites explicitly and repeat the option for each hostname:

```bash
humanos --browser-setup \
  --browser-target brave \
  --browser-host github.com \
  --browser-host developer.chrome.com
```

Running setup again replaces the configured host list while preserving the existing
HumanOS browser authentication secret.

### Load the extension

In the selected Chromium-family browser:

1. Open the browser's extensions management page.
2. Enable Developer mode.
3. Choose **Load unpacked**.
4. Select the HumanOS repository's `browser-extension/` directory.
5. Pin the **HumanOS Browser Bridge** toolbar action if convenient.

No browser profile database is edited by the setup command.

### Select the controlled tab

Open the page/tab you want HumanOS to use and click the HumanOS Browser Bridge toolbar
button. That tab becomes the selected tab. A browser request fails closed when no tab
has been selected.

HumanOS uses `tab_id: 0` internally as a sentinel meaning **the tab selected by the
owner**. A non-zero tab id is accepted only when it exactly matches the selected tab.

## Readiness

Check pairing without opening the Notebook:

```bash
humanos --browser-status
```

Important fields:

- `configured`: local HumanOS pairing/config exists.
- `manifest_installed`: the selected browser has the HumanOS native-host manifest.
- `launcher_ready`: the owner-only native-host launcher is present.
- `secret_ready`: the local 32-byte secret exists with restrictive permissions.
- `socket_present`: the browser has launched the native host and its Unix socket is
  currently present. This normally becomes true after the extension/native connection
  is active.
- `selected_tab_required`: always true.

A configured bridge is not claimed connected until a real browser action succeeds.

## Use from Mirror

Start HumanOS normally:

```bash
humanos
```

Examples:

```text
search the internet for HumanOS Browser Bridge
browse the web for Chrome native messaging documentation
inspect the browser tab
navigate the browser to https://github.com/
```

There is also an explicit command:

```text
/web HumanOS browser bridge
```

Search, navigation, click, and type are effectful browser actions and retain the
interactive HumanOS approval gate. Inspection of the already selected tab is read-only,
but the turn must still have explicit browser/web/internet scope.

Search is implemented through the owner-configured search provider in the selected
browser tab, followed by a bounded page inspection. It is **not** an unrestricted
network proxy.

## Security limits

- HTTPS navigation is limited to the configured host allowlist.
- The browser broker generates a short-lived run envelope in trusted host code; the
  model cannot create or extend that authority.
- Native-host requests use an HMAC over the exact request on an owner-only Unix socket.
- Page text returned to Mirror is bounded.
- The extension never evaluates model-provided JavaScript.
- Browser tools never receive browser cookies or credentials directly.
- The extension operates only the owner-selected tab.
- Clicks remain human-approved, but arbitrary page JavaScript triggered by an approved
  click can cause page behavior that the broker cannot fully predict. For sensitive
  navigation, prefer explicit `browser_navigate`, whose destination is validated
  against the host allowlist.
- Safari and Firefox are not supported by this activation slice.

## Remove HumanOS pairing

The explicit uninstall command removes only the HumanOS-owned native-host manifest and
HumanOS browser control directory. It does not remove the browser, browser profile, or
browsing data:

```bash
humanos --browser-uninstall
```

Remove the unpacked extension through the browser UI separately if desired.

## Troubleshooting

If Mirror reports `REGISTERED_NOT_CONFIGURED`, run `humanos --browser-setup` and
then `humanos --browser-status`.

If `socket_present` is false after pairing, confirm that the unpacked HumanOS
extension is loaded in the same browser target selected during setup, then reload the
extension or browser and check status again.

If a tool says no tab is selected, click the HumanOS extension toolbar button on the
desired tab.

If navigation says the URL host is outside the immutable allowlist, rerun browser setup
with the complete intended `--browser-host` list. The model cannot add hosts itself.

## Implementation files

- `browser_setup.py`: owner-only local installation/config/status/uninstall.
- `browser_bridge.py`: policy boundary, HMAC transport, audit and budgets.
- `browser_native_host.py`: authenticated socket/native-messaging transport.
- `browser-extension/`: selected-tab Chrome/Chromium extension.
- `server_core.py`, `engine.py`, `permissions.py`: runtime discovery, capability
  truthfulness, human-derived scope, and approval wiring.
- `docs/work-orders/HOS-BROWSER-001.md`: bounded SDLC acceptance contract.
