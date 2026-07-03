from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter
import uvicorn

from api.v1.endpoints.auth import router as auth_router
from api.v1.endpoints.capsules import router as capsule_router
from core.exception_handler import exception_handler
from api.v1.endpoints.users import router as users_router
from api.v1.endpoints.verification import router as verification_router
from core.logging_config import setup_logging
from core.middleware import LoggingMiddleware
from core.scheduler import scheduler
from core.telemetry import setup_tracing
from prometheus_fastapi_instrumentator import Instrumentator


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)
setup_logging()
setup_tracing(app)
Instrumentator().instrument(app).expose(app)

router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(capsule_router)
router.include_router(users_router)
router.include_router(verification_router)
app.include_router(router)
app.add_middleware(LoggingMiddleware)
exception_handler(app=app)


def run_server(*args: str):
    uvicorn.run(
        "entrypoint:app",
        host="localhost",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    run_server()
