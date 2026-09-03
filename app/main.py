from fastapi import FastAPI

from app.api.activities import router as activities_router


app = FastAPI(
    title="RideReady API",
    description="API REST para planeamento de atividades ao ar livre.",
    version="0.1.0",
)

app.include_router(activities_router)


@app.get("/")
def root():
    return {
        "name": "RideReady API",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
    }