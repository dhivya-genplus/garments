class AppException(Exception):
    """Base exception for application domain errors."""
    code = "APPLICATION_ERROR"
    message = "An unexpected error occurred."

    def __init__(self, message=None, code=None, details=None):
        if message:
            self.message = message
        if code:
            self.code = code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AppException):
    code = "VALIDATION_ERROR"
    message = "Invalid input or business rule violation."


class ResourceNotFound(AppException):
    code = "NOT_FOUND"
    message = "The requested resource does not exist."


class PermissionDeniedError(AppException):
    code = "PERMISSION_DENIED"
    message = "You do not have permission to perform this action."


class AuthenticationError(AppException):
    code = "AUTHENTICATION_FAILED"
    message = "Authentication credentials were not provided or are invalid."


class ConflictError(AppException):
    code = "CONFLICT"
    message = "A conflict occurred with an existing resource."
