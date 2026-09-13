const HOST = "com.humanos.chat_capture";

function validRecord(record) {
  const keys = ["chat_id", "chat_title", "message_id", "observed_at",
                "role", "source_url", "text"].sort();
  return record && typeof record === "object" &&
    Object.keys(record).sort().join("|") === keys.join("|") &&
    ["USER", "ASSISTANT"].includes(record.role) &&
    typeof record.text === "string" && record.text.length > 0;
}

chrome.runtime.onMessage.addListener((message, sender, respond) => {
  const url = sender.tab && sender.tab.url;
  if (!url || !/^https:\/\/(www\.)?chatgpt\.com\//.test(url) ||
      !message || message.kind !== "CAPTURE_VISIBLE_TURN" ||
      !validRecord(message.record)) {
    respond({ok: false, error: "Rejected untrusted capture message"});
    return false;
  }
  chrome.runtime.sendNativeMessage(HOST, message, (reply) => {
    if (chrome.runtime.lastError) {
      respond({ok: false, error: chrome.runtime.lastError.message});
    } else {
      respond(reply);
    }
  });
  return true;
});
