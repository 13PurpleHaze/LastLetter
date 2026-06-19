from fastapi import FastAPI, APIRouter
import uvicorn
from api.v1.endpoints.auth import router as auth_router
from api.v1.endpoints.capsules import router as capsule_router
from core.exception_handler import exception_handler

app = FastAPI()
router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
router.include_router(capsule_router)
app.include_router(router)
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
