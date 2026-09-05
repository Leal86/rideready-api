from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.activities import router as activities_router
from app.api.locations import router as locations_router

app = FastAPI(
    title="RideReady API",
    description="API REST para planeamento de atividades ao ar livre.",
    version="0.1.0",
)

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(activities_router)
app.include_router(locations_router)


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