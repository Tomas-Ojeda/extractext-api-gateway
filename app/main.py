from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.router import api_router
from config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación."""
    # Startup: aquí podríamos inicializar conexiones, etc.
    yield
    # Shutdown: limpieza de recursos


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
