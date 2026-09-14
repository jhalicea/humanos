// HumanOS Browser Bridge + Universal Conversation Capture transport.
// Browser-control commands and transcript capture use separate native hosts so
// the passive capture path never receives browser-control authority or secrets.
const HOST = "com.humanos.browser_bridge";
const CAPTURE_HOST = "com.humanos.conversation_capture";
let selectedTabId = null;
let port = null;
let capturePort = null;

chrome.action.onClicked.addListener((tab) => { selectedTabId = tab.id; });

function connect() {
  try {
    port = chrome.runtime.connectNative(HOST);
    port.onMessage.addListener(handle);
    port.onDisconnect.addListener(() => { port = null; setTimeout(connect, 1000); });
  } catch (_) {
    port = null;
    setTimeout(connect, 1000);
  }
}

function connectCapture() {
  try {
    capturePort = chrome.runtime.connectNative(CAPTURE_HOST);
    capturePort.onMessage.addListener(() => {});
    capturePort.onDisconnect.addListener(() => {
      capturePort = null;
      setTimeout(connectCapture, 1000);
    });
  } catch (_) {
    capturePort = null;
    setTimeout(connectCapture, 1000);
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (!message || message.kind !== "humanos-conversation-capture") return false;
  const event = message.event;
  if (!event || typeof event !== "object") {
    sendResponse({ok: false, error: "Malformed conversation capture event"});
    return false;
  }
  if (!capturePort) connectCapture();
  if (!capturePort) {
    sendResponse({ok: false, error: "HumanOS capture native host is unavailable"});
    return false;
  }
  try {
    capturePort.postMessage(event);
    sendResponse({ok: true, accepted_by_extension: true});
  } catch (error) {
    capturePort = null;
    sendResponse({ok: false, error: String(error.message || error)});
  }
  return false;
});

async function handle(command) {
  try {
    if (selectedTabId === null || command.tab_id !== selectedTabId) throw new Error("Tab is not selected in HumanOS extension");
    const result = await act(command);
    port.postMessage({ok: true, observation: result});
  } catch (error) {
    port.postMessage({ok: false, error: String(error.message || error)});
  }
}

async function act(command) {
  const {tool, arguments: args} = command;
  if (tool === "navigate") {
    await chrome.tabs.update(selectedTabId, {url: args.url});
    return {navigated: true};
  }
  if (tool === "download") {
    const id = await chrome.downloads.download({url: args.url, saveAs: true});
    return {download_id: id};
  }
  if (tool === "screenshot") {
    const tab = await chrome.tabs.get(selectedTabId);
    const image = await chrome.tabs.captureVisibleTab(tab.windowId, {format: "png"});
    return {png_data_url: image};
  }
  const [result] = await chrome.scripting.executeScript({target: {tabId: selectedTabId}, func: pageAction, args: [tool, args]});
  return result.result;
}

function pageAction(tool, args) {
  const clipped = (value, maximum = 16000) => String(value || "").slice(0, maximum);
  if (tool === "inspect") {
    return {url: location.href, title: document.title, text: clipped(document.body.innerText), forms: [...document.forms].slice(0, 20).map(f => ({action: f.action, method: f.method}))};
  }
  if (tool === "click") {
    const node = document.querySelector(args.selector);
    if (!node) throw new Error("Selector did not match");
    node.click(); return {clicked: args.selector};
  }
  if (tool === "type") {
    const node = document.querySelector(args.selector);
    if (!(node instanceof HTMLInputElement || node instanceof HTMLTextAreaElement || node.isContentEditable)) throw new Error("Selector is not a text target");
    node.focus(); node.value = args.text; node.dispatchEvent(new Event("input", {bubbles: true})); node.dispatchEvent(new Event("change", {bubbles: true}));
    return {typed: args.selector, bytes: new TextEncoder().encode(args.text).length};
  }
  if (tool === "scroll") { window.scrollBy(args.x, args.y); return {x: scrollX, y: scrollY}; }
  throw new Error("Unsupported extension tool");
}

connect();
connectCapture();
