# LinkAid — Product Specification

> **LinkAid** is a strategic AI assistant for Iranian software engineers building a powerful LinkedIn personal brand.  
> **Critical constraint:** Suggest only. Never post, send messages, or take automated actions. User stays in full control.

---

## 1. Vision & Positioning

| Item | Definition |
|------|------------|
| **Product name** | LinkAid |
| **Primary user** | Iranian software engineer (Backend / Full-Stack / AI) |
| **Audience on LinkedIn** | Recruiters, founders, senior engineers, intl. & Iranian companies |
| **Core goals** | Personal branding, high-quality job offers, lead gen, expert positioning |
| **Differentiator** | 2026 LinkedIn algorithm-aware + Persian-first UX + human-in-the-loop |

---

## 2. Hard Rules (Non-Negotiable)

1. **Suggest-only mode** — No auto-posting, messaging, or scraping that violates ToS.
2. **Rate limits** — Max 20 connection request suggestions per day.
3. **Context-first** — Ask clarifying questions when input is insufficient.
4. **Iranian reality** — Account for sanctions, connectivity, payment limits, and local job market.
5. **Memory** — Persist niche, goals, past posts, preferences across sessions.
6. **Standard response structure** — Every agent output follows the 6-section format (see §7).

---

## 2026 LinkedIn Algorithm Knowledge (Embedded in Prompts)

| Signal | Weight / Insight |
|--------|------------------|
| Interest-based distribution | Dominant; niche consistency matters |
| Document / PDF carousels | Highest engagement (~6.6%) |
| Short video (30–90s) | +36% growth |
| Saves | ~5× more valuable than likes |
| Personal profiles | Outperform company pages |
| Posting frequency | 2–5 high-quality posts/week |
| Post structure | Hook (3s) → Story → Value → CTA |
| First 60 min | Intelligent commenting is critical |
| External links | Avoid in post body; use first comment |

---

## 3. Core Capabilities

### 3.1 Content Intelligence
- 30-day serialized campaign ideas
- Full post drafts: Text, Carousel, Video script, Poll, Document outline
- Optimization for Hook + Story + Value + CTA + Saves
- A/B hook variants and hashtag suggestions

### 3.2 Networking Engine
- Profile analysis from pasted URL or pasted bio text
- SWOT + icebreakers + personalized connection request (≤300 chars)
- InMail templates and follow-up sequences (suggest-only)

### 3.3 Profile Optimization
- Headline (keywords + value prop)
- About (Problem → Proof → CTA)
- Experience bullets with quantifiable achievements
- Featured, Skills, Projects recommendations

### 3.4 Daily & Weekly Advisor
- Morning briefing (what to post, who to engage, trends)
- Previous post performance analysis (user-provided metrics)
- Targeted outreach list (≤20/day)

### 3.5 Personal Branding & Strategy
- Personal narrative / positioning statement
- Competitor analysis (user provides profiles or names)
- Content calendar (weekly/monthly)

---

## 4. Standard Agent Response Structure

Every capability must return structured output matching:

1. **Understanding of Request** (1–2 lines)
2. **Main Recommendation** (ready to copy)
3. **2–3 Alternative Options** (with brief comparison)
4. **Strategic Reasoning** (2026 algorithm alignment)
5. **Execution Tips** (timing, length, risks)
6. **Follow-up Question** (gather more context)

Implemented via Pydantic models + structured LLM output (Groq).

---

## 5. User Profile Schema (Long-Term Memory)

```yaml
user_profile:
  name: string
  role: Backend | FullStack | AI Engineer
  years_experience: int
  tech_stack: list[str]
  niche: string                    # e.g. "LLM agents for fintech"
  target_audience: list[str]
  goals: list[str]                 # jobs, leads, thought leadership
  tone_preference: professional | warm | bold
  language_mix: fa-en | en
  posting_frequency: 2-5/week
  past_posts: list[post_record]
  connection_preferences: object
  competitors: list[str]
  constraints:                   # sanctions, no video, etc.
    iranian_market: true
    max_daily_connections: 20
```

---

## 6. Tone & Style

- Professional, confident, warm — senior career consultant
- Short sentences, scannable layout
- Natural Persian + proper technical English terms
- Emojis: sparse, only when natural

---

## 7. Success Metrics (Product)

| Metric | Target |
|--------|--------|
| Time to first useful suggestion | < 30s |
| User copies recommendation | Track in UI (optional) |
| Session continuity | Profile persists across restarts |
| Suggestion quality | User rating thumbs up/down per response |
| Safety | Zero automated LinkedIn actions |

---

## 8. Out of Scope (v1)

- Direct LinkedIn API integration (official API is limited)
- Automated posting or messaging
- Paid LinkedIn Premium features
- Mass scraping or bot behavior

---

## 9. Future (v2+)

- Browser extension for in-context suggestions
- Next.js production UI
- Team/agency multi-user mode
- Analytics dashboard from exported LinkedIn data
