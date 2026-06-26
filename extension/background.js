import {
  analyzeProfile,
  checkHealth,
  checkReady,
  generatePost,
  getConfig,
  linkedinStatus,
  saveConfig,
} from "./lib/api.js";

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  handleMessage(message)
    .then(sendResponse)
    .catch((err) => sendResponse({ ok: false, error: err.message }));
  return true;
});

async function handleMessage(message) {
  const { action, payload = {} } = message;
  const { userId } = await getConfig();

  switch (action) {
    case "getConfig": {
      const config = await getConfig();
      return { ok: true, config };
    }
    case "saveConfig": {
      await saveConfig(payload.apiUrl, payload.userId);
      return { ok: true };
    }
    case "health": {
      const health = await checkHealth();
      const ready = await checkReady();
      return { ok: true, health, ready };
    }
    case "linkedinStatus": {
      const status = await linkedinStatus(payload.userId || userId);
      return { ok: true, status };
    }
    case "analyzeProfile": {
      const result = await analyzeProfile(payload.profileText, payload.userId || userId);
      return { ok: true, result };
    }
    case "generatePost": {
      const result = await generatePost(payload.topic, payload.userId || userId);
      return { ok: true, result };
    }
    default:
      return { ok: false, error: `Unknown action: ${action}` };
  }
}
