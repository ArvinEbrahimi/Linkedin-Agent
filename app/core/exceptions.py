class LinkAidError(Exception):
    """Base exception for LinkAid application errors."""

    def __init__(self, message: str, *, code: str = "linkaid_error") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class ConfigurationError(LinkAidError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="configuration_error")


class ValidationError(LinkAidError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="validation_error")


class NotFoundError(LinkAidError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="not_found")


class RateLimitError(LinkAidError):
    def __init__(self, message: str) -> None:
        super().__init__(message, code="rate_limit_exceeded")
