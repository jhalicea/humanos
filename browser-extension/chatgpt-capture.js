// HumanOS Universal Conversation Capture adapter for ChatGPT web.
//
// This script reads only rendered user/assistant message text on ChatGPT pages.
// It sends exact innerText to the extension service worker. The service worker
// forwards it to a separate local native host; no HumanOS secret is exposed here.

const sent = new Set();
const assistants = new Map();
const STABLE_MS = 1800;
let lastUrl = location.href;

function conversationId() {
  // Wait for a stable ChatGPT conversation route. A new blank chat normally
  // receives /c/<id> after the first message; until then we deliberately do not
  // invent an identifier.
  const path = location.pathname;
  if (!path.includes('/c/')) return null;
  return path;
}

function messageKey(node, role, index) {
  return node.getAttribute('data-message-id') ||
    node.closest('[data-message-id]')?.getAttribute('data-message-id') ||
    `${role}-${index}`;
}

function exactVisibleText(node) {
  // Do not trim or normalize the payload. innerText is the browser's rendered,
  // visible text representation and intentionally preserves visible line breaks.
  return node.innerText;
}

function sendEvent(conversation, turnId, role, text, dedupeKey) {
  if (sent.has(dedupeKey)) return;
  if (typeof text !== 'string' || text.length === 0) return;
  sent.add(dedupeKey);
  chrome.runtime.sendMessage({
    kind: 'humanos-conversation-capture',
    event: {
      source: 'chatgpt',
      conversation_id: conversation,
      turn_id: turnId,
      role,
      text,
    },
  }).then((response) => {
    if (!response || response.ok !== true) sent.delete(dedupeKey);
  }).catch(() => {
    // Native host or service worker may be restarting. Remove the local marker so
    // the next scan retries; the local HumanOS spool is idempotent.
    sent.delete(dedupeKey);
  });
}

function streamingNow() {
  return Boolean(
    document.querySelector('button[data-testid="stop-button"]') ||
    document.querySelector('button[aria-label*="Stop streaming" i]') ||
    document.querySelector('button[aria-label*="Stop generating" i]')
  );
}

function scan() {
  if (location.href !== lastUrl) {
    lastUrl = location.href;
    // Do not clear sent: route changes during the same SPA session can otherwise
    // duplicate already-delivered events. Provider/local IDs remain idempotent.
  }
  const conversation = conversationId();
  if (!conversation) return;

  const nodes = [...document.querySelectorAll(
    '[data-message-author-role="user"], [data-message-author-role="assistant"]'
  )];
  let currentUser = null;
  let assistantOrdinal = 0;

  nodes.forEach((node, index) => {
    const role = node.getAttribute('data-message-author-role');
    const text = exactVisibleText(node);
    const key = messageKey(node, role, index);

    if (role === 'user') {
      currentUser = {key, text};
      assistantOrdinal = 0;
      sendEvent(conversation, key, 'human', text,
                `${conversation}\u0000${key}\u0000human`);
      return;
    }
    if (role !== 'assistant' || !currentUser) return;

    assistantOrdinal += 1;
    const turnId = assistantOrdinal === 1 ? currentUser.key : `${currentUser.key}:alt:${key}`;
    if (assistantOrdinal > 1) {
      // A regenerated/alternate response is represented as its own immutable
      // turn, with the same visible human prompt preserved again as branch context.
      sendEvent(conversation, turnId, 'human', currentUser.text,
                `${conversation}\u0000${turnId}\u0000human`);
    }

    const assistantKey = `${conversation}\u0000${turnId}\u0000assistant`;
    const prior = assistants.get(assistantKey);
    const time = Date.now();
    if (!prior || prior.text !== text) {
      assistants.set(assistantKey, {text, changed: time, turnId, conversation});
      sent.delete(assistantKey);
      return;
    }
    if (!streamingNow() && time - prior.changed >= STABLE_MS) {
      sendEvent(conversation, turnId, 'assistant', text, assistantKey);
    }
  });
}

const observer = new MutationObserver(scan);
observer.observe(document.documentElement, {subtree: true, childList: true, characterData: true});
setInterval(scan, 1000);
scan();
