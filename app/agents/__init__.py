from langgraph.graph.state import CompiledStateGraph

from app.agents.graph import build_graph
from app.config import Settings
from app.services.content import ContentService
from app.services.llm import LLMService
from app.services.networking import NetworkingService
from app.services.profile import ProfileService
from app.services.rate_limit import OutreachRateLimiter

_graph: CompiledStateGraph | None = None
_llm_service: LLMService | None = None
_content_service: ContentService | None = None
_networking_service: NetworkingService | None = None
_profile_service: ProfileService | None = None
_rate_limiter: OutreachRateLimiter | None = None


def init_agent(settings: Settings) -> CompiledStateGraph:
    global _graph, _llm_service, _content_service
    global _networking_service, _profile_service, _rate_limiter

    _llm_service = LLMService(settings)
    _content_service = ContentService(_llm_service)
    _profile_service = ProfileService(_llm_service)
    _rate_limiter = OutreachRateLimiter(
        settings.outreach_limit_db_path,
        daily_limit=settings.max_daily_outreach,
    )
    _networking_service = NetworkingService(_llm_service, _rate_limiter)

    from app.agents.graph import build_checkpointer

    checkpointer = build_checkpointer(settings)
    _graph = build_graph(
        _llm_service,
        _content_service,
        _networking_service,
        _profile_service,
        checkpointer,
    )
    return _graph


def get_compiled_graph() -> CompiledStateGraph:
    if _graph is None:
        raise RuntimeError("Agent graph not initialized — call init_agent first")
    return _graph


def get_llm_service() -> LLMService:
    if _llm_service is None:
        raise RuntimeError("LLM service not initialized")
    return _llm_service


def get_content_service() -> ContentService:
    if _content_service is None:
        raise RuntimeError("Content service not initialized")
    return _content_service


def get_networking_service() -> NetworkingService:
    if _networking_service is None:
        raise RuntimeError("Networking service not initialized")
    return _networking_service


def get_profile_service() -> ProfileService:
    if _profile_service is None:
        raise RuntimeError("Profile service not initialized")
    return _profile_service
