"""Custom exceptions for the AI Legal OS backend."""

from typing import Any, Dict, Optional


class ProvinceLegalOSException(Exception):
    """Base exception for Province Legal OS."""
    
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class AuthenticationError(ProvinceLegalOSException):
    """Authentication related errors."""
    
    def __init__(self, message: str = "Authentication failed", **kwargs: Any) -> None:
        super().__init__(message, code="AUTHENTICATION_ERROR", **kwargs)


class AuthorizationError(ProvinceLegalOSException):
    """Authorization related errors."""
    
    def __init__(self, message: str = "Access denied", **kwargs: Any) -> None:
        super().__init__(message, code="AUTHORIZATION_ERROR", **kwargs)


class ValidationError(ProvinceLegalOSException):
    """Validation related errors."""
    
    def __init__(self, message: str = "Validation failed", **kwargs: Any) -> None:
        super().__init__(message, code="VALIDATION_ERROR", **kwargs)


class NotFoundError(ProvinceLegalOSException):
    """Resource not found errors."""
    
    def __init__(self, message: str = "Resource not found", **kwargs: Any) -> None:
        super().__init__(message, code="NOT_FOUND", **kwargs)


class ConflictError(ProvinceLegalOSException):
    """Resource conflict errors."""
    
    def __init__(self, message: str = "Resource conflict", **kwargs: Any) -> None:
        super().__init__(message, code="CONFLICT", **kwargs)


class ExternalServiceError(ProvinceLegalOSException):
    """External service errors."""
    
    def __init__(self, message: str = "External service error", **kwargs: Any) -> None:
        super().__init__(message, code="EXTERNAL_SERVICE_ERROR", **kwargs)