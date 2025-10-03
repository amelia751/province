"""Core exceptions for the AI Legal OS."""


class AILegalOSException(Exception):
    """Base exception for AI Legal OS."""
    pass


class NotFoundError(AILegalOSException):
    """Raised when a resource is not found."""
    pass


class ValidationError(AILegalOSException):
    """Raised when validation fails."""
    pass


class ConflictError(AILegalOSException):
    """Raised when there's a conflict (e.g., duplicate resource)."""
    pass


class PermissionError(AILegalOSException):
    """Raised when user lacks permission for an operation."""
    pass


class ServiceError(AILegalOSException):
    """Raised when an external service fails."""
    pass


class ProcessingError(AILegalOSException):
    """Raised when document or evidence processing fails."""
    pass