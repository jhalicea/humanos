// Capture only exact text visibly rendered in ChatGPT USER/ASSISTANT message nodes.
// Assistant text must be stable across observations and generation must be finished.
const seen = new Map();
const pending = new Map();
const inFlight = new Set();
let observedRoot = null;
let scanTimer = null;

function chatId() {
  const match = location.pathname.match(/^\/c\/([^/?#]+)/);
  return match ? match[1] : "chat-" + location.pathname;
}

function messageId(node, role, index) {
  return node.getAttribute("data-message-id") ||
    node.closest("[data-message-id]")?.getAttribute("data-message-id") ||
    node.id || node.closest("[id]")?.id ||
    [chatId(), role, index].join(":");
}

function generationActive() {
  return Boolean(document.querySelector(
    'button[data-testid="stop-button"], button[aria-label*="Stop generating"]'
  ));
}

function scheduleScan(delay = 100) {
  clearTimeout(scanTimer);
  scanTimer = setTimeout(scanSafely, delay);
}

function ensureObserver() {
  if (observedRoot === document.documentElement) return;
  observer.disconnect();
  observedRoot = document.documentElement;
  if (observedRoot) {
    observer.observe(observedRoot, {
      subtree: true, childList: true, characterData: true
    });
  }
}

function scan() {
  ensureObserver();
  const nodes = [...document.querySelectorAll("[data-message-author-role]")];
  nodes.forEach((node, index) => {
    const rawRole = node.getAttribute("data-message-author-role");
    const role = rawRole === "user" ? "USER" :
      rawRole === "assistant" ? "ASSISTANT" : null;
    if (!role) return;
    const text = node.innerText;
    if (!text) return;
    const id = messageId(node, role, index);
    const prior = pending.get(id);
    const stable = prior && prior.text === text ? prior.stable + 1 : 1;
    pending.set(id, {text, stable});
    if (seen.get(id) === text || inFlight.has(id)) return;
    if (role === "ASSISTANT" && (generationActive() || stable < 2)) return;
    const record = {
      message_id: id,
      chat_id: chatId(),
      chat_title: document.title || "Untitled ChatGPT chat",
      role,
      text,
      observed_at: new Date().toISOString(),
      source_url: location.href
    };
    inFlight.add(id);
    chrome.runtime.sendMessage({kind: "CAPTURE_VISIBLE_TURN", record}, reply => {
      inFlight.delete(id);
      if (!chrome.runtime.lastError && reply && reply.ok) {
        seen.set(id, text);
      }
    });
  });
}

function scanSafely() {
  try {
    scan();
  } catch (error) {
    console.error("HumanOS capture scan failed", error);
  }
}

const observer = new MutationObserver(() => scheduleScan(150));
ensureObserver();

window.addEventListener("pageshow", () => scheduleScan(0));
window.addEventListener("popstate", () => scheduleScan(0));
document.addEventListener("submit", () => {
  scheduleScan(100);
  setTimeout(scanSafely, 1000);
}, true);
document.addEventListener("click", () => scheduleScan(250), true);
document.addEventListener("keydown", event => {
  if (event.key === "Enter") {
    scheduleScan(100);
    setTimeout(scanSafely, 1000);
  }
}, true);

scanSafely();
// Rebind after SPA root replacement and recover from missed mutation notifications.
setInterval(scanSafely, 1000);
