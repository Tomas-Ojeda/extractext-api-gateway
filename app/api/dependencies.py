import httpx
from fastapi import Request

from config.settings import settings


def get_http_client(request: Request) -> httpx.AsyncClient:
    """Devuelve el cliente HTTP compartido del ciclo de vida (factor IX)."""
    return request.app.state.http_client