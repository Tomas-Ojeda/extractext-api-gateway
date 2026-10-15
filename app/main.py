from contextlib import asynccontextmanager

from fastapi import FastAPI
import httpx

from app.api.router import api_router
from config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida del cliente HTTP compartido."""
    app.state.http_client = httpx.AsyncClient()
    yield
    await app.state.http_client.aclose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.app_debug,
        lifespan=lifespan,
    )
    app.include_router(api_router)
    return app


app = create_app()