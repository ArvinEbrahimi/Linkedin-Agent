# LinkAid Fix Plan V2

## P0 — Chat quality & routing bugs

- [x] **V2-1** Stop routing `profile`/`content`/… intents to hardcoded clarification template when `needs_clarification=true`
- [x] **V2-2** Improve intent classifier: greetings & profile roadmap questions → `needs_clarification=false`
- [x] **V2-3** Pass `user_context` into classifier; use profile data in responses
- [x] **V2-4** Profile agent: advisory questions (e.g. «از کجا شروع کنم») → roadmap via LLM, not headline optimization
- [x] **V2-5** `generate_response`: still give useful answers when message is vague; no static boilerplate

## P1 — Chat UX

- [x] **V2-6** Compact chat bubble UI (hide 6-section wall for simple replies)
- [x] **V2-7** Persian-friendly chat placeholders & labels

## P2 — Professional cream/brown UI

- [x] **V2-8** Theme: cream `#FAF6F1`, coffee brown `#6F4E37`, tan accents
- [x] **V2-9** Fonts: Cormorant Garamond (headings) + DM Sans (body)
- [x] **V2-10** Replace all emojis with Material Symbols icons
- [x] **V2-11** Modern layout: sidebar nav, cards, auth screen polish

## Verification

- [x] **V2-12** Unit tests for routing + profile advisory (`tests/test_chat_routing.py`)
- [x] **V2-13** `pytest` — 70 passed

## Root cause (chat bug)

Classifier set `needs_clarification=true` → graph skipped specialist agents → `format_response` returned **hardcoded Persian boilerplate** for every message including `intent=profile`.
