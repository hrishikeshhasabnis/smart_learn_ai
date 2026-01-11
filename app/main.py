from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.router import router as v1_router

def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="Agentic Learning Itinerary API", version="1.0.0")

    @app.get("/")
    def root():
        return {
            "name": "Agentic Learning Itinerary API",
            "health": "/v1/health",
            "docs": "/docs",
            "itinerary": "POST /v1/itinerary",
        }

    origins = ["*"] if settings.allowed_origins.strip() == "*" else [
        o.strip() for o in settings.allowed_origins.split(",") if o.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(v1_router)
    return app

app = create_app()
