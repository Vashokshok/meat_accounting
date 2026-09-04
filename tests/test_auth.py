"""Auth: логин, me, чужие/битые токены."""

from httpx import AsyncClient


async def test_login_ok(client: AsyncClient, auth_headers: dict):
    assert auth_headers["Authorization"].startswith("Bearer ")


async def test_login_bad_password(client: AsyncClient, auth_headers: dict):
    r = await client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "wrong"}
    )
    assert r.status_code == 401


async def test_me_ok(client: AsyncClient, auth_headers: dict):
    r = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["username"] == "admin"


async def test_me_no_token(client: AsyncClient):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401
