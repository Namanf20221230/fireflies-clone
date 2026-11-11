import asyncio

import httpx

from app.main import app



async def get(path: str) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        return await client.get(path)


def test_root() -> None:
    response = asyncio.run(get("/"))

    assert response.status_code == 200
    assert response.json() == {"message": "Fireflies clone backend"}


def test_health_check() -> None:
    response = asyncio.run(get("/health"))

    assert response.status_code == 200
    assert response.json() == {"status": "operational"}
