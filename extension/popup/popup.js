async function send(action, payload = {}) {
  return chrome.runtime.sendMessage({ action, payload });
}

function setPill(id, text, className = "") {
  const el = document.getElementById(id);
  el.textContent = text;
  el.className = `pill ${className}`.trim();
}

async function load() {
  const resp = await send("getConfig");
  if (resp?.ok) {
    document.getElementById("apiUrl").value = resp.config.apiUrl;
    document.getElementById("userId").value = resp.config.userId;
  }

  try {
    const health = await send("health");
    if (health?.ok) {
      const groq = health.ready?.groq_configured;
      setPill(
        "api-status",
        groq ? `API online · ${health.health.app}` : "API online · Groq not configured",
        groq ? "" : "warn"
      );
      const userId = document.getElementById("userId").value || "default";
      const li = await send("linkedinStatus", { userId });
      if (li?.ok && li.status?.connected) {
        setPill("li-status", `LinkedIn: ${li.status.name || "connected"}`);
      } else {
        setPill("li-status", "LinkedIn: not connected", "muted");
      }
    }
  } catch (e) {
    setPill("api-status", `API offline — run make run`, "error");
  }
}

document.getElementById("save").addEventListener("click", async () => {
  const apiUrl = document.getElementById("apiUrl").value;
  const userId = document.getElementById("userId").value || "default";
  await send("saveConfig", { apiUrl, userId });
  setPill("api-status", "Settings saved");
  load();
});

load();
