"""Аудит: правка и отмена пишут было → стало."""

from httpx import AsyncClient

OP = {"meat_type": "FILLET", "operation_date": "2026-09-04"}


async def test_patch_writes_change(client: AsyncClient, auth_headers: dict):
    r = await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={"type": "INCOMING", **OP, "quantity": "20"},
    )
    oid = r.json()["id"]
    p = await client.patch(
        f"/api/v1/operations/{oid}", headers=auth_headers, json={"quantity": "18"}
    )
    assert p.status_code == 200
    c = await client.get(f"/api/v1/operations/{oid}/changes", headers=auth_headers)
    assert c.status_code == 200
    assert len(c.json()) == 1
    assert c.json()[0]["old_data"]["quantity"] == "20.000"


async def test_patch_cancelled_400(client: AsyncClient, auth_headers: dict):
    await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={"type": "INCOMING", **OP, "quantity": "10"},
    )
    r = await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={"type": "SPIT", **OP, "quantity": "1"},
    )
    oid = r.json()["id"]
    await client.post(f"/api/v1/operations/{oid}/cancel", headers=auth_headers)
    p = await client.patch(
        f"/api/v1/operations/{oid}", headers=auth_headers, json={"quantity": "2"}
    )
    assert p.status_code == 400


async def test_double_cancel_409(client: AsyncClient, auth_headers: dict):
    r = await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={"type": "INCOMING", **OP, "quantity": "5"},
    )
    oid = r.json()["id"]
    await client.post(f"/api/v1/operations/{oid}/cancel", headers=auth_headers)
    r2 = await client.post(f"/api/v1/operations/{oid}/cancel", headers=auth_headers)
    assert r2.status_code == 409
    assert r2.json()["code"] == "ALREADY_CANCELLED"
