from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from typing import Type
from sqlalchemy.exc import DatabaseError

from api.v1.schemas.failed_response import FailedResponseSchema, FailedDetailSchema
from modules.auth.exceptions import (
    AppException,
    UnauthorizedError,
    InvalidCredentialsError,
)
from modules.capsules.exceptions import (
    PermissionDeniedError,
    CapsuleNotFoundError,
    ContentNotFoundError,
)
from modules.user.exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
    EmailNotVerifiedError,
    UserInactiveError,
    EmailAlreadyVerifiedError,
)

ERROR_MAPPING: dict[Type[AppException], dict] = {
    UserAlreadyExistsError: {
        "status_code": status.HTTP_409_CONFLICT,
        "code": "user_already_exists",
    },
    UserNotFoundError: {
        "status_code": status.HTTP_404_NOT_FOUND,
        "code": "user_not_found",
    },
    EmailNotVerifiedError: {
        "status_code": status.HTTP_403_FORBIDDEN,
        "code": "email_not_verified",
    },
    UserInactiveError: {
        "status_code": status.HTTP_403_FORBIDDEN,
        "code": "user_inactive",
    },
    UnauthorizedError: {
        "status_code": status.HTTP_401_UNAUTHORIZED,
        "code": "unauthorized",
    },
    EmailAlreadyVerifiedError: {
        "status_code": status.HTTP_409_CONFLICT,
        "code": "email_already_verified",
    },
    InvalidCredentialsError: {
        "status_code": status.HTTP_401_UNAUTHORIZED,
        "code": "invalid_credentials",
    },
    PermissionDeniedError: {
        "status_code": status.HTTP_403_FORBIDDEN,
        "code": "permission_denied",
    },
    CapsuleNotFoundError: {
        "status_code": status.HTTP_404_NOT_FOUND,
        "code": "not_found",
    },
    ContentNotFoundError: {
        "status_code": status.HTTP_404_NOT_FOUND,
        "code": "not_found",
    },
}


def exception_handler(app: FastAPI):
    @app.exception_handler(AppException)
    def app_errors_handler(
        request: Request,
        exc: AppException,
    ):
        error = ERROR_MAPPING.get(type(exc))
        if error:
            return JSONResponse(
                status_code=error["status_code"],
                content=FailedResponseSchema(
                    success=False,
                    error=FailedDetailSchema(code=error["code"], message=str(exc)),
                ).model_dump(),
            )
        raise exc

    @app.exception_handler(RequestValidationError)
    def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=FailedResponseSchema(
                success=False,
                error=FailedDetailSchema(
                    code="validation_error", message=exc.errors()[0]["msg"]
                ),
            ).model_dump(),
        )

    @app.exception_handler(DatabaseError)
    def database_error_handler(
        request: Request,
        exc: DatabaseError,
    ):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=FailedResponseSchema(
                success=False,
                error=FailedDetailSchema(
                    code="database_error",
                    message=exc.code,
                ),
            ).model_dump(),
        )
