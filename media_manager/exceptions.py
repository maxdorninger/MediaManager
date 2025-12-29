from fastapi import Request
from fastapi.responses import JSONResponse


class MediaManagerException(Exception):
    """Base exception for MediaManager errors."""

    def __init__(self, message: str = "An error occurred."):
        super().__init__(message)
        self.message = message


class MediaAlreadyExists(MediaManagerException):
    """Raised when a media entity already exists (HTTP 409)."""

    def __init__(
        self, message: str = "Entity with this ID or other identifier already exists"
    ):
        super().__init__(message)


class NotFoundError(MediaManagerException):
    """Raised when an entity is not found (HTTP 404)."""

    def __init__(self, message: str = "The requested entity was not found."):
        super().__init__(message)


class InvalidConfigError(MediaManagerException):
    """Raised when the server is improperly configured (HTTP 500)."""

    def __init__(self, message: str = "The server is improperly configured."):
        super().__init__(message)


class BadRequestError(MediaManagerException):
    """Raised for invalid client requests (HTTP 400)."""

    def __init__(self, message: str = "Bad request."):
        super().__init__(message)


class UnauthorizedError(MediaManagerException):
    """Raised for authentication failures (HTTP 401)."""

    def __init__(self, message: str = "Unauthorized."):
        super().__init__(message)


class ForbiddenError(MediaManagerException):
    """Raised for forbidden actions (HTTP 403)."""

    def __init__(self, message: str = "Forbidden."):
        super().__init__(message)


class ConflictError(MediaManagerException):
    """Raised for resource conflicts (HTTP 409)."""

    def __init__(self, message: str = "Conflict."):
        super().__init__(message)


class UnprocessableEntityError(MediaManagerException):
    """Raised for validation errors (HTTP 422)."""

    def __init__(self, message: str = "Unprocessable entity."):
        super().__init__(message)


# Exception handlers
async def media_already_exists_exception_handler(
    request: Request, exc: MediaAlreadyExists
) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": exc.message})


async def not_found_error_exception_handler(
    request: Request, exc: NotFoundError
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": exc.message})


async def invalid_config_error_exception_handler(
    request: Request, exc: InvalidConfigError
) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": exc.message})


async def bad_request_error_handler(
    request: Request, exc: BadRequestError
) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": exc.message})


async def unauthorized_error_handler(
    request: Request, exc: UnauthorizedError
) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": exc.message})


async def forbidden_error_handler(
    request: Request, exc: ForbiddenError
) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": exc.message})


async def conflict_error_handler(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": exc.message})


async def unprocessable_entity_error_handler(
    request: Request, exc: UnprocessableEntityError
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": exc.message})


async def sqlalchemy_integrity_error_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={
            "detail": "The entity to create already exists or is in a conflict with others."
        },
    )
