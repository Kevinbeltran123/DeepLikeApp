from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    meta_routes,
    monoagent_routes,
    multiagent_routes,
    pipeline_routes,
)
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="DeepLikeApp",
        description="Traductor estilo DeepL en tres modos: pipeline, mono-agente, multi-agente.",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(meta_routes.router)
    app.include_router(pipeline_routes.router)
    app.include_router(monoagent_routes.router)
    app.include_router(multiagent_routes.router)
    return app


app = create_app()
