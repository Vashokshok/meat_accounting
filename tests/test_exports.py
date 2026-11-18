from io import BytesIO

from httpx import AsyncClient
from openpyxl import load_workbook

OP = {"meat_type": "FILLET", "operation_date": "2026-09-04"}


async def test_excel_shows_user_names(client: AsyncClient, auth_headers: dict):
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
    operation_id = created.json()["id"]

    franchise = await client.post(
        "/api/v1/franchises",
        headers=auth_headers,
        json={"name": "Тестовая франшиза"},
    )
    assert franchise.status_code == 201, franchise.text
    franchise_operation = await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={
            "type": "FRANCHISE",
            **OP,
            "quantity": "5",
            "franchise_id": franchise.json()["id"],
        },
    )
    assert franchise_operation.status_code == 201, franchise_operation.text

    month_end_operation = await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={
            "type": "INCOMING",
            "meat_type": "FILLET",
            "operation_date": "2026-09-30",
            "quantity": "10",
        },
    )
    assert month_end_operation.status_code == 201, month_end_operation.text

    changed = await client.patch(
        f"/api/v1/operations/{operation_id}",
        headers=auth_headers,
        json={"comment": "Проверка автора"},
    )
    assert changed.status_code == 200, changed.text

    outside_period = await client.post(
        "/api/v1/operations",
        headers=auth_headers,
        json={
            "type": "INCOMING",
            "meat_type": "FILLET",
            "operation_date": "2026-10-01",
            "quantity": "10",
        },
    )
    assert outside_period.status_code == 201, outside_period.text
    outside_change = await client.patch(
        f"/api/v1/operations/{outside_period.json()['id']}",
        headers=auth_headers,
        json={"comment": "Не должно попасть в этот период"},
    )
    assert outside_change.status_code == 200, outside_change.text

    response = await client.get(
        "/api/v1/exports/excel?period=custom&date_from=2026-09-01&date_to=2026-09-30",
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text

    workbook = load_workbook(BytesIO(response.content), read_only=True)
    operations = workbook["Операции"]
    changes = workbook["История изменений"]
    assert operations["H2"].value == "Иван"
    assert operations["J3"].value == "Тестовая франшиза"
    assert operations["B4"].value == "2026-09-30"
    assert operations.max_row == 4
    assert changes["C2"].value == "Иван"
    assert changes.max_row == 2
    assert changes["G2"].value == "2026-09-04"


async def test_excel_exports_only_selected_day(
    client: AsyncClient, auth_headers: dict
):
    for operation_date in ("2026-09-03", "2026-09-04", "2026-09-05"):
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

    response = await client.get(
        "/api/v1/exports/excel?period=custom&date_from=2026-09-04&date_to=2026-09-04",
        headers=auth_headers,
    )
    assert response.status_code == 200, response.text

    workbook = load_workbook(BytesIO(response.content), read_only=True)
    summary = workbook["Сводка"]
    operations = workbook["Операции"]
    assert summary["B1"].value == "2026-09-04 — 2026-09-04"
    assert operations.max_row == 2
    assert operations["B2"].value == "2026-09-04"
