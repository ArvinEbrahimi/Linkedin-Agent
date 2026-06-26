from langgraph.graph.state import CompiledStateGraph

from app.agents.graph import build_graph
from app.config import Settings
from app.services.llm import LLMService

_graph: CompiledStateGraph | None = None


def init_agent(settings: Settings) -> CompiledStateGraph:
    global _graph
    llm_service = LLMService(settings)
    from app.agents.graph import build_checkpointer

    checkpointer = build_checkpointer(settings)
    _graph = build_graph(llm_service, checkpointer)
    return _graph


def get_compiled_graph() -> CompiledStateGraph:
    if _graph is None:
        raise RuntimeError("Agent graph not initialized — call init_agent first")
    return _graph
