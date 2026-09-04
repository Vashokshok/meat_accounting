"""Остатки: филе/кожа отдельно, отмена возвращает склад."""

from httpx import AsyncClient

OP = {"operation_date": "2026-09-04"}


async def test_stock_separate_meats(client: AsyncClient, auth_headers: dict):
    await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={"type": "INCOMING", "meat_type": "FILLET", "quantity": "20", **OP},
    )
    await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={"type": "INCOMING", "meat_type": "SKIN", "quantity": "7", **OP},
    )
    s = await client.get("/api/v1/stock", headers=auth_headers)
    assert s.json() == {"fillet": 20.0, "skin": 7.0}


async def test_cancel_expense_restores(client: AsyncClient, auth_headers: dict):
    await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={"type": "INCOMING", "meat_type": "FILLET", "quantity": "20", **OP},
    )
    r = await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={"type": "SPIT", "meat_type": "FILLET", "quantity": "5", **OP},
    )
    sid = r.json()["id"]
    await client.post(f"/api/v1/operations/{sid}/cancel", headers=auth_headers)
    s = await client.get("/api/v1/stock", headers=auth_headers)
    assert s.json()["fillet"] == 20.0


async def test_cancel_incoming_below_stock_409(client: AsyncClient, auth_headers: dict):
    r1 = await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={"type": "INCOMING", "meat_type": "FILLET", "quantity": "10", **OP},
    )
    await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={"type": "SPIT", "meat_type": "FILLET", "quantity": "9", **OP},
    )
    r = await client.post(
        f"/api/v1/operations/{r1.json()['id']}/cancel", headers=auth_headers
    )
    assert r.status_code == 409
