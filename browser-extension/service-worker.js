// This extension accepts commands only from the locally-installed native host.
// It operates on the tab explicitly selected by the user through the toolbar.
const HOST = "com.humanos.browser_bridge";
let selectedTabId = null;
let port = null;

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

function waitForTabComplete(tabId, timeoutMs = 15000) {
  return new Promise((resolve, reject) => {
    let settled = false;
    const timer = setTimeout(() => finish(new Error("Timed out waiting for selected tab navigation")), timeoutMs);
    function finish(error) {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      chrome.tabs.onUpdated.removeListener(listener);
      if (error) reject(error); else resolve();
    }
    function listener(updatedId, info) {
      if (updatedId === tabId && info.status === "complete") finish();
    }
    chrome.tabs.onUpdated.addListener(listener);
    chrome.tabs.get(tabId).then((tab) => {
      if (tab.status === "complete") finish();
    }).catch(finish);
  });
}

async function handle(command) {
  try {
    if (selectedTabId === null) throw new Error("No tab is selected in HumanOS extension");
    // tab_id=0 is the broker's sentinel for "the tab the human selected".
    // A non-zero id is accepted only when it exactly matches that selected tab.
    if (command.tab_id !== 0 && command.tab_id !== selectedTabId) {
      throw new Error("Command does not target the HumanOS-selected tab");
    }
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
    await waitForTabComplete(selectedTabId);
    const tab = await chrome.tabs.get(selectedTabId);
    return {navigated: true, url: tab.url || "", title: tab.title || ""};
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
  const [result] = await chrome.scripting.executeScript({
    target: {tabId: selectedTabId},
    func: pageAction,
    args: [tool, args],
  });
  return result.result;
}

function pageAction(tool, args) {
  const clipped = (value, maximum = 16000) => String(value || "").slice(0, maximum);
  if (tool === "inspect") {
    return {
      url: location.href,
      title: document.title,
      text: clipped(document.body.innerText),
      forms: [...document.forms].slice(0, 20).map(f => ({action: f.action, method: f.method})),
    };
  }
  if (tool === "click") {
    const node = document.querySelector(args.selector);
    if (!node) throw new Error("Selector did not match");
    node.click();
    return {clicked: args.selector, url: location.href};
  }
  if (tool === "type") {
    const node = document.querySelector(args.selector);
    if (!(node instanceof HTMLInputElement || node instanceof HTMLTextAreaElement || node.isContentEditable)) {
      throw new Error("Selector is not a text target");
    }
    node.focus();
    if ("value" in node) node.value = args.text;
    else node.textContent = args.text;
    node.dispatchEvent(new Event("input", {bubbles: true}));
    node.dispatchEvent(new Event("change", {bubbles: true}));
    return {typed: args.selector, bytes: new TextEncoder().encode(args.text).length};
  }
  if (tool === "scroll") {
    window.scrollBy(args.x, args.y);
    return {x: scrollX, y: scrollY};
  }
  throw new Error("Unsupported extension tool");
}

connect();
