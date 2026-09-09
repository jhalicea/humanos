// This extension accepts commands only from the locally-installed native host.
// It operates on the tab explicitly selected by the user through the toolbar.
const HOST = "com.humanos.browser_bridge";
let selectedTabId = null;
let port = null;

chrome.action.onClicked.addListener((tab) => { selectedTabId = tab.id; });

function connect() {
  port = chrome.runtime.connectNative(HOST);
  port.onMessage.addListener(handle);
  port.onDisconnect.addListener(() => { port = null; setTimeout(connect, 1000); });
}

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
