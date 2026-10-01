from rest_framework.renderers import JSONRenderer

class StandardJSONRenderer(JSONRenderer):
    """
    Standardizes all API responses to adhere to the enterprise contract:
    Success:
    {
        "success": True,
        "data": ...,
        "meta": { ... }  # optional
    }
    Error:
    {
        "success": False,
        "error": {
            "code": "...",
            "message": "...",
            "details": { ... }
        }
    }
    """
    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get('response') if renderer_context else None

        # Check if already formatted
        if isinstance(data, dict) and ('success' in data and ('data' in data or 'error' in data)):
            return super().render(data, accepted_media_type, renderer_context)

        # If HTTP status is an error
        if response and response.status_code >= 400:
            error_code = "ERROR"
            message = "An error occurred."
            details = {}

            if isinstance(data, dict):
                if 'detail' in data:
                    message = str(data['detail'])
                    error_code = getattr(data.get('detail'), 'code', 'ERROR').upper()
                    details = {k: v for k, v in data.items() if k != 'detail'}
                else:
                    message = "Validation or processing error."
                    details = data
            elif isinstance(data, list):
                details = {"errors": data}
            else:
                message = str(data)

            formatted = {
                "success": False,
                "error": {
                    "code": error_code,
                    "message": message,
                    "details": details
                }
            }
            return super().render(formatted, accepted_media_type, renderer_context)

        # Pagination response separation
        meta = None
        payload = data

        if isinstance(data, dict) and 'results' in data and 'meta' in data:
            payload = data['results']
            meta = data['meta']

        formatted = {
            "success": True,
            "data": payload,
        }
        if meta:
            formatted["meta"] = meta

        return super().render(formatted, accepted_media_type, renderer_context)
