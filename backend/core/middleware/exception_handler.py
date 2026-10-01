from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from core.exceptions import AppException

def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF views that converts domain exceptions
    into standardized JSON error envelopes.
    """
    # First, let standard DRF handler process built-in DRF exceptions
    response = exception_handler(exc, context)

    if isinstance(exc, AppException):
        status_code = status.HTTP_400_BAD_REQUEST
        if exc.code == "NOT_FOUND":
            status_code = status.HTTP_404_NOT_FOUND
        elif exc.code == "PERMISSION_DENIED":
            status_code = status.HTTP_403_FORBIDDEN
        elif exc.code == "AUTHENTICATION_FAILED":
            status_code = status.HTTP_401_UNAUTHORIZED
        elif exc.code == "CONFLICT":
            status_code = status.HTTP_409_CONFLICT

        return Response(
            {
                "success": False,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details
                }
            },
            status=status_code
        )

    if response is not None:
        # Standardize DRF errors into our schema
        error_code = "VALIDATION_ERROR"
        if response.status_code == 404:
            error_code = "NOT_FOUND"
        elif response.status_code == 403:
            error_code = "PERMISSION_DENIED"
        elif response.status_code == 401:
            error_code = "UNAUTHORIZED"

        details = response.data
        message = "An error occurred during request processing."

        if isinstance(details, dict):
            if 'detail' in details:
                message = str(details['detail'])
        elif isinstance(details, list) and len(details) > 0:
            message = str(details[0])

        response.data = {
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "details": details
            }
        }

    return response
