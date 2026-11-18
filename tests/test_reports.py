"""Отчёты: остаток на начало + движение = остаток на конец."""

import calendar

from httpx import AsyncClient

from app.utils.dates import today


async def test_report_opening_closing(client: AsyncClient, auth_headers: dict):
    ops = [
        {
            "type": "INCOMING",
            "meat_type": "FILLET",
            "quantity": "30",
            "operation_date": "2026-09-03",
        },
        {
            "type": "SPIT",
            "meat_type": "FILLET",
            "quantity": "5",
            "operation_date": "2026-09-04",
        },
    ]
    for b in ops:
        r = await client.post("/api/v1/operations", headers=auth_headers, json=b)
        assert r.status_code == 201, r.text
    r = await client.get(
        "/api/v1/reports?period=custom&date_from=2026-09-04&date_to=2026-09-04",
        headers=auth_headers,
    )
    assert r.status_code == 200
    fillet = next(i for i in r.json()["items"] if i["meat_type"] == "FILLET")
    assert fillet["opening"] == 30.0
    assert fillet["spit"] == 5.0
    assert fillet["closing"] == 25.0


async def test_report_defaults_to_full_calendar_month(
    client: AsyncClient, auth_headers: dict
):
    response = await client.get("/api/v1/reports", headers=auth_headers)
    assert response.status_code == 200, response.text

    current_day = today()
    month_start = current_day.replace(day=1)
    month_end = current_day.replace(
        day=calendar.monthrange(current_day.year, current_day.month)[1]
    )
    assert response.json()["date_from"] == month_start.isoformat()
    assert response.json()["date_to"] == month_end.isoformat()
