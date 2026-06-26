from langgraph.graph.state import CompiledStateGraph

from app.agents.graph import build_graph
from app.config import Settings
from app.services.content import ContentService
from app.services.llm import LLMService

_graph: CompiledStateGraph | None = None
_llm_service: LLMService | None = None
_content_service: ContentService | None = None


def init_agent(settings: Settings) -> CompiledStateGraph:
    global _graph, _llm_service, _content_service

    _llm_service = LLMService(settings)
    _content_service = ContentService(_llm_service)

    from app.agents.graph import build_checkpointer

    checkpointer = build_checkpointer(settings)
    _graph = build_graph(_llm_service, _content_service, checkpointer)
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
