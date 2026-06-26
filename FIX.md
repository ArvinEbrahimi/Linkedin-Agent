# LinkAid Fix Plan

## P0 — Critical bugs

- [x] **FIX-1** Replace sync `SqliteSaver` with `AsyncSqliteSaver` + `aiosqlite` for `graph.ainvoke()`
- [x] **FIX-2** Add auth: accounts table, register/login API, JWT, protect user routes

## P1 — Performance

- [x] **FIX-3** Reuse persistent `httpx.Client` in `LinkAidClient`
- [x] **FIX-4** Cache sidebar health/ready/LinkedIn status (TTL 30s)
- [x] **FIX-5** Replace `st.tabs` with sidebar radio nav — render only active module
- [x] **FIX-6** Replace `components.html` copy iframes with `st.copy_button`

## P2 — UI/UX redesign

- [x] **FIX-7** Modern theme: header, cards, spacing, RTL-friendly layout
- [x] **FIX-8** Login/register screen before main app (no raw UUID user_id)
- [x] **FIX-9** Cleaner onboarding + sidebar (hide dev fields when logged in)

## P3 — Database

- [x] **FIX-10** `accounts` table in `DATABASE_URL` SQLite; map `user_id` to real account
- [x] **FIX-11** `AUTH_REQUIRED` env (default `false` for tests/extension; `true` in `.env.example`)

## Verification

- [x] **FIX-12** Run `pytest` — 61 passed
- [x] **FIX-13** Restart API + Streamlit

## Notes

- Set `AUTH_REQUIRED=true` in `.env` for production API protection.
- Chrome extension still calls API without JWT when `AUTH_REQUIRED=false`.
- Postgres migration remains a v2 item (`docs/ARCHITECTURE.md`).
