# LinkAid — Technical Architecture

## Stack (2026 — Free / Low-Cost)

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Language | Python 3.11+ | Best LangGraph ecosystem |
| Orchestration | LangGraph | Stateful workflows, checkpoints, HITL |
| LLM | Groq (Llama 3.3 70B, Qwen3) | Fast, cheap, OpenAI-compatible |
| Short-term memory | LangGraph State + Message History | Per-thread context |
| Long-term memory | ChromaDB → PGVector (prod) | Entity + summary memory |
| API | FastAPI | Async, OpenAPI, production-ready |
| UI (Phase 1) | Streamlit | Fast prototyping |
| UI (Phase 2) | Next.js | Production polish |
| Search | Tavily / DuckDuckGo | Trend & competitor research |
| Persistence | SQLite + LangGraph SqliteSaver | Dev; PostgreSQL in prod |
| Observability | LangFuse (free tier) | Traces, prompts, evals |
| Deployment | Railway / Render / VPS | Simple CI/CD |

---

## High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Streamlit / Next.js UI                    │
│              (suggest-only · copy buttons · HITL approve)        │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP
┌────────────────────────────▼────────────────────────────────────┐
│                         FastAPI Gateway                          │
│   /chat  /content  /networking  /profile  /advisor  /memory      │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    LinkAid Supervisor Graph                      │
│                      (LangGraph StateGraph)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Router   │→ │ Content  │  │ Network  │  │ Profile  │ ...    │
│  │ Node     │  │ Agent    │  │ Agent    │  │ Agent    │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│         │              │            │              │             │
│         └──────────────┴────────────┴──────────────┘             │
│                             │                                    │
│                    ┌────────▼────────┐                         │
│                    │  Response       │                         │
│                    │  Formatter Node │ → Standard 6-section     │
│                    └────────┬────────┘                         │
└─────────────────────────────┼───────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼──────┐    ┌─────────▼────────┐   ┌───────▼───────┐
│ Groq LLM     │    │ Memory Service   │   │ Search Tool   │
│ (structured) │    │ ChromaDB/SQLite  │   │ Tavily/DDG    │
└──────────────┘    └──────────────────┘   └───────────────┘
```

---

## LangGraph Design

### State (`LinkAidState`)

```python
class LinkAidState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    thread_id: str
    intent: Literal["content", "networking", "profile", "advisor", "strategy", "general"]
    user_context: dict          # loaded from long-term memory
    draft_response: dict | None # structured Pydantic as dict
    needs_clarification: bool
    clarification_question: str | None
    metadata: dict              # tokens, model, latency
```

### Nodes

| Node | Responsibility |
|------|----------------|
| `load_memory` | Fetch user profile, recent posts, preferences |
| `classify_intent` | Route to specialist subgraph |
| `gather_context` | Ask follow-ups if fields missing |
| `content_agent` | Campaigns, posts, hooks |
| `networking_agent` | SWOT, icebreakers, connection msgs |
| `profile_agent` | Headline, about, experience |
| `advisor_agent` | Briefing, performance, outreach list |
| `strategy_agent` | Narrative, competitors, calendar |
| `format_response` | Enforce 6-section structure |
| `save_memory` | Persist entities, summaries, posts |
| `human_review` | Optional interrupt before showing sensitive outreach |

### Edges

```
START → load_memory → classify_intent
classify_intent → gather_context (if incomplete)
classify_intent → {specialist} (if complete)
gather_context → END (return question) | classify_intent (retry)
{specialist} → format_response → save_memory → END
```

### Checkpointer

- Dev: `SqliteSaver` → `./data/checkpoints.db`
- Prod: `PostgresSaver`

Enables thread resume, multi-turn clarification, and audit trail.

---

## Directory Structure (Target)

```
Linkedin_Agent/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI entry
│   ├── config.py               # Settings (pydantic-settings)
│   ├── agents/
│   │   ├── graph.py            # Supervisor graph
│   │   ├── state.py
│   │   ├── nodes/
│   │   │   ├── router.py
│   │   │   ├── content.py
│   │   │   ├── networking.py
│   │   │   ├── profile.py
│   │   │   ├── advisor.py
│   │   │   └── strategy.py
│   │   └── prompts/            # System prompts per agent
│   ├── models/
│   │   ├── responses.py        # Standard 6-section output
│   │   ├── user.py
│   │   └── requests.py
│   ├── services/
│   │   ├── llm.py              # Groq client + structured output
│   │   ├── memory.py           # ChromaDB + entity store
│   │   └── search.py           # Tavily/DDG wrapper
│   └── ui/
│       └── streamlit_app.py
├── tests/
│   ├── unit/
│   └── integration/
├── docs/
├── data/                       # gitignored — DB, chroma
├── .cursor/rules/
├── pyproject.toml
├── .env.example
├── TASKS.md
└── README.md
```

---

## LLM Integration Pattern

```python
# Structured output with retry
from pydantic import BaseModel

class LinkAidResponse(BaseModel):
    understanding: str
    main_recommendation: str
    alternatives: list[AlternativeOption]  # max 3
    strategic_reasoning: str
    execution_tips: str
    follow_up_question: str

# Groq via langchain-groq or openai-compatible client
# Retry: tenacity 3x on validation errors
# Fallback: smaller model or degraded text mode
```

---

## Security & Privacy

- API keys in `.env` only; never committed
- User profile data encrypted at rest (prod: DB-level)
- No LinkedIn credentials stored in v1
- Rate limiting on API endpoints
- Audit log for all generated outreach suggestions

---

## Deployment Topology (Railway)

```
[Streamlit UI] ──► [FastAPI] ──► [Groq API]
                      │
                      ├── SQLite/Postgres (checkpoints + user)
                      ├── ChromaDB (vectors)
                      └── LangFuse (traces)
```

---

## Environment Variables

```bash
GROQ_API_KEY=
TAVILY_API_KEY=          # optional
LANGFUSE_PUBLIC_KEY=     # optional
LANGFUSE_SECRET_KEY=     # optional
DATABASE_URL=sqlite:///./data/linkaid.db
CHROMA_PERSIST_DIR=./data/chroma
ENV=development
LOG_LEVEL=INFO
```
