# LinkAid

**LinkAid** — Personal AI assistant for LinkedIn personal branding, built for Iranian software engineers.

> Suggest-only. Never posts, sends messages, or takes automated actions on LinkedIn.

## What It Does

| Module | Capabilities |
|--------|-------------|
| **Content Intelligence** | 30-day campaigns, posts, carousels, video scripts, hook optimization |
| **Networking Engine** | Profile SWOT, icebreakers, connection requests (≤300 chars), follow-ups |
| **Profile Optimization** | Headline, About, Experience, Featured, Skills |
| **Daily Advisor** | Morning briefing, post analysis, outreach suggestions (≤20/day) |
| **Strategy** | Personal narrative, competitor analysis, content calendar |

## Tech Stack

- **Orchestration:** LangGraph
- **LLM:** Groq (Llama 3.3 70B / Qwen3)
- **API:** FastAPI
- **UI:** Streamlit (v1) → Next.js (v2)
- **Memory:** ChromaDB + LangGraph checkpointer
- **Observability:** LangFuse

## Documentation

- [Product Specification](docs/PRODUCT_SPEC.md)
- [Technical Architecture](docs/ARCHITECTURE.md)
- [LinkedIn Setup](docs/LINKEDIN_SETUP.md) ← OAuth + data import
- [Implementation Tasks](TASKS.md) ← start here for development

## Project Status

✅ **Phase 0 complete** — FastAPI scaffold, models, tests  
✅ **Phase 1 complete** — LangGraph supervisor, Groq LLM, `/api/v1/chat`  
✅ **Phase 2 complete** — Content Intelligence, `/api/v1/content/post` & `/campaign`  
✅ **Phase 3 complete** — Networking Engine, SWOT, outreach, rate limit  
✅ **Phase 4 complete** — Profile Optimization, headline/about/experience  
✅ **Phase 5 complete** — Memory (ChromaDB), Daily Advisor, briefing API  
✅ **Phase 6 complete** — Strategy & Branding, narrative/competitor/calendar APIs  
✅ **Phase 7 complete** — Streamlit UI (chat, onboarding, module tabs, RTL, copy)  
✅ **Phase 8 complete** — LangFuse, Docker Compose, CI, E2E smoke, OpenAPI docs  
✅ **Phase 9 complete** — LinkedIn OAuth, data import, Setup UI

See [TASKS.md](TASKS.md) for the full phased roadmap (8 phases, 50+ tasks).

## Quick Start (after Phase 0)

```bash
# Clone
git clone git@github.com:ArvinEbrahimi/Linkedin-Agent.git
cd Linkedin-Agent

# Environment
cp .env.example .env
# Edit .env and add GROQ_API_KEY

# Install (Phase 0+)
pip install -e ".[dev]"

# Run API (Phase 1+)
uvicorn app.main:app --reload

# Run UI (Phase 7+)
make run-ui

# Docker — API + UI (Phase 8+)
cp .env.example .env   # add GROQ_API_KEY
make docker-up
# API → http://localhost:8000  |  UI → http://localhost:8501
# Docs → http://localhost:8000/docs

# E2E smoke (API must be running)
make e2e
make e2e-chat   # also tests /chat (needs GROQ_API_KEY)
```

## Development Workflow

1. Pick a task from [TASKS.md](TASKS.md)
2. Branch: `task/X.Y-short-name`
3. Implement → test → commit → push
4. PR into phase branch → merge phase into `main`

Cursor rules in `.cursor/rules/` enforce this workflow automatically.

## License

Private — All rights reserved.
