# HumanOS Browser Bridge

HumanOS provides governed local browser access to only the tab the owner explicitly selects.
The responsibility chain is: Owner -> HumanOS task scope/approval -> BrowserBroker -> native host -> selected-tab extension.

## Capability truth

Browser tools are not simply available/unavailable. HumanOS distinguishes registered, configured, connection-unverified, and ready-for-action states.
When pairing is absent, Mirror reports REGISTERED_NOT_CONFIGURED and does not advertise the browser tools to the model as executable.

## Setup

Run:

    humanos --browser-setup

Optional target selection:

    humanos --browser-setup --browser-target brave
    humanos --browser-setup --browser-target chrome
    humanos --browser-setup --browser-target chromium

Optional search provider and extra HTTPS hosts:

    humanos --browser-setup --browser-search-provider google
    humanos --browser-setup --browser-host github.com --browser-host developer.chrome.com

Setup writes owner-only pairing state outside the repository under ~/.humanos/browser/ and installs the native-messaging host manifest in the selected browser's per-user NativeMessagingHosts directory.
The 32-byte HMAC secret never enters Git or model prompts.

The bundled unpacked extension has a pinned development key and stable extension ID:

    hdmlcfjlepjknagpdebdlnbdlnjoijbn

## Owner browser action

HumanOS does not silently modify browser profile databases. After setup, open the browser extension management page, enable Developer mode, choose Load unpacked, and select this repository's browser-extension/ directory.
Then open the tab HumanOS may operate and click the HumanOS extension toolbar button. tab_id 0 means the tab the human selected; a non-zero ID must exactly match that selected tab.

Check pairing without opening the Life Notebook:

    humanos --browser-status

## Mirror use

Explicit browser/web/internet intent establishes browser scope. Examples include 'search the web for ...', 'browse the internet ...', and 'inspect the browser'.
browser_inspect is read-only. browser_search, browser_navigate, browser_click, and browser_type require the HumanOS interactive approval gate for the exact request.
BrowserBroker independently enforces HTTPS host allowlists, short-lived run authority, capability/action/byte limits, HMAC transport, audit evidence, and stop state.

browser_search navigates the selected tab to the owner-configured search provider and then returns a bounded inspection of the results page. It is not an unrestricted backend network proxy.

## Native messaging

The Manifest V3 extension declares nativeMessaging and connects only to com.humanos.browser_bridge.
The browser launches an owner-only generated wrapper executable. That wrapper supplies the exact socket and secret arguments required by browser_native_host.py.
The native host authenticates broker requests with HMAC and forwards bounded native-messaging frames over stdin/stdout.
The extension never evaluates model-provided JavaScript.

Extension-origin failures are propagated as HumanOS tool failures; transport success is not treated as action success.

## Removal

Remove only HumanOS-owned pairing artifacts with:

    humanos --browser-uninstall

This does not delete browser profiles, browsing data, other native-message hosts, or the unpacked extension.

## Evidence boundary

Current Chrome native-messaging documentation requires nativeMessaging permission, an absolute native-host path on macOS/Linux, exact non-wildcard allowed_origins, framed stdin/stdout transport, and browser-specific NativeMessagingHosts locations.
Repository tests verify deterministic setup and policy boundaries. Real end-to-end readiness remains unverified until post-promotion pairing/readback on the owner's Mac.
