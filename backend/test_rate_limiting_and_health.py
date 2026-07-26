"""
Pytest integration tests verifying slowapi rate limiting and /health endpoint response code.
"""

from httpx import ASGITransport, AsyncClient
import pytest
from main import app


@pytest.mark.asyncio
async def test_health_check_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["db_connection"] == "connected"


@pytest.mark.asyncio
async def test_auth_login_rate_limiting():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        login_data = {"email": "test@example.com", "password": "wrongpassword"}
        responses = []
        for _ in range(7):
            res = await ac.post("/auth/login", json=login_data)
            responses.append(res.status_code)

        # Expect 429 Too Many Requests after exceeding 5 requests per minute
        assert 429 in responses
