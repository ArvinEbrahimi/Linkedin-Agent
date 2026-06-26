/**
 * Extract visible text from LinkedIn pages (DOM selectors may break when LinkedIn updates UI).
 * Runs in content script context.
 */

function textOf(el) {
  return (el?.innerText || el?.textContent || "").trim();
}

function collectSectionTexts(root, selectors) {
  for (const sel of selectors) {
    const nodes = root.querySelectorAll(sel);
    const parts = Array.from(nodes)
      .map(textOf)
      .filter((t) => t.length > 2);
    if (parts.length) return parts.join("\n");
  }
  return "";
}

function extractProfilePage() {
  const main = document.querySelector("main") || document.body;
  const name =
    textOf(main.querySelector("h1")) ||
    textOf(document.querySelector(".pv-text-details__left-panel h1"));
  const headline =
    textOf(main.querySelector(".text-body-medium")) ||
    textOf(document.querySelector(".pv-text-details__left-panel .text-body-medium"));

  const about = collectSectionTexts(document, [
    "#about ~ div.display-flex .inline-show-more-text",
    "#about ~ * .inline-show-more-text",
    "section[data-section='summary'] .inline-show-more-text",
    "#about + div",
  ]);

  const experience = collectSectionTexts(document, [
    "#experience ~ div",
    "section[data-section='experience']",
  ]);

  const parts = [];
  if (name) parts.push(`Name: ${name}`);
  if (headline) parts.push(`Headline: ${headline}`);
  if (about) parts.push(`About:\n${about}`);
  if (experience) parts.push(`Experience:\n${experience.slice(0, 3000)}`);

  if (parts.length < 2) {
    const fallback = textOf(main).slice(0, 8000);
    return fallback.length >= 20 ? fallback : "";
  }
  return parts.join("\n\n");
}

function extractComposeContext() {
  const editor =
    document.querySelector(".ql-editor[contenteditable='true']") ||
    document.querySelector("[data-placeholder*='post'] div[contenteditable='true']") ||
    document.querySelector("div[role='textbox'][contenteditable='true']");
  return {
    editor,
    currentText: textOf(editor),
    pageType: editor ? "compose" : "unknown",
  };
}

function isProfilePage() {
  return /linkedin\.com\/in\//i.test(window.location.href);
}

function isFeedOrCompose() {
  return (
    /linkedin\.com\/feed/i.test(window.location.href) ||
    document.querySelector(".ql-editor[contenteditable='true']") !== null
  );
}

function extractPageContext() {
  if (isProfilePage()) {
    return { pageType: "profile", text: extractProfilePage() };
  }
  const compose = extractComposeContext();
  if (compose.pageType === "compose") {
    return { pageType: "compose", text: compose.currentText, editor: true };
  }
  return { pageType: "other", text: textOf(document.querySelector("main")).slice(0, 2000) };
}

// Content script global
if (typeof window !== "undefined") {
  window.LinkAidExtract = {
    extractPageContext,
    extractProfilePage,
    isProfilePage,
    isFeedOrCompose,
  };
}
