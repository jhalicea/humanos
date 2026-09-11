// Capture only exact text visibly rendered in ChatGPT USER/ASSISTANT message nodes.
// Assistant text must be stable across observations and generation must be finished.
const seen = new Map();
const pending = new Map();

function chatId() {
  const match = location.pathname.match(/^\/c\/([^/?#]+)/);
  return match ? match[1] : "chat-" + location.pathname;
}

function messageId(node, role, index) {
  return node.getAttribute("data-message-id") ||
    node.id || [chatId(), role, index].join(":");
}

function generationActive() {
  return Boolean(document.querySelector(
    'button[data-testid="stop-button"], button[aria-label*="Stop generating"]'
  ));
}

function scan() {
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
    if (seen.get(id) === text) return;
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
    chrome.runtime.sendMessage({kind: "CAPTURE_VISIBLE_TURN", record}, reply => {
      if (!chrome.runtime.lastError && reply && reply.ok) seen.set(id, text);
    });
  });
}

const observer = new MutationObserver(() => {
  clearTimeout(observer.timer);
  observer.timer = setTimeout(scan, 750);
});
observer.observe(document.documentElement, {subtree: true, childList: true, characterData: true});
scan();
setInterval(scan, 3000);
