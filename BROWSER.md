# HumanOS Browser Bridge

HumanOS now has a real browser capability with a narrow trust boundary. A local
model can inspect, navigate, click, type, scroll, download, and capture the
browser tab that you select. It does not receive browser credentials, cookies,
extension management, arbitrary JavaScript, DevTools, shell access, or a general
network proxy.

`browser-extension/` is a Manifest V3 Chrome/Chromium extension. Click its
toolbar button on the tab you want HumanOS to operate. It accepts commands only
through Chrome native messaging and rejects requests for another tab.

`browser_native_host.py` is the extension's local native-messaging host. It
listens only on an owner-only Unix socket and requires an HMAC over each broker
request. Its secret is generated locally in an owner-only directory.

`browser_bridge.py` validates an immutable envelope, enforces capability, URL,
action, byte, time, and stop limits, collects human approval for side effects,
and fsyncs an external audit record before and after every action.

The trusted host supplies this envelope, never the model:

```json
{
  "run_id": "work-20260909-01",
  "authorization": "Owner authorization HOS-BROWSER-001",
  "expires": 1789000000,
  "hosts": ["github.com", "docs.google.com"],
  "capabilities": ["inspect", "navigate", "click", "type", "scroll", "screenshot", "download"],
  "max_actions": 100,
  "max_bytes": 1000000
}
```

`inspect` and `screenshot` are read-only. Every other tool requires a separate
human approval callback immediately before dispatch. `navigate` and `download`
allow only HTTPS URLs whose host is exactly in `hosts` or its subdomain. The
extension's page script never evaluates model-provided JavaScript.

## Install and pairing

1. Load `browser-extension/` as an unpacked extension in Chrome or Chromium.
2. Copy `browser_extension_manifest.json` to Chrome's native-messaging-hosts
   directory. Replace `path` with the absolute native-host path and replace the
   extension ID after Chrome assigns it. Keep that manifest mode 0600.
3. Start the native host with absolute `--socket` and `--secret` paths in an
   owner-only control directory. Keep both out of workspaces, Notebooks,
   repositories, sync directories, model prompts, and extension storage.
4. Build the broker with `bridge_sender(socket_path, secret_path)` and an
   approval callback supplied by HumanOS's human interface.
5. Select a tab through the extension toolbar button before allowing any tool.

The broker receives strict requests such as:

```json
{"tool":"inspect","tab_id":123,"arguments":{}}
```

It returns bounded observations. Page text is capped at 16 KiB and native frames
at 1 MiB. The normal Mirror tool registry is intentionally unchanged until a
desktop approval dialog can show clear action-by-action choices. This bridge does
not automate installation, provide remote audit anchoring, or isolate arbitrary
native worker processes.
