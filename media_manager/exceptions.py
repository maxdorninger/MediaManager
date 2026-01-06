from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from psycopg.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError


class MediaManagerError(Exception):
    """Base exception for MediaManager errors."""

    def __init__(self, message: str = "An error occurred.") -> None:
        super().__init__(message)
        self.message = message


class MediaAlreadyExistsError(MediaManagerError):
    """Raised when a media entity already exists (HTTP 409)."""

    def __init__(
        self, message: str = "Entity with this ID or other identifier already exists"
    ) -> None:
        super().__init__(message)


class NotFoundError(MediaManagerError):
    """Raised when an entity is not found (HTTP 404)."""

    def __init__(self, message: str = "The requested entity was not found.") -> None:
        super().__init__(message)


class InvalidConfigError(MediaManagerError):
    """Raised when the server is improperly configured (HTTP 500)."""

    def __init__(self, message: str = "The server is improperly configured.") -> None:
        super().__init__(message)


class BadRequestError(MediaManagerError):
    """Raised for invalid client requests (HTTP 400)."""

    def __init__(self, message: str = "Bad request.") -> None:
        super().__init__(message)


class UnauthorizedError(MediaManagerError):
    """Raised for authentication failures (HTTP 401)."""

    def __init__(self, message: str = "Unauthorized.") -> None:
        super().__init__(message)


class ForbiddenError(MediaManagerError):
    """Raised for forbidden actions (HTTP 403)."""

    def __init__(self, message: str = "Forbidden.") -> None:
        super().__init__(message)


class ConflictError(MediaManagerError):
    """Raised for resource conflicts (HTTP 409)."""

    def __init__(self, message: str = "Conflict.") -> None:
        super().__init__(message)


class UnprocessableEntityError(MediaManagerError):
    """Raised for validation errors (HTTP 422)."""

    def __init__(self, message: str = "Unprocessable entity.") -> None:
        super().__init__(message)


# Exception handlers
async def media_already_exists_exception_handler(
    _request: Request, exc: MediaAlreadyExistsError
) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": exc.message})


async def not_found_error_exception_handler(
    _request: Request, exc: NotFoundError
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": exc.message})


async def invalid_config_error_exception_handler(
    _request: Request, exc: InvalidConfigError
) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": exc.message})


async def bad_request_error_handler(
    _request: Request, exc: BadRequestError
) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": exc.message})


async def unauthorized_error_handler(
    _request: Request, exc: UnauthorizedError
) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": exc.message})


async def forbidden_error_handler(
    _request: Request, exc: ForbiddenError
) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": exc.message})


async def conflict_error_handler(_request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": exc.message})


async def unprocessable_entity_error_handler(
    _request: Request, exc: UnprocessableEntityError
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": exc.message})


async def sqlalchemy_integrity_error_handler(
    _request: Request, _exc: Exception
) -> JSONResponse:
    return JSONResponse(
        status_code=409,
        content={
            "detail": "The entity to create already exists or is in a conflict with others."
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(NotFoundError, not_found_error_exception_handler)
    app.add_exception_handler(
        MediaAlreadyExistsError, media_already_exists_exception_handler
    )
    app.add_exception_handler(
        InvalidConfigError, invalid_config_error_exception_handler
    )
    app.add_exception_handler(IntegrityError, sqlalchemy_integrity_error_handler)
    app.add_exception_handler(UniqueViolation, sqlalchemy_integrity_error_handler)
