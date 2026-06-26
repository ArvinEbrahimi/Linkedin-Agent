/** In-page LinkAid panel on linkedin.com — suggest-only, no auto-submit. */

const PANEL_ID = "linkaid-floating-panel";

function ensurePanel() {
  if (document.getElementById(PANEL_ID)) return;

  const panel = document.createElement("div");
  panel.id = PANEL_ID;
  panel.innerHTML = `
    <div class="linkaid-panel-header">
      <span>🔗 LinkAid</span>
      <button type="button" id="linkaid-close" title="Close">×</button>
    </div>
    <div class="linkaid-panel-body">
      <p class="linkaid-hint">Suggest-only — you decide what to post or send.</p>
      <button type="button" id="linkaid-analyze" class="linkaid-btn">Analyze this profile</button>
      <button type="button" id="linkaid-post" class="linkaid-btn linkaid-btn-secondary">Draft post idea</button>
      <div id="linkaid-status" class="linkaid-status"></div>
      <pre id="linkaid-output" class="linkaid-output"></pre>
    </div>
  `;
  document.body.appendChild(panel);

  document.getElementById("linkaid-close").onclick = () => panel.remove();
  document.getElementById("linkaid-analyze").onclick = onAnalyze;
  document.getElementById("linkaid-post").onclick = onDraftPost;
}

function setStatus(msg, isError = false) {
  const el = document.getElementById("linkaid-status");
  if (el) {
    el.textContent = msg;
    el.className = isError ? "linkaid-status linkaid-error" : "linkaid-status";
  }
}

function setOutput(text) {
  const el = document.getElementById("linkaid-output");
  if (el) el.textContent = text;
}

async function send(action, payload = {}) {
  return chrome.runtime.sendMessage({ action, payload });
}

async function onAnalyze() {
  setStatus("Extracting profile…");
  setOutput("");
  const ctx = window.LinkAidExtract.extractPageContext();
  if (!ctx.text || ctx.text.length < 20) {
    setStatus("Could not read enough profile text on this page.", true);
    return;
  }
  setStatus("Analyzing with LinkAid…");
  const resp = await send("analyzeProfile", { profileText: ctx.text });
  if (!resp?.ok) {
    setStatus(resp?.error || "API error", true);
    return;
  }
  const r = resp.result?.result || {};
  const conn = r.connection_request || "";
  const ice = (r.icebreakers || []).map((x) => `• ${x}`).join("\n");
  setStatus("Done — copy connection request below.");
  setOutput(
    `Summary: ${r.summary || ""}\n\nIcebreakers:\n${ice}\n\nConnection (${conn.length} chars):\n${conn}`
  );
}

async function onDraftPost() {
  const topic = window.prompt("Post topic for LinkAid:", "Lessons from backend engineering");
  if (!topic) return;
  setStatus("Generating post…");
  setOutput("");
  const resp = await send("generatePost", { topic });
  if (!resp?.ok) {
    setStatus(resp?.error || "API error", true);
    return;
  }
  const post = resp.result?.result?.full_post || "";
  setStatus("Done — paste into LinkedIn compose (you post manually).");
  setOutput(post);
  insertIntoCompose(post);
}

function insertIntoCompose(text) {
  const editor =
    document.querySelector(".ql-editor[contenteditable='true']") ||
    document.querySelector("div[role='textbox'][contenteditable='true']");
  if (!editor) return;
  editor.focus();
  document.execCommand("selectAll", false, null);
  document.execCommand("insertText", false, text);
  setStatus("Draft inserted into compose box — review before posting.");
}

function maybeShowPanel() {
  if (window.LinkAidExtract.isProfilePage() || window.LinkAidExtract.isFeedOrCompose()) {
    ensurePanel();
  }
}

const observer = new MutationObserver(() => maybeShowPanel());
observer.observe(document.body, { childList: true, subtree: true });
maybeShowPanel();
