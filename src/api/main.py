"""FastAPI app factory."""
from __future__ import annotations

from fastapi import FastAPI

from .dependencies import init_application_state
from .routers import auth, branding, contents, reports, security, sentiment, sources, system
from fastapi.middleware.cors import CORSMiddleware

def create_app() -> FastAPI:
    init_application_state()
    app = FastAPI(title="Sentiment Analysis API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # atau ["*"] untuk dev
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(sources.router)
    app.include_router(contents.router)
    app.include_router(sentiment.router)
    app.include_router(reports.router)
    app.include_router(branding.router)
    app.include_router(system.router)
    app.include_router(security.router)

    @app.get("/", tags=["System"])
    def root() -> dict:
        return {"message": "Sentiment Analysis API v1"}

    return app


app = create_app()
