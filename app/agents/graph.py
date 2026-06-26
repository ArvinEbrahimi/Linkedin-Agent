import logging
import sqlite3
from functools import partial
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from app.agents.nodes.memory import classify_intent, load_memory, save_memory
from app.agents.nodes.respond import format_response, generate_response
from app.agents.state import LinkAidState
from app.config import Settings
from app.services.llm import LLMService

logger = logging.getLogger(__name__)


def _route_after_classify(state: LinkAidState) -> str:
    if state.get("needs_clarification"):
        return "format_response"
    return "generate_response"


def _ensure_checkpoint_dir(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


def build_checkpointer(settings: Settings) -> SqliteSaver:
    _ensure_checkpoint_dir(settings.checkpoint_db_path)
    conn = sqlite3.connect(settings.checkpoint_db_path, check_same_thread=False)
    return SqliteSaver(conn)


def build_graph(llm_service: LLMService, checkpointer: SqliteSaver | None = None):
    graph = StateGraph(LinkAidState)

    graph.add_node("load_memory", load_memory)
    graph.add_node("classify_intent", partial(classify_intent, llm_service=llm_service))
    graph.add_node("generate_response", partial(generate_response, llm_service=llm_service))
    graph.add_node("format_response", format_response)
    graph.add_node("save_memory", save_memory)

    graph.add_edge(START, "load_memory")
    graph.add_edge("load_memory", "classify_intent")
    graph.add_conditional_edges(
        "classify_intent",
        _route_after_classify,
        {"format_response": "format_response", "generate_response": "generate_response"},
    )
    graph.add_edge("generate_response", "format_response")
    graph.add_edge("format_response", "save_memory")
    graph.add_edge("save_memory", END)

    compiled = graph.compile(checkpointer=checkpointer)
    logger.info("LinkAid supervisor graph compiled")
    return compiled
