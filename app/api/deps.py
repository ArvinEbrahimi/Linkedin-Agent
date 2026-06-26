from fastapi import Request

from app.core.exceptions import ConfigurationError


def get_graph(request: Request):
    graph = getattr(request.app.state, "graph", None)
    if graph is None:
        raise ConfigurationError("Agent graph is not initialized")
    return graph
