"""OpenAPI metadata for LinkAid API documentation."""

OPENAPI_TAGS = [
    {
        "name": "health",
        "description": "Service health and version checks.",
    },
    {
        "name": "chat",
        "description": (
            "Supervisor chat endpoint. LangGraph routes messages by intent to specialist agents."
        ),
    },
    {
        "name": "content",
        "description": "Generate LinkedIn posts, hooks, and 30-day content campaigns.",
    },
    {
        "name": "networking",
        "description": (
            "Profile SWOT analysis, icebreakers, and outreach sequences (suggest-only, ≤20/day)."
        ),
    },
    {
        "name": "profile",
        "description": "Optimize headline, about, experience, featured, and skills sections.",
    },
    {
        "name": "memory",
        "description": "Persist user profile, niche, goals, and post performance history.",
    },
    {
        "name": "advisor",
        "description": "Daily briefing, post performance analysis, and outreach suggestions.",
    },
    {
        "name": "strategy",
        "description": "Personal narrative, competitor differentiation, and content calendars.",
    },
    {
        "name": "linkedin",
        "description": (
            "Connect LinkedIn account (OAuth read-only) and import official data export ZIP."
        ),
    },
]

API_DESCRIPTION = """
**LinkAid** helps Iranian software engineers grow their LinkedIn personal brand.

## Important

This API is **suggest-only**. It never posts, sends messages, or takes automated
actions on LinkedIn.

## Modules

| Module | Endpoints |
|--------|-----------|
| Chat | `POST /chat` — supervisor agent with thread memory |
| Content | `POST /content/post`, `POST /content/campaign` |
| Networking | `POST /networking/analyze`, `POST /networking/outreach` |
| Profile | `POST /profile/optimize` |
| Memory | `GET/PUT /memory/profile/{user_id}` |
| Advisor | `POST /advisor/briefing`, `/post-analysis`, `/outreach` |
| Strategy | `POST /strategy/narrative`, `/competitor`, `/calendar` |

## Authentication

No API key required for the LinkAid service itself. Set `GROQ_API_KEY` on the server for LLM calls.
"""
