from fastapi import FastAPI, APIRouter
import uvicorn

app = FastAPI()
router = APIRouter(prefix="/api/v1")
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
