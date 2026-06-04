from fastapi import FastAPI, APIRouter
import uvicorn
from api.v1.endpoints.auth import router as auth_router

app = FastAPI()
router = APIRouter(prefix="/api/v1")
router.include_router(auth_router)
app.include_router(router)


def run_server(*args: str):
    uvicorn.run(
        "entrypoint:app",
        host="localhost",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    run_server()
