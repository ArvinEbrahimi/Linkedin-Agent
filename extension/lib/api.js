/** LinkAid API client — used from the extension service worker. */

const DEFAULT_API_URL = "http://localhost:8000";

export async function getConfig() {
  const data = await chrome.storage.sync.get({
    apiUrl: DEFAULT_API_URL,
    userId: "default",
  });
  return { apiUrl: data.apiUrl.replace(/\/$/, ""), userId: data.userId };
}

export async function saveConfig(apiUrl, userId) {
  await chrome.storage.sync.set({ apiUrl: apiUrl.replace(/\/$/, ""), userId });
}

export async function apiRequest(path, options = {}) {
  const { apiUrl } = await getConfig();
  const url = `${apiUrl}${path}`;
  const response = await fetch(url, {
    ...options,
    headers: {
      Accept: "application/json",
      ...(options.headers || {}),
    },
  });
  const text = await response.text();
  let body;
  try {
    body = text ? JSON.parse(text) : null;
  } catch {
    body = { message: text };
  }
  if (!response.ok) {
    const message = body?.message || body?.detail || `HTTP ${response.status}`;
    throw new Error(message);
  }
  return body;
}

export async function checkHealth() {
  return apiRequest("/api/v1/health");
}

export async function checkReady() {
  return apiRequest("/api/v1/ready");
}

export async function analyzeProfile(profileText, userId) {
  return apiRequest("/api/v1/networking/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      profile_text: profileText,
      user_id: userId,
    }),
  });
}

export async function generatePost(topic, userId) {
  return apiRequest("/api/v1/content/post", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      topic,
      post_type: "text",
      language: "fa-en",
    }),
  });
}

export async function linkedinStatus(userId) {
  return apiRequest(`/api/v1/linkedin/status/${encodeURIComponent(userId)}`);
}
