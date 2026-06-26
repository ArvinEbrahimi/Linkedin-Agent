# LinkAid Browser Extension (planned)

Read-only context from an open LinkedIn tab — **no automation**.

## Planned capabilities

- Detect when user is on `linkedin.com/feed` or profile pages
- One-click: send visible profile text to LinkAid `/networking/analyze`
- One-click: copy compose-box draft from LinkAid `/content/post`
- Show connection status to local LinkAid API

## Not planned

- Auto-post, auto-connect, or scraping at scale (ToS risk)

## Stack (TBD)

- Manifest V3 Chrome extension
- Communicates with `LINKAID_API_URL` (default `http://localhost:8000`)

See Phase 10 in `TASKS.md` when scheduled.
