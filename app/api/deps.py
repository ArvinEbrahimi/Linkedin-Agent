from fastapi import Request

from app.core.exceptions import ConfigurationError
from app.services.content import ContentService


def get_graph(request: Request):
    graph = getattr(request.app.state, "graph", None)
    if graph is None:
        raise ConfigurationError("Agent graph is not initialized")
    return graph


def get_content_service(request: Request) -> ContentService:
    service = getattr(request.app.state, "content_service", None)
    if service is None:
        raise ConfigurationError("Content service is not initialized")
    return service
