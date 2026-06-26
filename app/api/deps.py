from fastapi import Request

from app.core.exceptions import ConfigurationError
from app.services.advisor import AdvisorService
from app.services.content import ContentService
from app.services.memory_store import MemoryService
from app.services.networking import NetworkingService
from app.services.profile import ProfileService


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


def get_networking_service(request: Request) -> NetworkingService:
    service = getattr(request.app.state, "networking_service", None)
    if service is None:
        raise ConfigurationError("Networking service is not initialized")
    return service


def get_profile_service(request: Request) -> ProfileService:
    service = getattr(request.app.state, "profile_service", None)
    if service is None:
        raise ConfigurationError("Profile service is not initialized")
    return service


def get_memory_service(request: Request) -> MemoryService:
    service = getattr(request.app.state, "memory_service", None)
    if service is None:
        raise ConfigurationError("Memory service is not initialized")
    return service


def get_advisor_service(request: Request) -> AdvisorService:
    service = getattr(request.app.state, "advisor_service", None)
    if service is None:
        raise ConfigurationError("Advisor service is not initialized")
    return service
