from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog import get_logger

logger = get_logger("http.middleware")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger.info(
            "Request started",
            path=request.url.path,
            method=request.method,
            client_ip=request.client.host if request.client else None,
            headers=dict(request.headers),
        )
        response = await call_next(request)
        logger.info(
            "Request completed",
            path=request.url.path,
            method=request.method,
            status_code=response.status_code,
        )
        return response
