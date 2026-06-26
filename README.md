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
- [Implementation Tasks](TASKS.md) ← start here for development

## Project Status

✅ **Phase 0 complete** — FastAPI scaffold, models, tests  
✅ **Phase 1 complete** — LangGraph supervisor, Groq LLM, `/api/v1/chat`  
✅ **Phase 2 complete** — Content Intelligence, `/api/v1/content/post` & `/campaign`  
🚧 **Phase 3 next** — Networking Engine

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
streamlit run app/ui/streamlit_app.py
```

## Development Workflow

1. Pick a task from [TASKS.md](TASKS.md)
2. Branch: `task/X.Y-short-name`
3. Implement → test → commit → push
4. PR into phase branch → merge phase into `main`

Cursor rules in `.cursor/rules/` enforce this workflow automatically.

## License

Private — All rights reserved.
