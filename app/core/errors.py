from fastapi import HTTPException

class APIError(HTTPException):
    def __init__(self, status_code: int, error_code: str, message: str, field: str = None):
        detail = {
            "error": error_code,
            "message": message
        }
        if field:
            detail["field"] = field
        super().__init__(status_code=status_code, detail=detail)

class InvalidStateTransitionError(APIError):
    def __init__(self, message: str = "Invalid state transition"):
        super().__init__(status_code=400, error_code="INVALID_STATE_TRANSITION", message=message)

class ValidationError(APIError):
    def __init__(self, message: str, field: str = None):
        super().__init__(status_code=400, error_code="VALIDATION_ERROR", message=message, field=field)

class NotFoundError(APIError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(status_code=404, error_code="NOT_FOUND", message=message)

class ConflictError(APIError):
    def __init__(self, message: str):
        super().__init__(status_code=409, error_code="CONFLICT", message=message)

class ForbiddenError(APIError):
    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(status_code=403, error_code="FORBIDDEN", message=message)

class UnauthorizedError(APIError):
    def __init__(self, message: str = "Could not validate credentials"):
        super().__init__(status_code=401, error_code="UNAUTHORIZED", message=message)
