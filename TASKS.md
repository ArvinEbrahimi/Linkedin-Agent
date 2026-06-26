# LinkAid — Implementation Task Board

> **Workflow:** One branch per task → implement → commit → push → at phase end: open PR → merge to `main`.  
> **Status legend:** `[ ]` todo · `[~]` in progress · `[x]` done

---

## Phase 0 — Project Foundation

**Branch:** `phase-0/project-foundation`  
**PR title:** `feat: project foundation and dev tooling`

| ID | Task | Branch | Acceptance Criteria |
|----|------|--------|---------------------|
| 0.1 | Python project scaffold | `task/0.1-python-scaffold` | `pyproject.toml`, `app/` package, `uv` or `pip` install works |
| 0.2 | Config & env | `task/0.2-config-env` | `pydantic-settings`, `.env.example`, `app/config.py` |
| 0.3 | Logging & errors | `task/0.3-logging` | Structured logging, custom exceptions, health endpoint stub |
| 0.4 | Dev tooling | `task/0.4-dev-tooling` | `ruff`, `pytest`, `pre-commit` or Makefile, `.gitignore` |
| 0.5 | Base Pydantic models | `task/0.5-base-models` | `LinkAidResponse`, `UserProfile`, request DTOs in `app/models/` |
| 0.6 | Docs & README | `task/0.6-readme` | Updated README with setup, architecture link, env vars |

**Phase 0 done when:** `pytest` passes (even if minimal), `uvicorn app.main:app` starts, README documents local run.

---

## Phase 1 — Core Agent & LangGraph

**Branch:** `phase-1/core-agent`  
**PR title:** `feat: LangGraph supervisor and Groq LLM integration`

| ID | Task | Branch | Acceptance Criteria |
|----|------|--------|---------------------|
| 1.1 | Groq LLM service | `task/1.1-groq-llm` | `app/services/llm.py`, structured output, retry on validation fail |
| 1.2 | LangGraph state | `task/1.2-graph-state` | `LinkAidState` TypedDict, message reducer |
| 1.3 | Supervisor graph | `task/1.3-supervisor-graph` | `StateGraph` compile, SqliteSaver checkpointer |
| 1.4 | Intent router node | `task/1.4-intent-router` | Classify: content / networking / profile / advisor / strategy |
| 1.5 | Response formatter | `task/1.5-response-formatter` | All paths return `LinkAidResponse` schema |
| 1.6 | Base system prompt | `task/1.6-base-prompt` | LinkAid persona, hard rules, 2026 algorithm embedded |
| 1.7 | FastAPI `/chat` | `task/1.7-chat-endpoint` | POST `/api/v1/chat` with thread_id, streams or JSON response |
| 1.8 | Integration tests | `task/1.8-agent-tests` | Mock LLM tests for router + formatter |

**Phase 1 done when:** curl/httpx to `/chat` returns valid 6-section JSON for a general question.

---

## Phase 2 — Content Intelligence

**Branch:** `phase-2/content-intelligence`  
**PR title:** `feat: content intelligence agent`

| ID | Task | Branch | Acceptance Criteria |
|----|------|--------|---------------------|
| 2.1 | Content agent node | `task/2.1-content-node` | Subgraph or node wired from router |
| 2.2 | Content prompts | `task/2.2-content-prompts` | Text, carousel, video script, poll, document templates |
| 2.3 | 30-day campaign generator | `task/2.3-campaign-gen` | Structured `CampaignPlan` model, 30 ideas with themes |
| 2.4 | Hook optimizer | `task/2.4-hook-optimizer` | 3 hook variants per post with save-optimization hints |
| 2.5 | Content API routes | `task/2.5-content-api` | `/api/v1/content/post`, `/api/v1/content/campaign` |
| 2.6 | Content tests | `task/2.6-content-tests` | Unit tests for prompt assembly and schema validation |

**Phase 2 done when:** API generates a full LinkedIn post + 3 hooks + CTA for a given topic.

---

## Phase 3 — Networking Engine

**Branch:** `phase-3/networking-engine`  
**PR title:** `feat: networking engine with outreach limits`

| ID | Task | Branch | Acceptance Criteria |
|----|------|--------|---------------------|
| 3.1 | Networking agent node | `task/3.1-networking-node` | SWOT + icebreakers from pasted profile text |
| 3.2 | Connection request gen | `task/3.2-connection-msg` | ≤300 chars, personalized, copy-ready |
| 3.3 | InMail & follow-up | `task/3.3-inmail-followup` | 3-step sequence templates |
| 3.4 | Daily limit guard | `task/3.4-rate-limit` | Enforce max 20 suggestions/day per user in memory |
| 3.5 | Networking API | `task/3.5-networking-api` | `/api/v1/networking/analyze`, `/outreach` |
| 3.6 | HITL for outreach | `task/3.6-hitl-outreach` | `interrupt_before` optional review on sensitive msgs |

**Phase 3 done when:** Analyze pasted bio → SWOT + connection msg; 21st request same day returns limit warning.

---

## Phase 4 — Profile Optimization

**Branch:** `phase-4/profile-optimization`  
**PR title:** `feat: LinkedIn profile optimization agent`

| ID | Task | Branch | Acceptance Criteria |
|----|------|--------|---------------------|
| 4.1 | Profile agent node | `task/4.1-profile-node` | Headline, about, experience paths |
| 4.2 | Headline generator | `task/4.2-headline` | Keyword-rich, ≤220 chars, 3 variants |
| 4.3 | About section | `task/4.3-about` | Problem → Proof → CTA structure |
| 4.4 | Experience bullets | `task/4.4-experience` | Quantified achievement rewrite |
| 4.5 | Featured & skills | `task/4.5-featured-skills` | Recommendations for featured section + top skills |
| 4.6 | Profile API | `task/4.6-profile-api` | `/api/v1/profile/optimize` with section param |

**Phase 4 done when:** User provides current headline + role → 3 optimized headlines with reasoning.

---

## Phase 5 — Memory & Daily Advisor

**Branch:** `phase-5/memory-advisor`  
**PR title:** `feat: long-term memory and daily advisor`

| ID | Task | Branch | Acceptance Criteria |
|----|------|--------|---------------------|
| 5.1 | ChromaDB memory service | `task/5.1-chroma-memory` | Store/retrieve user profile, posts, preferences |
| 5.2 | Entity memory | `task/5.2-entity-memory` | Remember niche, competitors, goals across threads |
| 5.3 | Summary memory | `task/5.3-summary-memory` | Compress long threads into rolling summary |
| 5.4 | Advisor agent node | `task/5.4-advisor-node` | Morning briefing logic |
| 5.5 | Post performance analysis | `task/5.5-post-analysis` | User inputs metrics → insights + next actions |
| 5.6 | Outreach suggestions | `task/5.6-outreach-list` | Daily list ≤20 with priority scores |
| 5.7 | Memory API | `task/5.7-memory-api` | CRUD `/api/v1/memory/profile`, `/posts` |

**Phase 5 done when:** Second session recalls user niche; briefing references stored goals.

---

## Phase 6 — Strategy & Branding

**Branch:** `phase-6/strategy-branding`  
**PR title:** `feat: personal branding and content strategy`

| ID | Task | Branch | Acceptance Criteria |
|----|------|--------|---------------------|
| 6.1 | Strategy agent node | `task/6.1-strategy-node` | Narrative, competitor, calendar intents |
| 6.2 | Personal narrative | `task/6.2-narrative` | Positioning statement + elevator pitch |
| 6.3 | Competitor analysis | `task/6.3-competitor` | Search tool + SWOT vs competitors |
| 6.4 | Content calendar | `task/6.4-calendar` | 4-week calendar with post types and themes |
| 6.5 | Search integration | `task/6.5-search-tool` | Tavily/DDG for trends (graceful fallback) |
| 6.6 | Strategy API | `task/6.6-strategy-api` | `/api/v1/strategy/narrative`, `/calendar` |

**Phase 6 done when:** Competitor names in → comparison table + differentiated content angles.

**Status:** `[x]` complete — merged to `main`

---

## Phase 7 — Streamlit UI

**Branch:** `phase-7/streamlit-ui`  
**PR title:** `feat: Streamlit UI for LinkAid`

| ID | Task | Branch | Acceptance Criteria |
|----|------|--------|---------------------|
| 7.1 | Chat interface | `task/7.1-chat-ui` | Multi-turn chat, thread persistence |
| 7.2 | Profile onboarding | `task/7.2-onboarding` | First-run wizard for user profile |
| 7.3 | Module tabs | `task/7.3-module-tabs` | Content / Networking / Profile / Advisor / Strategy |
| 7.4 | Copy-to-clipboard | `task/7.4-copy-buttons` | One-click copy for recommendations |
| 7.5 | Persian RTL support | `task/7.5-rtl` | Readable FA text, mixed EN terms |
| 7.6 | Suggest-only disclaimer | `task/7.6-disclaimer` | Persistent banner: no auto-actions |

**Phase 7 done when:** Non-technical user can complete onboarding and generate a post via UI.

**Status:** `[x]` complete — merged to `main`

---

## Phase 8 — Observability & Deployment

**Branch:** `phase-8/deploy-observability`  
**PR title:** `feat: observability and deployment`

| ID | Task | Branch | Acceptance Criteria |
|----|------|--------|---------------------|
| 8.1 | LangFuse integration | `task/8.1-langfuse` | Trace LLM calls and graph steps |
| 8.2 | Docker Compose | `task/8.2-docker` | API + UI + volumes for data |
| 8.3 | Railway/Render config | `task/8.3-deploy-config` | `railway.toml` or render.yaml |
| 8.4 | CI pipeline | `task/8.4-ci` | GitHub Actions: lint + test on PR |
| 8.5 | API docs | `task/8.5-openapi` | Polished OpenAPI descriptions |
| 8.6 | E2E smoke test | `task/8.6-e2e` | Script validates full chat flow |

**Phase 8 done when:** `docker compose up` runs locally; CI green on PR.

**Status:** `[x]` complete — merged to `main`

---

## Git Workflow (Per Task)

```bash
git checkout main && git pull
git checkout -b task/X.Y-short-name
# ... implement ...
git add -A && git commit -m "feat(scope): description"
git push -u origin task/X.Y-short-name
# Merge via PR into phase branch, then phase PR into main
```

### Commit Message Convention

```
feat(content): add 30-day campaign generator
fix(memory): persist user niche on restart
docs(tasks): update phase 2 status
test(agent): mock Groq for router tests
```

---

## Current Progress

| Phase | Status | PR |
|-------|--------|-----|
| 0 — Foundation | `[x]` | phase-0/project-foundation |
| 1 — Core Agent | `[x]` | phase-1/core-agent |
| 2 — Content | `[x]` | phase-2/content-intelligence |
| 3 — Networking | `[x]` | phase-3/networking-engine |
| 4 — Profile | `[x]` | phase-4/profile-optimization |
| 5 — Memory | `[x]` | phase-5/memory-advisor |
| 6 — Strategy | `[ ]` | — |
| 7 — UI | `[ ]` | — |
| 8 — Deploy | `[ ]` | — |

---

## Recommended Start Order

1. **Phase 0** (today) — scaffold so every next task has a home  
2. **Phase 1** — working brain (graph + Groq + `/chat`)  
3. **Phase 7.2 + 7.1** (partial) — onboarding early improves prompt context  
4. **Phase 2 → 6** — specialist agents in value order  
5. **Phase 8** — ship it

---

## Notes for Iranian Users (Build Into Prompts)

- Prefer async text content over heavy video when user has bandwidth constraints
- Mention local companies (Snapp, Digikala, Cafe Bazaar) alongside remote EU/US roles
- Payment: Groq free tier first; warn before paid API usage
- No assumptions about LinkedIn Premium or Sales Navigator
