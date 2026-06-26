# LinkAid Chrome Extension

Read-only in-context assistant on **linkedin.com** — connects to your local LinkAid API.

> Suggest-only. Never auto-posts or sends messages. You review and click Post/Connect yourself.

## Prerequisites

1. LinkAid API running: `make run` (http://localhost:8000)
2. `GROQ_API_KEY` in `.env` for AI features
3. Chrome or Edge (Chromium)

## Install (unpacked)

1. Open `chrome://extensions`
2. Enable **Developer mode**
3. **Load unpacked** → select the `extension/` folder in this repo
4. Click the LinkAid icon → set API URL and User ID (match Streamlit sidebar)

## Usage on LinkedIn

| Page | Action |
|------|--------|
| **Profile** (`/in/username`) | Floating panel → **Analyze this profile** → SWOT + connection draft |
| **Feed / Compose** | **Draft post idea** → inserts text into compose box (you post manually) |

## Architecture

```
linkedin.com page
  └── content/content.js  (extract DOM, floating panel)
        └── chrome.runtime.sendMessage
              └── background.js  (service worker)
                    └── lib/api.js → localhost:8000
```

API calls go through the **background service worker** (no CORS issues).

## Configuration

Stored in `chrome.storage.sync`:

- `apiUrl` — default `http://localhost:8000`
- `userId` — must match Streamlit/API user for memory

## Limitations

- LinkedIn DOM changes may break profile extraction — fallback uses visible main text
- No access to private analytics or connections via API
- Extension does not replace Streamlit UI — use both together

See [docs/LINKEDIN_SETUP.md](../docs/LINKEDIN_SETUP.md) for OAuth and data import.
