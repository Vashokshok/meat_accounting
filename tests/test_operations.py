"""Операции: создание, матрица валидации, запрет минуса, история."""

from httpx import AsyncClient

OP = {"meat_type": "FILLET", "operation_date": "2026-09-04"}


async def test_incoming_and_stock(client: AsyncClient, auth_headers: dict):
    r = await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={"type": "INCOMING", **OP, "quantity": "20"},
    )
    assert r.status_code == 201, r.text
    s = await client.get("/api/v1/stock", headers=auth_headers)
    assert s.json()["fillet"] == 20.0


async def test_overspend_409(client: AsyncClient, auth_headers: dict):
    await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={"type": "INCOMING", **OP, "quantity": "10"},
    )
    r = await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={"type": "SPIT", **OP, "quantity": "99"},
    )
    assert r.status_code == 409
    assert r.json()["code"] == "INSUFFICIENT_STOCK"


async def test_franchise_requires_id(client: AsyncClient, auth_headers: dict):
    r = await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={"type": "FRANCHISE", **OP, "quantity": "1"},
    )
    assert r.status_code == 422


async def test_franchise_id_forbidden_for_others(
    client: AsyncClient, auth_headers: dict
):
    r = await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={"type": "SPIT", **OP, "quantity": "1", "franchise_id": 1},
    )
    assert r.status_code == 422


async def test_history_filter(client: AsyncClient, auth_headers: dict):
    for typ, qty in (("INCOMING", "10"), ("SPIT", "3")):
        await client.post(
            "/api/v1/operations",
            headers=auth_headers,
            json={"type": typ, **OP, "quantity": qty},
        )
    r = await client.get("/api/v1/operations?type=SPIT", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["type"] == "SPIT"
