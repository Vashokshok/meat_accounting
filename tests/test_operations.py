"""Операции: создание, матрица валидации, запрет минуса, история."""

from datetime import timedelta

from httpx import AsyncClient

from app.utils.dates import today

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


async def test_history_includes_creator_name(client: AsyncClient, auth_headers: dict):
    profile = await client.patch(
        "/api/v1/auth/profile",
        headers=auth_headers,
        json={"display_name": "Иван", "current_password": "meat123"},
    )
    assert profile.status_code == 200, profile.text

    created = await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={"type": "INCOMING", **OP, "quantity": "20"},
    )
    assert created.status_code == 201, created.text

    response = await client.get("/api/v1/operations", headers=auth_headers)
    assert response.status_code == 200, response.text
    assert response.json()["items"][0]["created_by_name"] == "Иван"


async def test_clear_history_day_deletes_operations_and_audit(
    client: AsyncClient, auth_headers: dict
):
    incoming = await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={"type": "INCOMING", **OP, "quantity": "20"},
    )
    operation_id = incoming.json()["id"]
    await client.patch(
        f"/api/v1/operations/{operation_id}",
        headers=auth_headers,
        json={"comment": "audit"},
    )
    await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={
            "type": "INCOMING",
            "meat_type": "SKIN",
            "operation_date": "2026-09-05",
            "quantity": "10",
        },
    )

    response = await client.delete(
        "/api/v1/operations/history?period=day&operation_date=2026-09-04",
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["deleted_count"] == 1

    history = await client.get("/api/v1/operations", headers=auth_headers)
    assert history.json()["total"] == 1
    audit = await client.get(
        f"/api/v1/operations/{operation_id}/changes",
        headers=auth_headers,
    )
    assert audit.json() == []
    stock = await client.get("/api/v1/stock", headers=auth_headers)
    assert stock.json()["fillet"] == 0
    assert stock.json()["skin"] == 10


async def test_clear_history_day_requires_date(client: AsyncClient, auth_headers: dict):
    response = await client.delete(
        "/api/v1/operations/history?period=day",
        headers=auth_headers,
    )
    assert response.status_code == 400


async def test_clear_history_last_month_deletes_previous_calendar_month(
    client: AsyncClient, auth_headers: dict
):
    this_month = today().replace(day=1)
    last_month = (this_month - timedelta(days=1)).replace(day=1)
    in_last_month = last_month.isoformat()
    in_this_month = this_month.isoformat()

    for operation_date in (in_last_month, in_this_month):
        response = await client.post(
            "/api/v1/operations",
            headers=auth_headers,
            json={
                "type": "INCOMING",
                "meat_type": "FILLET",
                "operation_date": operation_date,
                "quantity": "10",
            },
        )
        assert response.status_code == 201, response.text

    response = await client.delete(
        "/api/v1/operations/history?period=last_month",
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["deleted_count"] == 1

    history = await client.get("/api/v1/operations", headers=auth_headers)
    assert history.json()["total"] == 1
    assert history.json()["items"][0]["operation_date"] == in_this_month


async def test_clear_all_history_deletes_audit_rows(
    client: AsyncClient, auth_headers: dict
):
    created = await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={"type": "INCOMING", **OP, "quantity": "10"},
    )
    operation_id = created.json()["id"]
    await client.patch(
        f"/api/v1/operations/{operation_id}",
        headers=auth_headers,
        json={"comment": "audit"},
    )

    response = await client.delete(
        "/api/v1/operations/history?period=all",
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["deleted_count"] == 1
    history = await client.get("/api/v1/operations", headers=auth_headers)
    assert history.json()["total"] == 0
