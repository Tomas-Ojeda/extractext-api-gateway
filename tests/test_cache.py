import json
from contextlib import asynccontextmanager

import fakeredis.aioredis
import httpx
import pytest
from fastapi import FastAPI

from app.api.router import api_router

DOCUMENT = {
    "id": "abc",
    "filename": "ejemplo.pdf",
    "content": "texto extraido",
    "checksum": "checksum-abc",
}


@asynccontextmanager
async def _app_client(handler):
    app = FastAPI()
    app.include_router(api_router)
    app.state.http_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    app.state.redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield app, client
    finally:
        await app.state.redis.aclose()
        await app.state.http_client.aclose()


async def test_cache_miss_then_hit():
    calls = {"get": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["get"] += 1
        return httpx.Response(200, json=DOCUMENT)

    async with _app_client(handler) as (_, client):
        first = await client.get("/api/v1/documents/abc")
        second = await client.get("/api/v1/documents/abc")

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json() == DOCUMENT
    assert calls["get"] == 1


async def test_cache_hit_does_not_call_storage():
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("storage no deberia llamarse en un cache hit")

    async with _app_client(handler) as (app, client):
        await app.state.redis.set("document:abc", json.dumps(DOCUMENT))
        response = await client.get("/api/v1/documents/abc")

    assert response.status_code == 200
    assert response.json() == DOCUMENT


async def test_delete_invalidates_cache():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        return httpx.Response(204)

    async with _app_client(handler) as (app, client):
        await app.state.redis.set("document:abc", json.dumps(DOCUMENT))
        response = await client.delete("/api/v1/documents/abc")
        cached = await app.state.redis.get("document:abc")

    assert response.status_code == 204
    assert cached is None
