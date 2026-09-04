"""Гонка: остаток 10 кг, параллельно 8 и 7 кг — проходит одна."""

import asyncio

from httpx import AsyncClient

OP = {"meat_type": "FILLET", "operation_date": "2026-09-04"}


async def test_concurrent_spends_no_negative(client: AsyncClient, auth_headers: dict):
    r = await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={"type": "INCOMING", **OP, "quantity": "10"},
    )
    assert r.status_code == 201, r.text

    async def spend(qty: str) -> int:
        res = await client.post(
            "/api/v1/operations",
            headers=auth_headers,
            json={"type": "SPIT", **OP, "quantity": qty},
        )
        return res.status_code

    codes = await asyncio.gather(spend("8"), spend("7"))
    assert sorted(codes) == [201, 409]

    s = await client.get("/api/v1/stock", headers=auth_headers)
    assert s.json()["fillet"] >= 0
